#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试相机拍照功能
验证巡逻过程中的自动拍照功能
"""
from temi_control import Temi_Control_Def
import time

def capture_current_position():
    """功能1：在当前点位直接拍照"""
    print("="*60)
    print("当前点位拍照")
    print("="*60)
    
    # 创建控制器
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # 连接
    if not controller.connect():
        print("❌ 连接失败")
        return
    
    try:
        print("\n等待机器人就绪...")
        if not controller.wait_until_ready(timeout=10):
            print("❌ 机器人未就绪")
            return
        
        # 获取当前位置
        current_pos = controller.current_position if controller.current_position else "unknown"
        print(f"\n当前位置: {current_pos}")
        print("📷 正在拍照...\n")
        
        # 直接调用拍照方法
        photo_path = controller._capture_photo(current_pos)
        
        if photo_path:
            print(f"✅ 拍照成功！照片已保存: {photo_path}")
        else:
            print("❌ 拍照失败")
            
    except Exception as e:
        print(f"\n❌ 拍照出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        controller.disconnect()

def test_camera_patrol():
    """功能2：测试带拍照功能的巡逻"""
    print("="*60)
    print("巡逻拍照功能测试")
    print("="*60)
    print("\n功能说明：")
    print("  1. 巡逻到达每个航点后自动拍照")
    print("  2. 照片保存在photos文件夹")
    print("  3. 文件名格式：航点名_时间戳.png")
    print("="*60 + "\n")
    
    # 创建控制器
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        temi_serial="00121506569",
        silent=False
    )
    
    # 连接
    if not controller.connect():
        print("❌ 连接失败")
        return
    
    try:
        # 设置测试航点（较少航点用于快速测试）
        controller.patrol_waypoints = ["a12", "a13"]
        
        print(f"\n测试航点: {controller.patrol_waypoints}")
        print(f"照片保存目录: {controller.photo_dir}\n")
        
        # 等待机器人就绪
        if not controller.wait_until_ready(timeout=10):
            print("❌ 机器人未就绪")
            return
        
        # 执行带拍照的巡逻
        print("\n🚀 开始巡逻测试（每个航点将自动拍照）...\n")
        
        success = controller.execute_patrol(
            wait_time=60,      # 60秒超时
            check_interval=3,  # 每3秒检查一次
            max_retries=1      # 失败后重试1次
        )
        
        # 结果
        print("\n" + "="*60)
        if success:
            print("✅ 巡逻测试完成！")
        else:
            print("⚠️  巡逻测试完成，部分航点可能跳过")
        print(f"📁 请查看 {controller.photo_dir} 文件夹中的照片")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔌 断开连接...")
        controller.disconnect()

def main():
    """主菜单"""
    print("\n" + "="*60)
    print("Temi 机器人拍照功能测试")
    print("="*60)
    print("\n请选择功能：")
    print("  1 - 在当前点位直接拍照")
    print("  2 - 巡逻并在每个航点拍照")
    print("="*60)
    
    choice = input("\n请输入选项 (1 或 2): ").strip()
    
    if choice == "1":
        capture_current_position()
    elif choice == "2":
        test_camera_patrol()
    else:
        print("❌ 无效选项，请输入 1 或 2")

if __name__ == "__main__":
    main()
