#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
相机控制器测试脚本
通过WebSocket客户端测试camera_controller.py的各项功能
"""
import asyncio
import websockets
import json
import sys
from datetime import datetime


class CameraControllerTester:
    """相机控制器测试类"""
    
    def __init__(self, host: str = "192.168.8.132", port: int = 8765):
        """
        初始化测试器
        
        Args:
            host: WebSocket服务器地址
            port: WebSocket服务器端口
        """
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
    
    def _log(self, message: str):
        """输出带时间戳的日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    async def send_command(self, websocket, command: dict) -> dict:
        """
        发送命令并接收响应
        
        Args:
            websocket: WebSocket连接对象
            command: 命令字典
            
        Returns:
            dict: 服务器响应
        """
        try:
            # 发送命令
            command_str = json.dumps(command)
            self._log(f"📤 发送命令: {command_str}")
            await websocket.send(command_str)
            
            # 接收响应
            response_str = await websocket.recv()
            response = json.loads(response_str)
            self._log(f"📥 收到响应: {json.dumps(response, ensure_ascii=False, indent=2)}")
            
            return response
            
        except Exception as e:
            self._log(f"❌ 发送命令错误: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_status(self, websocket):
        """测试状态查询"""
        self._log("\n" + "="*70)
        self._log("🧪 测试1: 查询相机状态")
        self._log("="*70)
        
        command = {"command": "status"}
        response = await self.send_command(websocket, command)
        
        if "initialized" in response:
            self._log(f"✅ 状态查询成功")
            self._log(f"   ├─ 相机已初始化: {response.get('initialized')}")
            self._log(f"   ├─ 正在录制: {response.get('recording')}")
            self._log(f"   └─ 相机索引: {response.get('camera_index')}")
        else:
            self._log(f"❌ 状态查询失败")
        
        await asyncio.sleep(1)
    
    async def test_capture(self, websocket, filename: str = None):
        """测试拍照功能"""
        self._log("\n" + "="*70)
        self._log("🧪 测试2: 拍照功能")
        self._log("="*70)
        
        command = {"command": "capture"}
        if filename:
            command["filename"] = filename
            self._log(f"📝 指定文件名: {filename}")
        
        response = await self.send_command(websocket, command)
        
        if response.get("success"):
            self._log(f"✅ 拍照成功")
            self._log(f"   ├─ 文件名: {response.get('filename')}")
            self._log(f"   ├─ 路径: {response.get('filepath')}")
            self._log(f"   ├─ 分辨率: {response.get('width')}x{response.get('height')}")
            self._log(f"   └─ 大小: {response.get('size_bytes', 0)/1024:.2f} KB")
        else:
            self._log(f"❌ 拍照失败: {response.get('error')}")
        
        await asyncio.sleep(1)
    
    async def test_record(self, websocket, duration: int = 5, 
                         width: int = 1280, height: int = 720, 
                         fps: int = 30, filename: str = None,
                         format: str = 'avi'):
        """测试视频录制功能"""
        self._log("\n" + "="*70)
        self._log("🧪 测试3: 视频录制功能")
        self._log("="*70)
        
        command = {
            "command": "record",
            "duration": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "format": format
        }
        if filename:
            command["filename"] = filename
            self._log(f"📝 指定文件名: {filename}")
        
        self._log(f"⏱️  录制时长: {duration}秒")
        self._log(f"📐 分辨率: {width}x{height}")
        self._log(f"🎬 帧率: {fps} FPS")
        self._log(f"📼 格式: {format.upper()}")
        
        response = await self.send_command(websocket, command)
        
        if response.get("success"):
            self._log(f"✅ 录制已开始")
            self._log(f"   ├─ 文件名: {response.get('filename')}")
            self._log(f"   ├─ 路径: {response.get('filepath')}")
            self._log(f"   └─ 时长: {response.get('duration')}秒")
            
            # 等待录制完成
            self._log(f"⏳ 等待录制完成...")
            await asyncio.sleep(duration + 2)  # 额外等待2秒
            self._log(f"✅ 录制应该已完成")
        else:
            self._log(f"❌ 录制失败: {response.get('error')}")
        
        await asyncio.sleep(1)
    
    async def test_invalid_command(self, websocket):
        """测试无效命令"""
        self._log("\n" + "="*70)
        self._log("🧪 测试4: 无效命令处理")
        self._log("="*70)
        
        command = {"command": "invalid_command"}
        response = await self.send_command(websocket, command)
        
        if not response.get("success"):
            self._log(f"✅ 正确处理无效命令: {response.get('error')}")
        else:
            self._log(f"❌ 未能正确处理无效命令")
        
        await asyncio.sleep(1)
    
    async def test_multiple_captures(self, websocket, count: int = 3):
        """测试连续拍照"""
        self._log("\n" + "="*70)
        self._log(f"🧪 测试5: 连续拍照 ({count}张)")
        self._log("="*70)
        
        for i in range(count):
            self._log(f"\n📸 拍照 {i+1}/{count}")
            filename = f"test_photo_{i+1}.jpg"
            command = {"command": "capture", "filename": filename}
            response = await self.send_command(websocket, command)
            
            if response.get("success"):
                self._log(f"   ✅ 第{i+1}张拍照成功: {response.get('filename')}")
            else:
                self._log(f"   ❌ 第{i+1}张拍照失败: {response.get('error')}")
            
            await asyncio.sleep(0.5)  # 短暂延迟
    
    async def test_video_formats(self, websocket):
        """测试不同视频格式"""
        self._log("\n" + "="*70)
        self._log("🧪 测试6: 不同视频格式")
        self._log("="*70)
        
        formats = ['mp4', 'avi', 'mov']
        
        for fmt in formats:
            self._log(f"\n📼 测试格式: {fmt.upper()}")
            filename = f"test_video_{fmt}.{fmt}"
            command = {
                "command": "record",
                "duration": 3,  # 短时间录制
                "width": 640,
                "height": 480,
                "fps": 20,
                "format": fmt,
                "filename": filename
            }
            response = await self.send_command(websocket, command)
            
            if response.get("success"):
                self._log(f"   ✅ {fmt.upper()}格式录制开始成功: {response.get('filename')}")
                # 等待录制完成
                await asyncio.sleep(4)
            else:
                self._log(f"   ❌ {fmt.upper()}格式录制失败: {response.get('error')}")
            
            await asyncio.sleep(0.5)
    
    async def run_all_tests(self):
        """运行所有测试"""
        self._log("="*70)
        self._log("🚀 相机控制器自动化测试")
        self._log("="*70)
        self._log(f"📡 连接到: {self.uri}")
        self._log("="*70)
        
        try:
            # 连接到WebSocket服务器
            self._log("\n🔗 正在连接到相机控制器...")
            async with websockets.connect(self.uri) as websocket:
                self._log("✅ 连接成功\n")
                
                # 运行各项测试
                await self.test_status(websocket)
                await self.test_capture(websocket)
                await self.test_capture(websocket, "custom_name.jpg")
                await self.test_record(websocket, duration=5, width=1280, height=720, format='mp4')
                await self.test_invalid_command(websocket)
                await self.test_multiple_captures(websocket, count=3)
                await self.test_video_formats(websocket)
                
                # 最后再次查询状态
                await self.test_status(websocket)
                
                self._log("\n" + "="*70)
                self._log("✅ 所有测试完成")
                self._log("="*70)
                
        except websockets.exceptions.ConnectionRefusedError:
            self._log(f"❌ 连接失败: 无法连接到 {self.uri}")
            self._log("💡 请确保相机控制器已启动: python camera_controller.py")
        except Exception as e:
            self._log(f"❌ 测试错误: {e}")
    
    async def interactive_mode(self):
        """交互式测试模式"""
        self._log("="*70)
        self._log("🎮 相机控制器交互式测试")
        self._log("="*70)
        self._log(f"📡 连接到: {self.uri}")
        self._log("="*70)
        
        try:
            # 配置 WebSocket 客户端参数
            async with websockets.connect(
                self.uri,
                ping_interval=20,  # 启用自动 ping，每20秒一次
                ping_timeout=10,   # ping 超时10秒
                close_timeout=10   # 关闭超时10秒
            ) as websocket:
                self._log("✅ 连接成功")
                self._log("💓 心跳已启用 (WebSocket 自动 ping/pong)\n")
                
                while True:
                    print("\n" + "="*70)
                    print("可用命令:")
                    print("  1 - 查询状态")
                    print("  2 - 拍照（自动命名）")
                    print("  3 - 拍照（自定义命名）")
                    print("  4 - 录制视频（5秒，1280x720，MP4）")
                    print("  5 - 录制视频（自定义参数）")
                    print("  6 - 连续拍照3张")
                    print("  7 - 测试所有视频格式（MP4/AVI/MOV）")
                    print("  0 - 退出")
                    print("="*70)
                    
                    choice = input("请选择命令 [0-7]: ").strip()
                    
                    if choice == "0":
                        self._log("👋 退出交互式测试")
                        break
                    elif choice == "1":
                        await self.test_status(websocket)
                    elif choice == "2":
                        await self.test_capture(websocket)
                    elif choice == "3":
                        filename = input("输入文件名（例如：my_photo.jpg）: ").strip()
                        await self.test_capture(websocket, filename if filename else None)
                    elif choice == "4":
                        await self.test_record(websocket, duration=5, format='mp4')
                    elif choice == "5":
                        try:
                            duration = int(input("录制时长（秒）[10]: ").strip() or "10")
                            width = int(input("宽度 [1920]: ").strip() or "1920")
                            height = int(input("高度 [1080]: ").strip() or "1080")
                            fps = int(input("帧率 [30]: ").strip() or "30")
                            format_input = input("格式 (mp4/avi/mov/[mp4]: ").strip().lower() or "mp4"
                            filename = input("文件名（可选）: ").strip()
                            await self.test_record(
                                websocket, 
                                duration=duration,
                                width=width,
                                height=height,
                                fps=fps,
                                filename=filename if filename else None,
                                format=format_input
                            )
                        except ValueError:
                            self._log("❌ 输入参数无效")
                    elif choice == "6":
                        await self.test_multiple_captures(websocket, count=3)
                    elif choice == "7":
                        await self.test_video_formats(websocket)
                    else:
                        print("❌ 无效选择")
                
        except websockets.exceptions.ConnectionRefusedError:
            self._log(f"❌ 连接失败: 无法连接到 {self.uri}")
            self._log("💡 请确保相机控制器已启动: python camera_controller.py")
        except KeyboardInterrupt:
            self._log("\n👋 退出交互式测试")
        except Exception as e:
            self._log(f"❌ 错误: {e}")


async def main():
    """主函数"""
    # 解析命令行参数
    host = "192.168.8.132"
    port = 8765
    mode = "auto"  # auto 或 interactive
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "-i" or sys.argv[1] == "--interactive":
            mode = "interactive"
        elif sys.argv[1] == "-h" or sys.argv[1] == "--help":
            print("="*70)
            print("相机控制器测试脚本")
            print("="*70)
            print("用法:")
            print("  python test_camera_controller.py           # 自动测试模式")
            print("  python test_camera_controller.py -i        # 交互式测试模式")
            print("  python test_camera_controller.py --help    # 显示帮助")
            print("\n环境变量:")
            print("  CAMERA_HOST - WebSocket服务器地址 (默认: localhost)")
            print("  CAMERA_PORT - WebSocket服务器端口 (默认: 8765)")
            print("="*70)
            return
    
    # 创建测试器
    tester = CameraControllerTester(host=host, port=port)
    
    # 运行测试
    if mode == "interactive":
        await tester.interactive_mode()
    else:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
