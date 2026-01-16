#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example usage of Temi_Control_Def class
Demonstrates patrol control functionality
"""
from temi_control import Temi_Control_Def
import time
import argparse
import os
import socket


def find_waypoints_file(specified_path=None):
    """
    自动查找waypoints.txt文件
    
    查找策略：
    1. 如果用户指定了路径，直接使用
    2. 否则使用默认路径 (config/waypoints.txt)
    3. 如果默认路径不存在，在pytemi目录下递归搜索waypoints.txt
    4. 如果都找不到，返回None
    
    Args:
        specified_path: 用户指定的waypoints文件路径
        
    Returns:
        str: 找到的文件路径，失败返回None
    """
    # 策略1: 用户指定路径
    if specified_path:
        if os.path.isfile(specified_path):
            print(f"[INFO] 使用指定的waypoints文件: {specified_path}")
            return specified_path
        else:
            print(f"[WARNING] 指定的文件不存在: {specified_path}")
    
    # 策略2: 默认路径 (相对于项目根目录)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))  # pytemi根目录
    default_path = os.path.join(project_root, "config", "waypoints.txt")
    
    if os.path.isfile(default_path):
        print(f"[INFO] 使用默认waypoints文件: {default_path}")
        return default_path
    
    # 策略3: 在pytemi目录下递归搜索
    print(f"[INFO] 在项目目录下搜索waypoints.txt...")
    pytemi_root = project_root
    
    for root, dirs, files in os.walk(pytemi_root):
        if "waypoints.txt" in files:
            found_path = os.path.join(root, "waypoints.txt")
            print(f"[INFO] 找到waypoints文件: {found_path}")
            return found_path
    
    # 策略4: 都找不到
    print(f"[ERROR] 无法找到waypoints.txt文件")
    print(f"[ERROR] 请使用 --waypoints 参数指定文件路径")
    return None


def get_local_ip_in_subnet(subnet="192.168.8"):
    """
    自动获取指定网段下的本机IP地址
    
    Args:
        subnet: 网段前缀，默认"192.168.8"
        
    Returns:
        str: 找到的IP地址，失败返回None
    """
    try:
        # 获取本机所有网络接口的IP地址
        hostname = socket.gethostname()
        addrs = socket.getaddrinfo(hostname, None)
        
        # 筛选符合指定网段的IPv4地址
        matching_ips = []
        for addr in addrs:
            ip = addr[4][0]
            # 只处理IPv4地址
            if ':' not in ip and ip.startswith(subnet + '.'):
                matching_ips.append(ip)
        
        # 去重
        matching_ips = list(set(matching_ips))
        
        if len(matching_ips) == 1:
            print(f"[INFO] 自动检测到{subnet}.x网段IP: {matching_ips[0]}")
            return matching_ips[0]
        elif len(matching_ips) > 1:
            print(f"[WARNING] 检测到多个{subnet}.x网段IP: {matching_ips}")
            print(f"[INFO] 使用第一个IP: {matching_ips[0]}")
            return matching_ips[0]
        else:
            print(f"[ERROR] 未检测到{subnet}.x网段的IP地址")
            return None
            
    except Exception as e:
        print(f"[ERROR] 获取本机IP失败: {e}")
        return None


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='Temi机器人巡航控制脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 使用默认配置运行示例2（从文件巡航）
  python example_patrol.py
  
  # 指定waypoints文件路径
  python example_patrol.py --waypoints /path/to/waypoints.txt
  
  # 指定MQTT服务器IP
  python example_patrol.py --ip 192.168.8.100
  
  # 同时指定多个参数
  python example_patrol.py --waypoints config/waypoints.txt --ip 192.168.8.132 --example 3
        ''')
    
    parser.add_argument(
        '--waypoints',
        type=str,
        default=None,
        help='waypoints.txt文件路径（可选，未指定则自动查找）'
    )
    
    parser.add_argument(
        '--ip',
        type=str,
        default=None,
        help='MQTT服务器IP地址（可选，未指定则自动检测192.168.8网段IP）'
    )
    
    parser.add_argument(
        '--example',
        type=int,
        choices=[1, 2, 3, 4],
        default=None,
        help='直接运行指定示例（1-4），跳过交互选择'
    )
    
    return parser.parse_args()


def example_single_navigation(broker_ip):
    """Example: Navigate to a single waypoint"""
    print("\n" + "="*60)
    print("Example 1: Single Waypoint Navigation")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host=broker_ip,
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("[ERROR] Failed to connect")
        return
    
    try:
        # Wait for ready
        if controller.wait_until_ready(timeout=10):
            # Navigate to waypoint
            controller.goto_waypoint("a6a")
            
            # Monitor navigation
            for i in range(20):
                time.sleep(1)
                status = controller.get_status()
                print(f"Status: {status['robot_status']} | Goto: {status['goto_status']}")
                
                if status['goto_status'] == 'complete':
                    print("[INFO] Navigation complete!")
                    break
    
    finally:
        controller.disconnect()


def example_patrol_from_file(broker_ip, waypoints_path):
    """Example: Execute patrol from waypoint file"""
    print("\n" + "="*60)
    print("Example 2: Patrol from File (带自动拍照)")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host=broker_ip,
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("[WRROR] Failed to connect")
        return
    
    try:
        # Load waypoints from file
        waypoints = controller.load_waypoints_from_file(waypoints_path)
        
        if not waypoints:
            print("[ERROR] No waypoints loaded")
            return
        
        print(f"\nLoaded waypoints: {waypoints}")
        print(f"[INFO] 照片将保存到: {controller.photo_dir} 文件夹\n")
        
        # Wait for ready
        if controller.wait_until_ready(timeout=10):
            # Execute patrol with retry mechanism and auto photo capture
            # - timeout: 60s per attempt (increased for photo capture)
            # - check_interval: 3s
            # - max_retries: 1 (total 2 attempts per waypoint)
            # - Photos automatically captured 1s after arriving at each waypoint
            success = controller.execute_patrol(
                wait_time=60, 
                check_interval=3,
                max_retries=1
            )
            
            if success:
                print("[INFO] Patrol completed successfully!")
                print(f"[INFO] 请查看 {controller.photo_dir} 文件夹中的照片")
            else:
                print("[INFO]  Patrol completed with some waypoints skipped")
    
    finally:
        controller.disconnect()


def example_custom_patrol(broker_ip):
    """Example: Custom patrol with manual waypoint list"""
    print("\n" + "="*60)
    print("Example 3: Custom Patrol")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host=broker_ip,
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("[INFO] Failed to connect")
        return
    
    try:
        # Set custom waypoints
        controller.patrol_waypoints = ["a13", "a12", "a2", "home base"]
        
        print(f"\nCustom waypoints: {controller.patrol_waypoints}\n")
        
        # Wait for ready
        if controller.wait_until_ready(timeout=10):
            # Execute patrol with retry mechanism
            controller.execute_patrol(
                wait_time=60,
                check_interval=1,
                max_retries=1
            )
    
    finally:
        controller.disconnect()


def example_status_monitoring(broker_ip):
    """Example: Continuous status monitoring"""
    print("\n" + "="*60)
    print("Example 4: Status Monitoring")
    print("="*60 + "\n")
    
    # Create controller
    controller = Temi_Control_Def(
        broker_host=broker_ip,
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect
    if not controller.connect():
        print("[ERROR] Failed to connect")
        return
    
    try:
        print("[INFO] Monitoring robot status (Press Ctrl+C to exit)...")
        
        while True:
            controller.print_status()
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    
    finally:
        controller.disconnect()


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 自动配置MQTT服务器IP
    if args.ip:
        broker_ip = args.ip
        print(f"[INFO] 使用指定的MQTT服务器IP: {broker_ip}")
    else:
        broker_ip = get_local_ip_in_subnet("192.168.8")
        if not broker_ip:
            print("[ERROR] 无法自动检测MQTT服务器IP，请使用 --ip 参数指定")
            exit(1)
    
    # 自动查找waypoints文件
    waypoints_path = find_waypoints_file(args.waypoints)
    if not waypoints_path:
        print("[ERROR] 无法找到waypoints文件，程序终止")
        exit(1)
    
    # 如果指定了示例编号，直接运行
    if args.example:
        choice = str(args.example)
    else:
        # 交互式选择示例
        print("\n" + "="*60)
        print("Temi Control Examples")
        print("="*60)
        print("1. Single Waypoint Navigation")
        print("2. Patrol from File (带自动拍照)")
        print("3. Custom Patrol (带自动拍照)")
        print("4. Status Monitoring")
        print("="*60)
        print(f"\n当前配置:")
        print(f"  MQTT服务器: {broker_ip}")
        print(f"  Waypoints文件: {waypoints_path}")
        print("="*60)
        
        choice = input("\nSelect example (1-4): ").strip()
    
    # 运行选定的示例
    if choice == "1":
        example_single_navigation(broker_ip)
    elif choice == "2":
        example_patrol_from_file(broker_ip, waypoints_path)
    elif choice == "3":
        example_custom_patrol(broker_ip)
    elif choice == "4":
        example_status_monitoring(broker_ip)
    else:
        print("Invalid choice")
