# Temi 机器人本地 MQTT 配置指南

## ✅ 问题已解决

**问题原因**: test.mosquitto.org 公共服务器可能因为网络策略、防火墙或连接限制拒绝了连接。

**解决方案**: 使用本地 MQTT broker (Mosquitto)。

---

## 当前状态

### ✅ 已完成
1. **Mosquitto MQTT Broker** - 已安装并运行在本地
   - 版本: 2.0.22
   - 端口: 1883
   - 配置文件: `mosquitto.conf`
   
2. **Python 脚本** - 已更新连接到本地 broker
   - 连接状态: ✅ 成功
   - MQTT Host: `localhost`
   - MQTT Port: `1883`

3. **测试脚本** - 已创建并验证
   - `test_local_mqtt.py` - 本地连接测试
   - 所有 MQTT 命令发布成功

---

## 下一步: 连接 Temi 机器人

要让 Temi 机器人接收命令，需要在机器人上配置 MQTT 客户端：

### 方法 1: 使用 temi-mqtt-client 应用

1. **在 Temi 机器人上安装应用**
   - 从 GitHub 下载: https://github.com/hapi-robo/temi-mqtt-client
   - 或从应用商店安装（如果可用）

2. **获取本机 IP 地址**
   ```powershell
   # 在 Windows 上运行
   ipconfig
   # 查找 IPv4 地址，例如: 192.168.1.100
   ```

3. **在 Temi 上配置 MQTT 连接**
   - MQTT Host: `你的电脑 IP` (例如: 192.168.1.100)
   - MQTT Port: `1883`
   - Client ID: `00121506569` (Temi 序列号)
   - 用户名/密码: 留空（已允许匿名连接）

### 方法 2: 临时测试 - 使用 MQTT 订阅查看消息

在另一个终端监听 MQTT 消息：

```powershell
# 订阅所有 temi 相关主题
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t "temi/#" -v
```

然后运行 Python 脚本，你会看到发布的所有命令。

---

## 运行示例脚本

### 启动 Mosquitto (如果未运行)

在一个终端中:
```powershell
& "C:\Program Files\mosquitto\mosquitto.exe" -c "d:\0-YorkGUO\HKPC Project\Temi\pytemi\mosquitto.conf" -v
```

### 运行测试脚本

在另一个终端中:
```powershell
& C:/Users/17399/AppData/Local/Programs/Python/Python38/python.exe "d:/0-YorkGUO/HKPC Project/Temi/pytemi/test_local_mqtt.py"
```

或运行完整示例:
```powershell
& C:/Users/17399/AppData/Local/Programs/Python/Python38/python.exe "d:/0-YorkGUO/HKPC Project/Temi/pytemi/sample.py"
```

---

## MQTT 主题结构

Temi 使用以下 MQTT 主题：

### 发布 (Python → Temi)
```
temi/00121506569/command/tts                 # 语音播报
temi/00121506569/command/waypoint/goto       # 导航到位置
temi/00121506569/command/move/tilt           # 头部倾斜
temi/00121506569/command/move/tilt_by        # 相对倾斜
temi/00121506569/command/move/turn_by        # 旋转
temi/00121506569/command/move/joystick       # 摇杆控制
temi/00121506569/command/media/video         # 播放视频
temi/00121506569/command/media/webview       # 显示网页
```

### 订阅 (Temi → Python)
```
temi/00121506569/status/info                 # 机器人状态
temi/00121506569/status/utils/battery        # 电池状态
temi/00121506569/event/waypoint/goto         # 导航事件
temi/00121506569/event/user/detection        # 用户检测
```

---

## 故障排除

### 检查 Mosquitto 是否运行
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*mosquitto*"}
```

### 测试 MQTT 连接
```powershell
# 发布测试消息
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -p 1883 -t "test/hello" -m "Hello"

# 订阅测试消息
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t "test/#"
```

### 检查防火墙
确保 Windows 防火墙允许端口 1883 的入站连接。

---

## 文件列表

- `mosquitto.conf` - Mosquitto 配置文件
- `sample.py` - 主示例脚本（已更新为本地连接）
- `test_local_mqtt.py` - 本地 MQTT 测试脚本
- `setup_local_mqtt.md` - 本地 MQTT 设置指南

---

## 总结

✅ **本地 MQTT broker 已成功部署并运行**  
✅ **Python 脚本可以成功连接并发布命令**  
⏳ **下一步: 在 Temi 机器人上配置 MQTT 客户端连接到此 broker**

现在你的开发环境完全不依赖外部服务，更稳定可靠！
