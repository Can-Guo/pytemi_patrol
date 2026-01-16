#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单的 Temi 控制测试脚本"""
import pytemi as temi
import time


def main():
    # 配置参数
    MQTT_HOST = "192.168.8.132"
    MQTT_PORT = 1883
    TEMI_SERIAL = '00121506569'
    
    print("=" * 60)
    print("Temi 机器人控制测试")
    print("=" * 60)
    
    # 连接到 MQTT broker
    print("\n[步骤 1] 连接到 MQTT broker...")
    mqtt_client = temi.connect(MQTT_HOST, MQTT_PORT)
    
    # 创建机器人对象
    print("[步骤 2] 创建机器人对象 (序列号: {})...".format(TEMI_SERIAL))
    robot = temi.Robot(mqtt_client, TEMI_SERIAL, silent=False)
    
    # 等待连接建立
    print("[步骤 3] 等待连接建立...")
    time.sleep(3)
    
    print("\n" + "=" * 60)
    print("开始执行控制命令")
    print("=" * 60 + "\n")
    
    # 测试 1: 语音播报
    print("\n[测试 1] 语音播报")
    robot.tts("你好,我是 Temi 机器人")
    time.sleep(3)
    
    # 测试 2: 头部倾斜
    print("\n[测试 2] 头部倾斜测试")
    robot.tts("我现在要抬头")
    time.sleep(2)
    robot.tilt(30)
    time.sleep(3)
    
    robot.tts("我现在要低头")
    time.sleep(2)
    robot.tilt(-10)
    time.sleep(3)
    
    robot.tts("恢复正常角度")
    time.sleep(2)
    robot.tilt(0)
    time.sleep(2)
    
    # 测试 3: 旋转
    print("\n[测试 3] 旋转测试")
    robot.tts("我要向右转 90 度")
    time.sleep(2)
    robot.rotate(90)
    time.sleep(5)
    
    robot.tts("我要向左转 90 度")
    time.sleep(2)
    robot.rotate(-90)
    time.sleep(5)
    
    # 测试 4: 导航(如果有保存的位置点)
    # 注释掉,因为不确定是否有 "a6a" 这个位置点
    # print("\n[测试 4] 导航测试")
    # robot.tts("我要去 a6a 位置")
    # time.sleep(2)
    # robot.goto("a6a")
    # time.sleep(10)
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
    
    # 保持连接
    print("\n按 Ctrl+C 退出...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] 程序退出")


if __name__ == "__main__":
    main()
