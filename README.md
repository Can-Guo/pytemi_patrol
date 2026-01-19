# Temi机器人巡查系统 - 快速启动指南

A repo to create, execute or arrange periodic patrol tasks for Temi robot based on [pytemi](https://github.com/hapi-robo/pytemi) & [temi_mqtt_client](https://github.com/hapi-robo/temi-mqtt-client/).

> **运行环境**: Jetson NX (192.168.8.132) 或者 PC远程SSH进入MCB进行操作

> **更新日期**: 2026年1月14日

####  设备IP清单：
##### 1. Temi Robot: 192.168.8.130
##### 2. MCB: 192.168.8.132
##### 3. Your PC: 192.168.8.xxx (Depends on your PC's ip)

####  步骤清单：
##### 1. Temi机器人连网
启动Temi机器人,Temi连接至Cruzr_PSTS(wifi)，默认ip: 192.168.8.130，保持机器人正常连网状态。
##### 2. 扫图、加点
重新扫图，备份地图，登录Temi Center [url](https://center.robotemi.com/)，添加所有需巡检的点位，点击某些点位让机器人前往，查看Temi是否正常定位和导航，如果未知定位，请重新定位，并在机器人行走时，查看temi center是否持续更新机器人的定位和状态。
##### 3. 启动照片监控脚本
启动照片监控脚本（可先启动，以随时监控照片并上传至ai服务器分析结果，保持运行）。或远程SSH登录MCB，执行照片监控脚本，
##### 4. 启动巡检脚本
启动巡检脚本（指定路径巡检）或远程SSH登录MCB，执行巡检脚本。

---

### Related Repository: [pytemi](https://github.com/hapi-robo/pytemi)
 & [temi_mqtt_client](https://github.com/hapi-robo/temi-mqtt-client/)


### 系统概述

本系统由两个独立脚本和temi_mqtt_client安卓应用组成，实现Temi机器人自动巡查与照片分析：

1. **`example_patrol.py`** - 控制Temi机器人按路径点巡查并拍照
2. **`monitor_photos_v2.py`** - 监控新照片并自动发送API分析
3. **`temi_mqtt_client.apk`** - 将Temi机器人的MQTT消息，包括导航状态等转发至mqtt服务器（MCB），接受MCB的点位指令执行点到点的导航任务。

---

## Temi Robot的WiFi配置和MQTT配置（2步完成）
1. **WiFi配置**: 确保Temi机器人已连接至WiFi，并已配置好WiFi名称和密码(默认会自动连接)。**`Cruzr_PSTS, password: 03442944`**，确保有正常互联网连接。
2. **MQTT配置**: 确保Temi机器人已连接至MQTT服务器，并已配置好MQTT服务器的ip，如果异常请重新启动temi_mqtt_client应用，输入MCB的ip **`192.168.8.132`**，点击connect。提示:successfully connected或already connected，如提示Failed to connect，则检查mqtt服务器的状态和ip是否正确。


### MCB的快速启动（3步完成）

#### **步骤1: 配置巡查路径点**

编辑 `waypoints.txt` 文件，每行一个路径点名称，按顺序填写，格式如下：

```text
# Temi巡查路径配置，注释会自动忽略
# 每行一个路径点名称（逗号可选）
# 建议最后一点添加home base，以满足充电需求

a1
a2
a3
a4
home base
```

**重要说明**:
- 路径点名称必须与Temi机器人地图中已保存的位置**完全一致**
- 支持空格（如 `home base`）
- 以 `#` 开头的行会被注释，会被忽略
- 空行自动跳过

---

#### **步骤2: 启动照片监控脚本**

步骤3: 启动照片监控脚本**

**打开新的终端窗口**，执行：

```bash
cd ~/Desktop/pytemi
python3 monitor_photos_v2.py
```

**脚本会自动**:
- 👁️ 监控 `./pytemi/photos/` 文件夹
- 🆕 检测20秒内创建的新照片
- 📤 自动发送到API分析（地址: https://645t2cmhz085.share.zrok.io/analyze）
- 💾 保存分析结果到 `analysis_results.csv`

**输出示例**:
```
sunny@ubuntu:~/Desktop/pytemi$ python3 monitor_photos_v2.py
[2026-01-14 15:45:13] ======================================================================
[2026-01-14 15:45:13] 📷 照片监控与自动分析系统
[2026-01-14 15:45:13] ======================================================================
[2026-01-14 15:45:13] 📁 监控目录: /home/sunny/Desktop/pytemi/photos
[2026-01-14 15:45:13] 🌐 API地址: https://645t2cmhz085.share.zrok.io/analyze
[2026-01-14 15:45:13] 📊 结果文件: /home/sunny/Desktop/pytemi/analysis_results.csv
[2026-01-14 15:45:13] ⏱️  时间阈值: 20秒
[2026-01-14 15:45:13] 🔄 检查间隔: 2秒
[2026-01-14 15:45:13] ======================================================================
[2026-01-14 15:45:13] 📂 目录中现有 41 张图片
[2026-01-14 15:45:13]    示例: ['a13_20260108_100128.png', 'a22_20260114_145113.png', 'a2_20260107_151657.png']
[2026-01-14 15:45:13] 🚀 工作线程已启动
[2026-01-14 15:45:13] ✅ 监控系统已启动
[2026-01-14 15:45:13] 💡 按 Ctrl+C 停止监控

[2026-01-14 15:45:55] 🆕 检测到新图片: a13_20260114_154554.png
[2026-01-14 15:45:55]    └─ 文件年龄: 1.0秒
[2026-01-14 15:45:55]    └─ 当前队列任务数: 0
[2026-01-14 15:45:55] 🔄 开始处理: a13_20260114_154554.png
[2026-01-14 15:45:55] 📤 发送API请求: a13_20260114_154554.png
[2026-01-14 15:46:12] ✅ API响应成功: a13_20260114_154554.png
[2026-01-14 15:46:12]    └─ 结果: The image depicts an overhead view of a ceiling composed of square, light-colored acoustic tiles. Pr...
[2026-01-14 15:46:12]    └─ JSON字段: ['image_filename', 'prompt_query', 'analyzed_result', 'water_leakage']
[2026-01-14 15:46:12] 💾 结果已保存: a13_20260114_154554.png
[2026-01-14 15:46:12] ✅ 处理完成: a13_20260114_154554.png


```

---

##### 查看分析结果

分析结果保存在 `analysis_results.csv`，包含以下字段：

| 字段 | 说明 |
|------|------|
| `image_filename` | 照片文件名 |
| `prompt_query` | 分析提示词 |
| `analyzed_result` | AI分析结果（文字描述） |
| `water_leakage` | 漏水检测结果 |
| `处理时间` | 分析完成时间 |

使用Excel或LibreOffice打开查看，或者下载至自己的电脑用Excel导入csv数据查看实际的分析结果文本和漏水情况分析。

---

#### **步骤3: 启动巡查脚本**

打开终端，执行以下命令：

```bash
cd ~/Desktop/pytemi
python3 example_patrol.py
```

然后输入选项 **`2`**, 键入Enter（从文件加载路径进行巡查）

**脚本会自动**:
- ✅ 连接Temi机器人 (MQTT Broker: 192.168.8.130)
- ✅ 读取 `waypoints.txt` 中的路径点
- ✅ 依次导航到每个路径点
- ✅ 到达后自动拍照（保存到 `./pytemi/photos/` 文件夹）
- ✅ 显示实时巡查进度和状态

**输出示例**:
```
sunny@ubuntu:~/Desktop/pytemi$ python3 example_patrol.py

Temi Control Examples
============================================================
1. Single Waypoint Navigation
2. Patrol from File (带自动拍照)
3. Custom Patrol (带自动拍照)
4. Status Monitoring
============================================================

Select example (1-4): 3

============================================================
Example 3: Custom Patrol
============================================================

[15:45:33] 📷 摄像头已就绪
[15:45:33] 🔌 Connecting to MQTT broker...
[15:45:33] ✅ Connected to MQTT Broker at 192.168.8.132:1883
[15:45:33] 📡 Subscribed to robot topics
[15:45:33] 📋 Message callbacks registered
[15:45:33] ⏳ Waiting for initial status...

Custom waypoints: ['a13', 'a12', 'a2', 'home base']

[15:45:36] ⏳ Waiting for robot to be ready...
[15:45:36] ✅ Robot is ready
[15:45:36] 🚀 Starting patrol: 4 waypoints
[15:45:36]    Configuration: timeout=60s, max_retries=1
[15:45:36]
[1/4] Navigating to: a13
[15:45:36] 🎯 Command sent: goto 'a13'
[15:45:37] 🗺️  Navigation: a13 - start
[15:45:38] 🗺️  Navigation:  - calculating
[15:45:39] 🗺️  Navigation: a13 - going
[15:45:53] 🗺️  Navigation: a13 - complete
[15:45:53] 📍 Position confirmed: a13
[15:45:53] ✅ Reached waypoint: a13
[15:45:53]    └─ Position verified: current_waypoint_a13
[15:45:54] 📷 照片已保存: ./photos/a13_20260114_154554.png
[15:45:55]
```

---


### 高级配置

#### 修改巡查超时时间

编辑 [example_patrol.py](example_patrol.py#L75)：

```python
success = controller.execute_patrol(
    wait_time=60,        # 每个路径点等待时间（秒）
    check_interval=3,    # 状态检查间隔（秒）
    max_retries=1        # 失败重试次数
)
```

#### 修改照片监控参数

编辑 [monitor_photos_v2.py](monitor_photos_v2.py#L18-L21)：

```python
TIME_THRESHOLD = 20   # 只处理20秒内创建的新照片
CHECK_INTERVAL = 2    # 每2秒检查一次文件夹
PROMPT = "Please describe the image."  # API分析提示词
```

#### 修改MQTT连接参数

编辑 [example_patrol.py](example_patrol.py#L51)：

```python
controller = Temi_Control_Def(
    broker_host="192.168.8.132",  # MQTT Broker IP
    temi_serial="00121506569"     # Temi机器人序列号
)
```

---

### ❓常见问题

#### Q1: 提示路径点不存在怎么办？
**A**: 确保 `waypoints.txt` 中的名称与Temi地图中**完全一致**（包括大小写和空格）

#### Q2: 照片监控没有响应？
**A**: 检查以下项：
- `./pytemi/photos/` 文件夹是否存在
- 照片是否在20秒内创建（超过20秒不会被处理）
- API地址是否可访问

#### Q3: 如何停止脚本？
**A**: 在终端按 `Ctrl+C` 安全停止

#### Q4: 巡查过程中某个路径点失败了？
**A**: 脚本会自动重试1次（默认），失败后跳过继续下一个路径点

---

#### 📞如有任何疑惑，请联络York GUO 或 查看详细日志输出。

**项目目录**: `~/Desktop/pytemi`  
**核心文件**:
- `example_patrol.py` - 巡查控制
- `monitor_photos_v2.py` - 照片监控
- `temi_control.py` - 底层控制库
- `waypoints.txt` - 路径点配置

