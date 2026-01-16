#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Temi 机器人交互式控制台"""
import pytemi as temi
import time
import sys


def print_menu():
    """显示菜单"""
    print("\n" + "=" * 60)
    print("Temi 机器人控制菜单")
    print("=" * 60)
    print("1. 语音播报 (TTS)")
    print("2. 头部倾斜")
    print("3. 旋转机身")
    print("4. 导航到位置")
    print("5. 停止移动")
    print("6. 跟随模式")
    print("7. 查看电池电量")
    print("8. 查看已保存位置")
    print("0. 退出")
    print("=" * 60)


def main():
    # 配置参数
    MQTT_HOST = "192.168.8.132"
    MQTT_PORT = 1883
    TEMI_SERIAL = '00121506569'
    
    print("\n" + "=" * 60)
    print("Temi 机器人交互式控制台")
    print("=" * 60)
    
    # 连接到 MQTT broker
    print("\n正在连接到 MQTT broker...")
    mqtt_client = temi.connect(MQTT_HOST, MQTT_PORT)
    
    # 创建机器人对象
    print("正在创建机器人对象...")
    robot = temi.Robot(mqtt_client, TEMI_SERIAL, silent=False)
    
    # 等待连接建立
    print("等待连接建立...")
    time.sleep(3)
    
    print("\n✅ 连接成功!机器人序列号: {}".format(TEMI_SERIAL))
    
    # 主循环
    while True:
        print_menu()
        choice = input("\n请选择操作 (0-8): ").strip()
        
        if choice == '0':
            print("\n退出程序...")
            break
            
        elif choice == '1':
            text = input("请输入要播报的内容: ").strip()
            if text:
                print("发送命令: 语音播报 '{}'".format(text))
                robot.tts(text)
                time.sleep(2)
            
        elif choice == '2':
            angle = input("请输入倾斜角度 (-25 到 55): ").strip()
            try:
                angle = int(angle)
                print("发送命令: 头部倾斜到 {} 度".format(angle))
                robot.tilt(angle)
                time.sleep(2)
            except ValueError:
                print("❌ 输入无效,请输入数字")
        
        elif choice == '3':
            angle = input("请输入旋转角度 (-360 到 360): ").strip()
            try:
                angle = int(angle)
                print("发送命令: 旋转 {} 度".format(angle))
                robot.rotate(angle)
                time.sleep(abs(angle) / 30 + 1)  # 根据角度估算等待时间
            except ValueError:
                print("❌ 输入无效,请输入数字")
        
        elif choice == '4':
            location = input("请输入位置名称: ").strip()
            if location:
                print("发送命令: 导航到 '{}'".format(location))
                robot.goto(location)
                print("机器人正在移动中...")
                time.sleep(3)
            
        elif choice == '5':
            print("发送命令: 停止移动")
            robot.stop()
            time.sleep(1)
        
        elif choice == '6':
            print("发送命令: 开启跟随模式")
            robot.follow()
            time.sleep(1)
        
        elif choice == '7':
            battery = robot.battery
            if battery is not None:
                print("🔋 当前电池电量: {}%".format(battery))
            else:
                print("⚠️ 电池信息尚未就绪,请稍后再试")
                print("提示: 机器人需要几秒钟来同步状态数据")
            time.sleep(1)
        
        elif choice == '8':
            locations = robot.locations
            if locations:
                print("\n📍 已保存的位置点:")
                for i, loc in enumerate(locations, 1):
                    print("  {}. {}".format(i, loc))
            else:
                print("⚠️ 没有已保存的位置点")
            time.sleep(1)
        
        else:
            print("❌ 无效选择,请重试")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] 程序被用户中断")
    except Exception as e:
        print("\n❌ 发生错误: {}".format(str(e)))
        import traceback
        traceback.print_exc()
