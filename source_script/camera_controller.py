#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
相机控制类 - WebSocket服务器
支持远程拍照和视频录制功能
"""
import os
import cv2
import asyncio
import websockets
import json
import threading
import time
import socket
import ipaddress
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class CameraController:
    """
    相机控制类
    提供相机初始化、拍照、录制视频等功能
    通过WebSocket接收远程控制指令
    """
    
    def __init__(self, camera_index: int = 0, host: str = "0.0.0.0", port: int = 8765, 
                 use_csi: bool = False, csi_width: int = 1920, csi_height: int = 1080, csi_fps: int = 30):
        """
        初始化相机控制器
        
        Args:
            camera_index: 相机设备索引，默认为0（系统默认相机）
            host: WebSocket服务器监听地址
            port: WebSocket服务器监听端口
            use_csi: 是否使用CSI相机（Jetson平台）
            csi_width: CSI相机宽度
            csi_height: CSI相机高度
            csi_fps: CSI相机帧率
        """
        self.camera_index = camera_index
        self.host = host
        self.port = port
        self.camera: Optional[cv2.VideoCapture] = None
        self.is_initialized = False
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.video_writer: Optional[cv2.VideoWriter] = None
        
        # 平台检测
        self.is_jetson = self._detect_jetson_platform()
        # 明确判断：只有当use_csi显式为True时才使用CSI，否则使用USB
        if use_csi is True:
            self.use_csi = True
        elif use_csi is False:
            self.use_csi = False
        else:
            # use_csi为None时，不自动启用CSI（即使在Jetson上）
            self.use_csi = False
        self.csi_width = csi_width
        self.csi_height = csi_height
        self.csi_fps = csi_fps
        
        # 网络安全配置
        self.allowed_networks = self._get_local_networks()
        self.block_localhost = False  # 是否拒绝本机连接
        
        # 设置保存路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.photo_dir = os.path.join(self.script_dir, "cam_photos")
        self.video_dir = os.path.join(self.script_dir, "cam_videos")
        
        # 创建保存目录
        os.makedirs(self.photo_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        
        self._log(f"📷 相机控制器已创建")
        self._log(f"   ├─ 照片目录: {self.photo_dir}")
        self._log(f"   └─ 视频目录: {self.video_dir}")
    
    def _log(self, message: str):
        """输出带时间戳的日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def _detect_jetson_platform(self) -> bool:
        """
        检测是否运行在Jetson平台
        
        Returns:
            bool: 如果是Jetson平台返回True
        """
        try:
            # 检查是否存在Jetson特有的文件
            if os.path.exists('/etc/nv_tegra_release'):
                with open('/etc/nv_tegra_release', 'r') as f:
                    content = f.read()
                    self._log(f"🤖 检测到Jetson平台: {content.strip()}")
                    return True
            
            # 检查设备树模型
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read()
                    if 'jetson' in model.lower():
                        self._log(f"🤖 检测到Jetson设备: {model.strip()}")
                        return True
        except Exception as e:
            pass
        
        return False
    
    def _get_csi_gstreamer_pipeline(self, sensor_id: int = 0, 
                                     width: int = 1920, height: int = 1080, 
                                     fps: int = 30, flip_method: int = 0) -> str:
        """
        构建CSI相机的GStreamer管道字符串
        
        Args:
            sensor_id: 相机传感器ID
            width: 图像宽度
            height: 图像高度
            fps: 帧率
            flip_method: 翻转方法 (0-7)
            
        Returns:
            str: GStreamer管道字符串
        """
        return (
            f"nvarguscamerasrc sensor-id={sensor_id} ! "
            f"video/x-raw(memory:NVMM), width=(int){width}, height=(int){height}, "
            f"format=(string)NV12, framerate=(fraction){fps}/1 ! "
            f"nvvidconv flip-method={flip_method} ! "
            f"video/x-raw, width=(int){width}, height=(int){height}, format=(string)BGRx ! "
            f"videoconvert ! "
            f"video/x-raw, format=(string)BGR ! "
            f"appsink"
        )
    
    def _get_local_networks(self) -> list:
        """
        获取本机所在的局域网网段
        
        Returns:
            list: 包含本机所有网络接口的网段列表
        """
        networks = []
        
        try:
            # 方法1: 尝试使用 socket.getaddrinfo
            hostname = socket.gethostname()
            addresses = socket.getaddrinfo(hostname, None)
            
            for addr_info in addresses:
                ip_str = addr_info[4][0]
                
                # 只处理IPv4地址
                if ':' not in ip_str:
                    try:
                        ip = ipaddress.IPv4Address(ip_str)
                        
                        # 跳过回环地址
                        if ip.is_loopback:
                            continue
                        
                        # 根据私有地址类别确定网段
                        if ip.is_private:
                            # 使用/24作为默认子网掩码
                            network = ipaddress.IPv4Network(f"{ip_str}/24", strict=False)
                            if network not in networks:
                                networks.append(network)
                                self._log(f"   ├─ 检测到局域网网段: {network}")
                    except ValueError:
                        continue
            
            # 方法2: 如果方法1未获取到网段，尝试读取 /proc/net/fib_trie (Linux)
            if len(networks) == 0 and platform.system() == "Linux":
                self._log("   ├─ 使用备用方法检测网络接口...")
                try:
                    import subprocess
                    # 使用 ip addr 命令获取所有网络接口
                    result = subprocess.run(['ip', 'addr', 'show'], 
                                          capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            # 查找 inet 行，格式如: inet 192.168.8.129/24 brd 192.168.8.255 scope global dynamic noprefixroute eth1
                            if 'inet ' in line and 'scope global' in line:
                                parts = line.strip().split()
                                if len(parts) >= 2:
                                    # 获取 IP/掩码，如 192.168.8.129/24
                                    ip_with_mask = parts[1]
                                    try:
                                        # 创建网络对象
                                        interface = ipaddress.IPv4Interface(ip_with_mask)
                                        ip = interface.ip
                                        
                                        # 跳过回环地址
                                        if ip.is_loopback:
                                            continue
                                        
                                        # 获取网络地址
                                        network = interface.network
                                        if network not in networks:
                                            networks.append(network)
                                            self._log(f"   ├─ 检测到局域网网段: {network}")
                                    except ValueError:
                                        continue
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                    self._log(f"   ├─ 备用方法失败: {e}")
        
        except Exception as e:
            self._log(f"⚠️  获取本地网络信息失败: {e}")
        
        return networks
    
    def _is_ip_allowed(self, client_ip: str) -> tuple:
        """
        检查客户端IP是否允许连接
        
        Args:
            client_ip: 客户端IP地址字符串
            
        Returns:
            tuple: (是否允许, 原因说明)
        """
        try:
            ip = ipaddress.IPv4Address(client_ip)
            
            # 检查是否为本机连接（回环地址）
            if ip.is_loopback:
                if self.block_localhost:
                    return False, "拒绝本机连接"
                else:
                    return True, "允许本机连接"
            
            # 检查是否在允许的网段内
            for network in self.allowed_networks:
                if ip in network:
                    return True, f"允许网段 {network}"
            
            # 不在任何允许的网段内
            return False, "不在允许的局域网网段内"
            
        except ValueError:
            return False, "无效的IP地址格式"
        except Exception as e:
            return False, f"验证错误: {e}"
    
    def initialize_camera(self) -> bool:
        """
        初始化相机设备
        
        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        try:
            if self.is_initialized:
                self._log("⚠️  相机已经初始化")
                return True
            
            if self.use_csi:
                # 使用CSI相机 (Jetson平台)
                self._log(f"🔧 正在初始化CSI相机 (传感器ID: {self.camera_index})...")
                gst_pipeline = self._get_csi_gstreamer_pipeline(
                    sensor_id=self.camera_index,
                    width=self.csi_width,
                    height=self.csi_height,
                    fps=self.csi_fps
                )
                self._log(f"   └─ GStreamer管道: {gst_pipeline[:80]}...")
                self.camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            else:
                # 使用USB相机或默认相机
                self._log(f"🔧 正在初始化相机 (索引: {self.camera_index})...")
                self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                self._log("❌ 相机打开失败")
                if self.use_csi:
                    self._log("💡 提示: 请确保CSI相机已正确连接并且GStreamer插件已安装")
                self.camera = None
                return False
            
            # 设置相机参数（仅对USB相机有效）
            if not self.use_csi:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # 获取实际参数
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.camera.get(cv2.CAP_PROP_FPS))
            
            self.is_initialized = True
            self._log(f"✅ 相机初始化成功")
            self._log(f"   ├─ 分辨率: {width}x{height}")
            self._log(f"   └─ 帧率: {fps} FPS")
            
            return True
            
        except Exception as e:
            self._log(f"❌ 相机初始化错误: {e}")
            self.camera = None
            return False
    
    def warmup_camera(self, frames: int = 30) -> bool:
        """
        预热相机，读取若干帧以稳定图像质量
        
        Args:
            frames: 预热帧数，默认30帧
            
        Returns:
            bool: 预热成功返回True，失败返回False
        """
        if not self.is_initialized or self.camera is None:
            self._log("❌ 相机未初始化，无法预热")
            return False
        
        try:
            self._log(f"🔥 相机预热中 (读取 {frames} 帧)...")
            
            for i in range(frames):
                ret, _ = self.camera.read()
                if not ret:
                    self._log(f"⚠️  预热失败: 第 {i+1} 帧读取失败")
                    return False
                
                if (i + 1) % 10 == 0:
                    self._log(f"   └─ 进度: {i+1}/{frames}")
            
            self._log("✅ 相机预热完成")
            return True
            
        except Exception as e:
            self._log(f"❌ 相机预热错误: {e}")
            return False
    
    def deinitialize_camera(self):
        """释放相机资源"""
        if self.is_recording:
            self._log("⚠️  正在录制中，停止录制...")
            self._stop_recording()
        
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            self.is_initialized = False
            self._log("✅ 相机已释放")
        else:
            self._log("⚠️  相机未初始化，无需释放")
    
    def capture_photo(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        拍摄照片并保存
        
        Args:
            filename: 指定文件名（可选），不指定则自动生成时间戳文件名
            
        Returns:
            dict: 包含状态和文件路径的字典
        """
        if not self.is_initialized or self.camera is None:
            return {"success": False, "error": "相机未初始化"}
        
        try:
            # 读取一帧
            ret, frame = self.camera.read()
            
            if not ret or frame is None:
                return {"success": False, "error": "读取帧失败"}
            
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"photo_{timestamp}.jpg"
            
            # 确保文件名有扩展名
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filename += '.jpg'
            
            # 完整路径
            filepath = os.path.join(self.photo_dir, filename)
            
            # 保存照片
            success = cv2.imwrite(filepath, frame)
            
            if success:
                file_size = os.path.getsize(filepath)
                self._log(f"📸 照片已保存: {filename}")
                self._log(f"   ├─ 路径: {filepath}")
                self._log(f"   ├─ 分辨率: {frame.shape[1]}x{frame.shape[0]}")
                self._log(f"   └─ 大小: {file_size/1024:.2f} KB")
                
                return {
                    "success": True,
                    "filename": filename,
                    "filepath": filepath,
                    "width": frame.shape[1],
                    "height": frame.shape[0],
                    "size_bytes": file_size
                }
            else:
                return {"success": False, "error": "保存照片失败"}
                
        except Exception as e:
            self._log(f"❌ 拍照错误: {e}")
            return {"success": False, "error": str(e)}
    
    def start_recording(self, duration: int = 10, width: int = 1920, 
                       height: int = 1080, fps: int = 30, 
                       filename: Optional[str] = None, 
                       format: str = 'mp4') -> Dict[str, Any]:
        """
        开始录制视频
        
        Args:
            duration: 录制时长（秒）
            width: 视频宽度
            height: 视频高度
            fps: 视频帧率
            filename: 指定文件名（可选）
            format: 视频格式，支持 'mp4', 'avi', 'mov', 'mkv'（默认'avi'）
            
        Returns:
            dict: 包含状态信息的字典
        """
        if not self.is_initialized or self.camera is None:
            return {"success": False, "error": "相机未初始化"}
        
        if self.is_recording:
            return {"success": False, "error": "已在录制中"}
        
        try:
            # 标准化格式
            format = format.lower().lstrip('.')
            supported_formats = ['mp4', 'avi', 'mov', 'mkv']
            
            if format not in supported_formats:
                return {
                    "success": False, 
                    "error": f"不支持的格式: {format}，支持的格式: {', '.join(supported_formats)}"
                }
            
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"video_{timestamp}.{format}"
            
            # 确保文件名有正确的扩展名
            file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
            if not file_ext or file_ext not in supported_formats:
                filename = os.path.splitext(filename)[0] + f'.{format}'
                file_ext = format
            else:
                format = file_ext  # 使用文件扩展名作为格式
            
            # 完整路径
            filepath = os.path.join(self.video_dir, filename)
            
            # 根据格式选择编码器（传递实际参数以测试编码器）
            fourcc, codec_name = self._get_fourcc_for_format(format, width, height, fps)
            self.video_writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
            
            if not self.video_writer.isOpened():
                return {"success": False, "error": "VideoWriter初始化失败"}
            
            # 在新线程中录制
            self.is_recording = True
            self.recording_thread = threading.Thread(
                target=self._record_video,
                args=(duration, width, height, filepath),
                daemon=True
            )
            self.recording_thread.start()
            
            self._log(f"🎥 开始录制视频: {filename}")
            self._log(f"   ├─ 格式: {format.upper()}")
            self._log(f"   ├─ 时长: {duration}秒")
            self._log(f"   ├─ 分辨率: {width}x{height}")
            self._log(f"   └─ 帧率: {fps} FPS")
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "format": format
            }
            
        except Exception as e:
            self._log(f"❌ 开始录制错误: {e}")
            self.is_recording = False
            return {"success": False, "error": str(e)}
    
    def _record_video(self, duration: int, width: int, height: int, filepath: str):
        """
        录制视频的内部方法（在独立线程中运行）
        
        Args:
            duration: 录制时长（秒）
            width: 视频宽度
            height: 视频高度
            filepath: 视频文件路径
        """
        start_time = time.time()
        frame_count = 0
        
        try:
            while self.is_recording and (time.time() - start_time) < duration:
                ret, frame = self.camera.read()
                
                if ret and frame is not None:
                    # 调整帧大小
                    if frame.shape[1] != width or frame.shape[0] != height:
                        frame = cv2.resize(frame, (width, height))
                    
                    self.video_writer.write(frame)
                    frame_count += 1
                else:
                    self._log("⚠️  读取帧失败")
                    break
            
            # 录制结束
            self._stop_recording()
            
            elapsed_time = time.time() - start_time
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            
            self._log(f"✅ 视频录制完成")
            self._log(f"   ├─ 实际时长: {elapsed_time:.2f}秒")
            self._log(f"   ├─ 总帧数: {frame_count}")
            self._log(f"   └─ 文件大小: {file_size/1024/1024:.2f} MB")
            
        except Exception as e:
            self._log(f"❌ 录制视频错误: {e}")
            self._stop_recording()
    
    def _stop_recording(self):
        """停止录制并释放资源"""
        self.is_recording = False
        
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
    
    def _get_fourcc_for_format(self, format_ext: str, width: int = 640, height: int = 480, fps: int = 20) -> tuple:
        """
        根据视频格式获取对应的fourcc编码器，并验证编码器是否可用
        
        Args:
            format_ext: 文件扩展名（如 'mp4', 'avi', 'mov'）
            width: 测试视频宽度
            height: 测试视频高度
            fps: 测试视频帧率
            
        Returns:
            tuple: (fourcc对象, 编码器名称)
        """
        format_ext = format_ext.lower().lstrip('.')
        
        # 不同格式的编码器映射
        if self.is_jetson:
            # Jetson平台：避免使用可能失败的硬件编码器，优先使用MJPG
            codec_map = {
                'mp4': ['MJPG', 'mp4v', 'X264', 'avc1'],  # MJPG最稳定
                'avi': ['MJPG', 'XVID', 'DIVX'],          # MJPEG较通用
                'mov': ['MJPG', 'mp4v', 'avc1'],          # MJPG优先
                'mkv': ['MJPG', 'X264', 'XVID']           # MJPG优先
            }
        else:
            # 标准PC平台编码器
            codec_map = {
                'mp4': ['mp4v', 'avc1', 'H264', 'X264'],  # MP4格式
                'avi': ['XVID', 'MJPG', 'DIVX'],          # AVI格式
                'mov': ['mp4v', 'avc1'],                   # MOV格式
                'mkv': ['X264', 'H264', 'XVID']            # MKV格式
            }
        
        codecs = codec_map.get(format_ext, ['MJPG', 'XVID'])
        
        # 测试文件路径
        test_file = os.path.join(self.video_dir, f".test_codec_{format_ext}.{format_ext}")
        
        # 尝试每个编码器
        for codec in codecs:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                
                # 实际测试编码器是否可用
                test_writer = cv2.VideoWriter(test_file, fourcc, fps, (width, height))
                
                if test_writer.isOpened():
                    test_writer.release()
                    # 删除测试文件
                    try:
                        if os.path.exists(test_file):
                            os.remove(test_file)
                    except:
                        pass
                    
                    self._log(f"   └─ 使用编码器: {codec}")
                    return fourcc, codec
                else:
                    test_writer.release()
                    
            except Exception as e:
                continue
        
        # 如果都失败，使用最稳定的MJPG
        self._log(f"   ⚠️  格式 {format_ext} 的编码器测试失败，使用默认MJPG")
        return cv2.VideoWriter_fourcc(*'MJPG'), 'MJPG'
    
    async def handle_websocket_message(self, websocket, path):
        """
        处理WebSocket消息
        
        Args:
            websocket: WebSocket连接对象
            path: 连接路径
        """
        client_address = websocket.remote_address
        client_ip = client_address[0] if client_address else "unknown"
        
        self._log(f"🔗 新客户端尝试连接: {client_address}")
        
        # IP验证
        allowed, reason = self._is_ip_allowed(client_ip)
        
        if not allowed:
            self._log(f"🚫 拒绝连接: {client_ip} - {reason}")
            error_message = {
                "success": False,
                "error": f"连接被拒绝: {reason}"
            }
            try:
                await websocket.send(json.dumps(error_message))
                await websocket.close(1008, reason)  # 1008 = Policy Violation
            except:
                pass
            return
        
        self._log(f"✅ 连接已接受: {client_ip} - {reason}")
        
        try:
            async for message in websocket:
                try:
                    # 解析JSON消息
                    data = json.loads(message)
                    command = data.get("command", "")
                    
                    self._log(f"📨 收到命令: {command} (来自 {client_address})")
                    
                    # 处理命令
                    if command == "capture":
                        # 拍照命令
                        filename = data.get("filename", None)
                        result = self.capture_photo(filename)
                        await websocket.send(json.dumps(result))
                    
                    elif command == "record":
                        # 录制视频命令
                        duration = data.get("duration", 10)
                        width = data.get("width", 1920)
                        height = data.get("height", 1080)
                        fps = data.get("fps", 30)
                        filename = data.get("filename", None)
                        format = data.get("format", "avi")
                        
                        result = self.start_recording(
                            duration=duration,
                            width=width,
                            height=height,
                            fps=fps,
                            filename=filename,
                            format=format
                        )
                        await websocket.send(json.dumps(result))
                    
                    elif command == "status":
                        # 查询状态
                        status = {
                            "initialized": self.is_initialized,
                            "recording": self.is_recording,
                            "camera_index": self.camera_index
                        }
                        await websocket.send(json.dumps(status))
                    
                    elif command == "ping":
                        # 心跳响应
                        pong_response = {
                            "success": True,
                            "pong": True,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(pong_response))
                    
                    else:
                        # 未知命令
                        error_response = {
                            "success": False,
                            "error": f"未知命令: {command}"
                        }
                        await websocket.send(json.dumps(error_response))
                        
                except json.JSONDecodeError:
                    error_response = {
                        "success": False,
                        "error": "无效的JSON格式"
                    }
                    await websocket.send(json.dumps(error_response))
                    
                except Exception as e:
                    self._log(f"❌ 处理消息错误: {e}")
                    error_response = {
                        "success": False,
                        "error": str(e)
                    }
                    await websocket.send(json.dumps(error_response))
        
        except websockets.exceptions.ConnectionClosed:
            self._log(f"🔌 客户端断开连接: {client_address}")
        except Exception as e:
            self._log(f"❌ WebSocket错误: {e}")
    
    async def start_websocket_server(self):
        """启动WebSocket服务器"""
        self._log("="*70)
        self._log("🌐 相机控制WebSocket服务器")
        self._log("="*70)
        self._log(f"📡 监听地址: {self.host}:{self.port}")
        self._log(f"📷 相机索引: {self.camera_index}")
        self._log("="*70)
        self._log("🔒 安全配置:")
        self._log(f"   ├─ 拒绝本机连接: {self.block_localhost}")
        self._log(f"   └─ 允许的网段数: {len(self.allowed_networks)}")
        for network in self.allowed_networks:
            self._log(f"      └─ {network}")
        self._log("="*70)
        self._log("\n支持的命令:")
        self._log("  1. 拍照: {\"command\": \"capture\", \"filename\": \"可选\"}")
        self._log("  2. 录制: {\"command\": \"record\", \"duration\": 10, \"width\": 1920, \"height\": 1080, \"fps\": 30, \"format\": \"mp4\"}")
        self._log("  3. 状态: {\"command\": \"status\"}")
        self._log("  4. 心跳: {\"command\": \"ping\"}")
        self._log("\n支持的视频格式: mp4, avi, mov, mkv")
        self._log("💡 按 Ctrl+C 停止服务器\n")
        
        # 配置 WebSocket 服务器参数，启用 ping/pong 心跳
        async with websockets.serve(
            self.handle_websocket_message, 
            self.host, 
            self.port,
            ping_interval=20,  # 每20秒发送一次ping
            ping_timeout=10,   # ping超时时间10秒
            close_timeout=10   # 关闭超时时间10秒
        ):
            self._log("✅ WebSocket服务器已启动")
            self._log("💓 心跳已启用: ping间隔20秒, 超时10秒")
            await asyncio.Future()  # 运行直到取消
    
    def run(self):
        """运行相机控制器（启动WebSocket服务器）"""
        try:
            # 初始化相机
            if not self.initialize_camera():
                self._log("❌ 相机初始化失败，退出")
                return
            
            # 预热相机
            if not self.warmup_camera():
                self._log("⚠️  相机预热失败，继续运行")
            
            # 启动WebSocket服务器
            asyncio.run(self.start_websocket_server())
            
        except KeyboardInterrupt:
            self._log("\n\n⚠️  收到停止信号，正在关闭...")
        except Exception as e:
            self._log(f"❌ 运行错误: {e}")
        finally:
            # 清理资源
            self.deinitialize_camera()
            self._log("✅ 相机控制器已停止")


def main():
    """主函数"""
    # 检查命令行参数
    import sys
    use_csi = '--csi' in sys.argv or '-c' in sys.argv
    
    # 创建相机控制器
    controller = CameraController(
        camera_index=0,      # 默认相机/CSI传感器ID
        host="0.0.0.0",      # 监听所有网络接口
        port=8765,           # WebSocket端口
        use_csi=use_csi      # 是否强制使用CSI相机
    )
    
    # 运行控制器
    controller.run()


if __name__ == "__main__":
    main()
