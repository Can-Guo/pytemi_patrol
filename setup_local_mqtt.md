# 本地 MQTT Broker 设置指南

## 方案一：使用 Mosquitto (推荐)

### 1. 下载并安装 Mosquitto

访问官方网站下载 Windows 版本：
https://mosquitto.org/download/

或使用 Chocolatey 安装：
```powershell
choco install mosquitto
```

### 2. 启动 Mosquitto

安装后，在 PowerShell 中运行：
```powershell
# 默认配置启动（允许匿名连接）
mosquitto -v
```

或者创建配置文件 `mosquitto.conf`:
```
listener 1883
allow_anonymous true
```

然后使用配置文件启动：
```powershell
mosquitto -c mosquitto.conf -v
```

### 3. 测试连接

在另一个终端测试订阅：
```powershell
mosquitto_sub -h localhost -p 1883 -t "test/#" -v
```

在第三个终端测试发布：
```powershell
mosquitto_pub -h localhost -p 1883 -t "test/hello" -m "Hello MQTT"
```

## 方案二：使用 Docker 运行 Mosquitto

如果你已安装 Docker：

```powershell
# 运行 Mosquitto 容器（允许匿名连接）
docker run -it -p 1883:1883 eclipse-mosquitto:latest mosquitto -c /mosquitto-no-auth.conf
```

## 方案三：使用 EMQX (功能更强大)

### 使用 Docker 运行 EMQX：
```powershell
docker run -d --name emqx -p 1883:1883 -p 8083:8083 -p 8084:8084 -p 8883:8883 -p 18083:18083 emqx/emqx:latest
```

Web 管理界面: http://localhost:18083
- 默认用户名: admin
- 默认密码: public

## 修改代码以使用本地 Broker

修改 `sample.py` 中的连接参数：
```python
MQTT_HOST = "localhost"  # 或 "127.0.0.1"
MQTT_PORT = 1883
```

## 验证连接

运行测试脚本验证连接是否成功。
