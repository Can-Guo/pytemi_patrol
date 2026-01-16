#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单示例：读取 Temi 机器人状态
"""
from temi_reader import TemiStatusReader
import time

# 配置参数
BROKER_HOST = "192.168.8.132"  # MQTT Broker 地址
TEMI_SERIAL = "00121506569"    # 机器人序列号

# 创建读取器
reader = TemiStatusReader(BROKER_HOST, temi_serial=TEMI_SERIAL)

# 方式 1: 持续读取 (推荐)
print("方式 1: 持续读取模式")
reader.start_reading(continuous=True)

# 方式 2: 定时读取 (读取 30 秒后停止)
# print("方式 2: 定时读取模式")
# reader.start_reading(duration=30, continuous=False)

# 方式 3: 自定义处理
# reader.client = mqtt.Client(...)
# reader.client.on_connect = reader.on_connect
# reader.client.on_message = reader.on_message
# reader.client.connect(BROKER_HOST, 1883, 60)
# reader.client.loop_start()
# 
# # 等待数据
# time.sleep(10)
# 
# # 获取最新状态
# status = reader.get_latest_status()
# print("电池:", reader.get_battery_percentage(), "%")
# print("位置点:", reader.get_waypoint_list())
