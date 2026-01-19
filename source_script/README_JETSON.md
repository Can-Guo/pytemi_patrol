# Jetson NX 平台部署指南

## 兼容性修正说明

脚本已针对 Jetson NX (Ubuntu 20.04) 平台进行了兼容性优化。

## 主要改进

### 1. CSI 相机支持
- 自动检测 Jetson 平台
- 支持通过 GStreamer 访问 CSI 相机（如 IMX219、IMX477）
- 可通过命令行参数强制使用 CSI 模式

### 2. 硬件编码器优化
- Jetson 平台优先使用 H.264 硬件编码器
- 视频格式建议：MP4 (H.264)、AVI (MJPEG)

### 3. 依赖安装

#### 必需包

```bash
# 更新系统
sudo apt-get update

# 安装 Python 依赖
pip3 install opencv-python
pip3 install websockets

# 如果使用 CSI 相机，确保 GStreamer 插件已安装
sudo apt-get install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev

# 验证 GStreamer 插件
gst-inspect-1.0 nvarguscamerasrc
```

## 使用方法

### 启动服务器

#### USB 相机模式
```bash
python3 camera_controller.py
```

#### CSI 相机模式
```bash
python3 camera_controller.py --csi
# 或
python3 camera_controller.py -c
```

### 运行测试
```bash
# 自动测试
python3 test_camera_controller.py

# 交互式测试
python3 test_camera_controller.py -i
```

## 常见问题

### 1. CSI 相机无法打开

**问题**：`相机打开失败`

**解决方案**：
```bash
# 检查相机是否被识别
ls /dev/video*

# 测试 GStreamer 管道
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! \
  'video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1' ! \
  nvvidconv ! 'video/x-raw, format=BGRx' ! \
  videoconvert ! 'video/x-raw, format=BGR' ! \
  fakesink

# 检查权限
sudo usermod -a -G video $USER
# 注销后重新登录
```

### 2. 视频编码失败

**问题**：`VideoWriter初始化失败`

**解决方案**：
- 对于 Jetson，建议使用 MP4 + H.264 或 AVI + MJPEG
- 确保 OpenCV 编译时包含 GStreamer 支持

```bash
# 检查 OpenCV 构建信息
python3 -c "import cv2; print(cv2.getBuildInformation())"
# 查找 GStreamer: YES
```

### 3. 权限问题

**问题**：无法访问相机或网络端口

**解决方案**：
```bash
# 相机权限
sudo chmod 666 /dev/video*

# 网络端口 (如果端口 < 1024)
sudo setcap 'cap_net_bind_service=+ep' $(which python3)
```

## 性能优化

### 1. 使用硬件加速

CSI 相机模式自动使用 NVIDIA 硬件加速管道：
- `nvarguscamerasrc`：ARGUS 相机源
- `nvvidconv`：硬件视频转换
- H.264 硬件编码

### 2. 降低分辨率

如果性能不足，可以降低分辨率：

```python
controller = CameraController(
    camera_index=0,
    use_csi=True,
    csi_width=1280,   # 降低到 720p
    csi_height=720,
    csi_fps=30
)
```

### 3. 监控系统资源

```bash
# 实时监控 Jetson 状态
sudo tegrastats

# 查看 GPU 使用率
nvidia-smi
```

## 推荐配置

### Jetson NX 推荐设置

```python
# camera_controller.py 主函数修改
controller = CameraController(
    camera_index=0,
    host="0.0.0.0",
    port=8765,
    use_csi=True,        # 使用 CSI 相机
    csi_width=1920,      # 1080p
    csi_height=1080,
    csi_fps=30
)
```

### 网络设置

在局域网环境中：
- 确保防火墙允许端口 8765
- 检查 IP 地址：`ifconfig` 或 `ip addr`

```bash
# 允许端口
sudo ufw allow 8765/tcp
```

## 测试相机

### 快速测试脚本

```python
import cv2

# 测试 CSI 相机
gst_str = (
    "nvarguscamerasrc sensor-id=0 ! "
    "video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12, framerate=30/1 ! "
    "nvvidconv ! video/x-raw, format=BGRx ! "
    "videoconvert ! video/x-raw, format=BGR ! appsink"
)

cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print("✅ CSI 相机工作正常")
        print(f"分辨率: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("❌ 无法读取帧")
else:
    print("❌ 无法打开相机")

cap.release()
```

## 视频格式对比

| 格式 | Jetson 支持 | 推荐编码器 | 文件大小 | 质量 |
|------|-------------|-----------|---------|------|
| MP4  | ✅ 优秀     | H.264 (硬件) | 小      | 高   |
| AVI  | ✅ 良好     | MJPEG     | 大      | 高   |
| MOV  | ⚠️ 一般     | H.264     | 中      | 高   |
| MKV  | ⚠️ 一般     | H.264     | 中      | 高   |

**建议**：在 Jetson 上优先使用 **MP4 + H.264** 格式。

## 故障排除命令

```bash
# 1. 检查相机设备
v4l2-ctl --list-devices

# 2. 测试 GStreamer
gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink

# 3. 检查 OpenCV 版本
python3 -c "import cv2; print(cv2.__version__)"

# 4. 检查网络连接
netstat -tuln | grep 8765

# 5. 查看系统日志
dmesg | grep -i camera
journalctl -xe
```

## 联系支持

如遇到问题，请提供：
1. Jetson 型号和 JetPack 版本
2. 相机型号
3. 错误日志输出
4. OpenCV 构建信息
