#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Temi Robot Control Class
Professional patrol control system with status monitoring
"""
import paho.mqtt.client as mqtt
import json
import time
import csv
import os
import cv2
from enum import Enum
from datetime import datetime


class RobotStatus(Enum):
    """Robot status enumeration"""
    STANDBY = "Standby"
    NAVIGATING = "Navigating"
    ERROR = "Error"


class Temi_Control_Def:
    """
    Temi Robot Control Class
    
    Features:
    1. Status monitoring (battery, position, waypoints)
    2. Navigation control (goto waypoint)
    3. Load waypoints from file (txt/csv)
    4. Sequential patrol execution
    5. Real-time status tracking (Standby/Navigating/Error)
    """
    
    def __init__(self, broker_host="192.168.8.132", broker_port=1883, 
                 temi_serial="00121506569", silent=False):
        """
        Initialize Temi control system
        
        Args:
            broker_host: MQTT broker IP address
            broker_port: MQTT broker port
            temi_serial: Temi robot serial number
            silent: Suppress log output
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.temi_serial = temi_serial
        self.silent = silent
        
        # MQTT client
        self.client = None
        
        # Robot state data
        self.status_data = {
            "battery_percentage": None,
            "waypoint_list": [],
            "position": None,
            "speed": 0.0,
            "goto_status": None,
            "goto_location": None
        }
        
        # Control state
        self.robot_status = RobotStatus.STANDBY
        self.is_connected = False
        self.patrol_waypoints = []
        self.current_waypoint_index = 0
        
        # Position tracking
        self.current_position = None  # Current confirmed waypoint (None = unknown/NaN)
        self.target_waypoint = None   # Target waypoint for current navigation
        self.position_status = "NaN"  # Position status: "NaN", "moving_to_next_point", "current_waypoint_XXX"
        
        # Photo capture settings - 自动定位到项目根目录的photos文件夹
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))  # pytemi根目录
        self.photo_dir = os.path.join(project_root, "photos")
        self._ensure_photo_directory()
        
        # Camera initialization (pre-opened for fast capture)
        self.camera = None
        self._init_camera()
        
        # Speed threshold for navigation detection (m/s)
        self.SPEED_THRESHOLD = 0.1
    
    def _log(self, message):
        """Internal logging function"""
        if not self.silent:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def _ensure_photo_directory(self):
        """确保photos目录存在"""
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)
    
    def _init_camera(self):
        """预初始化摄像头（保持连接以实现快速拍照）"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                # 设置缓冲区大小
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # 预热：读取并丢弃前3帧
                for _ in range(3):
                    self.camera.read()
                self._log("[INFO] 摄像头已就绪")
            else:
                self._log("[ERROR] 摄像头初始化失败，拍照功能将不可用")
                self.camera = None
        except Exception as e:
            self._log(f"[ERROR] 摄像头初始化错误: {e}")
            self.camera = None
    
    def _capture_photo(self, waypoint_name):
        """
        使用摄像头拍照并保存（超快速版：使用预初始化摄像头）
        
        Args:
            waypoint_name: 当前航点名称
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            # 检查摄像头是否可用
            if self.camera is None or not self.camera.isOpened():
                self._log("[WARNING]  摄像头不可用")
                return None
            
            # 生成文件名: waypoint_timestamp.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{waypoint_name}_{timestamp}.png"
            filepath = os.path.join(self.photo_dir, filename)
            
            # 直接读取当前帧（摄像头已预热）
            ret, frame = self.camera.read()
            
            if ret:
                # 保存图片
                cv2.imwrite(filepath, frame)
                self._log(f"[INFO] 照片已保存: {filepath}")
                return filepath
            else:
                self._log("[WARNING]  无法从摄像头读取图像")
                return None
                
        except Exception as e:
            self._log(f"[ERROR] 拍照失败: {e}")
            return None
    
    def _on_connect(self, client, userdata, flags, rc, *args, **kwargs):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            self._log(f"[INFO] Connected to MQTT Broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to all temi topics
            client.subscribe(f"temi/#", qos=1)
            
            self._log(f"[INFO] Subscribed to robot topics")
        else:
            self._log(f"[ERROR] Connection failed with code: {rc}")
            self.is_connected = False
    
    def _on_status_info(self, client, userdata, msg):
        """Callback for status/info messages"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            if "battery_percentage" in payload:
                self.status_data["battery_percentage"] = payload["battery_percentage"]
            if "waypoint_list" in payload:
                self.status_data["waypoint_list"] = payload["waypoint_list"]
            if "position" in payload:
                self.status_data["position"] = payload["position"]
            if "speed" in payload:
                self.status_data["speed"] = payload["speed"]
            
            self._update_robot_status()
            
        except Exception as e:
            self._log(f"[WARNING]  Error processing status: {e}")
    
    def _on_goto_event(self, client, userdata, msg):
        """Callback for waypoint/goto event messages"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            goto_status = payload.get("status")
            goto_location = payload.get("location")
            
            self.status_data["goto_status"] = goto_status
            self.status_data["goto_location"] = goto_location
            self._log(f"[NAV]  Navigation: {goto_location} - {goto_status}")
            
            # Update position tracking based on navigation events
            self._update_position_tracking(goto_location, goto_status)
            
            # Update robot status
            self._update_robot_status()
            
        except Exception as e:
            self._log(f"[WARNING]  Error processing goto event: {e}")
    
    def _update_position_tracking(self, goto_location, goto_status):
        """
        Update position tracking based on navigation events
        Implements pytemi-style waypoint arrival verification
        
        Position status states:
        - "NaN": Unknown position (initial state)
        - "moving_to_next_point": Actively navigating to target waypoint
        - "current_waypoint_XXX": Confirmed arrival at waypoint XXX
        
        Args:
            goto_location: Target location from MQTT event
            goto_status: Navigation status (start/calculating/going/complete/abort)
        """
        try:
            # Update position status based on navigation state
            if goto_status in ["start", "calculating", "going"]:
                # Robot is actively navigating
                self.position_status = "moving_to_next_point"
                
            elif goto_status == "complete":
                # Navigation completed - verify location matches target
                if goto_location and goto_location == self.target_waypoint:
                    # Confirmed arrival at target waypoint
                    self.current_position = goto_location
                    self.position_status = f"current_waypoint_{goto_location}"
                    self._log(f"[LOCAT] Position confirmed: {goto_location}")
                elif goto_location:
                    # Arrived at location (target may be None in manual navigation)
                    self.current_position = goto_location
                    self.position_status = f"current_waypoint_{goto_location}"
                    self._log(f"[LOCAT] Position updated: {goto_location}")
                    
            elif goto_status == "abort":
                # Navigation aborted - position remains at last confirmed location
                self.position_status = "moving_to_next_point"  # Transition state
                self._log(f"[WARNING]  Navigation aborted, position: {self.current_position or 'unknown'}")
                
        except Exception as e:
            self._log(f"[WARNING]  Error updating position tracking: {e}")
    
    def _update_robot_status(self):
        """Update robot status based on current data"""
        try:
            # Check for error conditions
            if self.status_data["battery_percentage"] is not None:
                if self.status_data["battery_percentage"] < 10:
                    self.robot_status = RobotStatus.ERROR
                    return
            
            # Check navigation status
            goto_status = self.status_data.get("goto_status")
            speed = self.status_data.get("speed", 0.0)
            
            # Determine status based on speed and navigation state
            if goto_status in ["going", "calculating"]:
                self.robot_status = RobotStatus.NAVIGATING
            elif speed > self.SPEED_THRESHOLD:
                self.robot_status = RobotStatus.NAVIGATING
            else:
                self.robot_status = RobotStatus.STANDBY
                
        except Exception as e:
            self._log(f"[WARNING]  Error updating status: {e}")
            self.robot_status = RobotStatus.ERROR
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self._log(f"[NET] Connecting to MQTT broker...")
            
            # Create MQTT client
            client_id = f"temi_control_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            try:
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=client_id
                )
            except (AttributeError, TypeError):
                self.client = mqtt.Client(client_id=client_id)
            
            # Set main on_connect callback first
            self.client.on_connect = self._on_connect
            
            # Connect and start loop
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            for i in range(timeout * 10):
                if self.is_connected:
                    break
                time.sleep(0.1)
            
            if not self.is_connected:
                raise ConnectionError("Failed to connect within timeout")
            
            # Now add message callbacks for specific topics (after connection)
            self.client.message_callback_add(
                f"temi/{self.temi_serial}/status/info",
                self._on_status_info
            )
            self.client.message_callback_add(
                f"temi/{self.temi_serial}/event/waypoint/goto",
                self._on_goto_event
            )
            self._log("[INFO] Message callbacks registered")
            
            # Wait for initial status
            self._log("[INFO] Waiting for initial status...")
            time.sleep(3)
            
            return True
            
        except Exception as e:
            self._log(f"[ERROR] Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker and release camera"""
        # Release camera
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        
        # Disconnect MQTT
        if self.client:
            self._log("[NET] Disconnecting from MQTT broker...")
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
    
    def get_status(self):
        """Get current robot status with position tracking"""
        return {
            "robot_status": self.robot_status.value,
            "battery": self.status_data["battery_percentage"],
            "speed": self.status_data["speed"],
            "goto_status": self.status_data["goto_status"],
            "goto_location": self.status_data["goto_location"],
            "available_waypoints": len(self.status_data["waypoint_list"]),
            # Position tracking (new)
            "current_position": self.current_position,
            "target_waypoint": self.target_waypoint,
            "position_status": self.position_status
        }
    
    def print_status(self):
        """Print current robot status with position tracking"""
        status = self.get_status()
        print(f"\n{'='*60}")
        print(f"Robot Status: {status['robot_status']}")
        print(f"{'='*60}")
        print(f"Battery: {status['battery']}%")
        print(f"Speed: {status['speed']} m/s")
        print(f"Navigation Target: {status['goto_location']} - {status['goto_status']}")
        print(f"")
        print(f"Position Tracking:")
        print(f"  Current Position: {status['current_position'] or 'NaN'}")
        print(f"  Target Waypoint: {status['target_waypoint'] or 'None'}")
        print(f"  Position Status: {status['position_status']}")
        print(f"")
        print(f"Available Waypoints: {status['available_waypoints']}")
        print(f"{'='*60}\n")
    
    def goto_waypoint(self, waypoint_name):
        """
        Navigate to specified waypoint
        
        Args:
            waypoint_name: Name of the waypoint
            
        Returns:
            bool: True if command sent successfully
        """
        try:
            if not self.is_connected:
                self._log("[ERROR] Not connected to MQTT broker")
                return False
            
            # Check if waypoint exists
            if waypoint_name not in self.status_data["waypoint_list"]:
                self._log(f"[WARNING]  Waypoint '{waypoint_name}' not found in robot memory")
                self._log(f"Available waypoints: {len(self.status_data['waypoint_list'])}")
            
            # Set target waypoint for position verification
            self.target_waypoint = waypoint_name
            
            # Send navigation command
            topic = f"temi/{self.temi_serial}/command/waypoint/goto"
            payload = json.dumps({"location": waypoint_name})
            
            self.client.publish(topic, payload, qos=1)
            self._log(f"[INFO] Command sent: goto '{waypoint_name}'")
            
            return True
            
        except Exception as e:
            self._log(f"[ERROR] Error sending goto command: {e}")
            return False
    
    def load_waypoints_from_file(self, filepath):
        """
        Load waypoints from txt or csv file
        
        File format:
        - Each line contains one waypoint name
        - Lines ending with ',' are parsed (comma is optional)
        - Empty lines and comments (#) are ignored
        
        Args:
            filepath: Path to waypoint file
            
        Returns:
            list: List of waypoint names
        """
        try:
            self.patrol_waypoints = []
            
            # Read file with error handling for encoding issues
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Remove null characters and other problematic characters
            content = content.replace('\x00', '').replace('\r', '')
            
            # Process each line
            for line in content.split('\n'):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Remove trailing comma if present
                waypoint = line.rstrip(',').strip()
                
                if waypoint:
                    self.patrol_waypoints.append(waypoint)
            
            self._log(f"[INFO] Loaded {len(self.patrol_waypoints)} waypoints from {filepath}")
            return self.patrol_waypoints
            
        except FileNotFoundError:
            self._log(f"[ERROR] File not found: {filepath}")
            return []
        except Exception as e:
            self._log(f"[ERROR] Error loading waypoints: {e}")
            return []
    
    def execute_patrol(self, wait_time=60, check_interval=3, max_retries=1):
        """
        Execute sequential patrol through loaded waypoints with retry mechanism
        
        Args:
            wait_time: Maximum wait time for each navigation attempt (seconds) - default 30s
            check_interval: Status check interval (seconds)
            max_retries: Maximum retry attempts per waypoint (default 1, total 2 attempts)
            
        Returns:
            bool: True if patrol completed successfully
        """
        if not self.patrol_waypoints:
            self._log("[ERROR] No waypoints loaded. Use load_waypoints_from_file() first.")
            return False
        
        if not self.is_connected:
            self._log("[ERROR] Not connected to MQTT broker")
            return False
        
        self._log(f"[INFO] Starting patrol: {len(self.patrol_waypoints)} waypoints")
        self._log(f"[INFO] Configuration: timeout={wait_time}s, max_retries={max_retries}")
        
        success_count = 0
        retry_count = 0
        skip_count = 0
        self.current_waypoint_index = 0
        
        for idx, waypoint in enumerate(self.patrol_waypoints):
            self.current_waypoint_index = idx
            
            self._log(f"\n[{idx+1}/{len(self.patrol_waypoints)}] Navigating to: {waypoint}")
            
            # Retry loop for each waypoint
            navigation_success = False
            for attempt in range(max_retries + 1):
                
                # Display retry attempt information
                if attempt > 0:
                    self._log(f"[RETRY] Retry attempt {attempt}/{max_retries} for: {waypoint}")
                    retry_count += 1
                    time.sleep(2)  # Brief delay before retry
                
                # Send goto command
                if not self.goto_waypoint(waypoint):
                    self._log(f"[WARNING]  Failed to send command for waypoint: {waypoint}")
                    if attempt < max_retries:
                        continue  # Retry
                    else:
                        break  # Skip after all retries failed
                
                # Wait for navigation to complete
                elapsed = 0
                navigation_complete = False
                
                while elapsed < wait_time:
                    time.sleep(check_interval)
                    elapsed += check_interval
                    
                    goto_status = self.status_data.get("goto_status")
                    goto_location = self.status_data.get("goto_location")
                    
                    # Check completion with position verification
                    if goto_status == "complete":
                        # Verify robot actually reached the target waypoint
                        if goto_location == waypoint:
                            # Confirmed arrival at target
                            self._log(f"[INFO] Reached waypoint: {waypoint}")
                            if attempt > 0:
                                self._log(f"   └─ Success after {attempt} retry(ies)")
                            self._log(f"   └─ Position verified: {self.position_status}")
                            
                            # 等待1秒后拍照
                            time.sleep(1)
                            self._capture_photo(waypoint)
                            
                            success_count += 1
                            navigation_success = True
                            navigation_complete = True
                            break
                        else:
                            # Navigation completed but location mismatch
                            self._log(f"[WARNING]  Navigation complete but location mismatch")
                            self._log(f"   Expected: {waypoint}, Actual: {goto_location}")
                            navigation_complete = True
                            break
                    
                    # Check for abort/error
                    elif goto_status == "abort":
                        self._log(f"[WARNING]  Navigation aborted for: {waypoint}")
                        navigation_complete = True
                        break
                    
                    # Check robot status
                    if self.robot_status == RobotStatus.ERROR:
                        self._log(f"[ERROR] Robot error detected. Stopping patrol.")
                        return False
                
                # Handle navigation result
                if navigation_success:
                    break  # Success, move to next waypoint
                
                if navigation_complete and goto_status == "abort":
                    # Aborted - retry if attempts remaining
                    if attempt < max_retries:
                        self._log(f"[INFO]   └─ Will retry due to abort")
                        continue
                    else:
                        self._log(f"[INFO]   └─ Skipping after abort and {max_retries} retry(ies)")
                        skip_count += 1
                        break
                
                # Check timeout
                if elapsed >= wait_time:
                    if attempt < max_retries:
                        self._log(f"[TIMEOUT]  Timeout waiting for waypoint: {waypoint}")
                        self._log(f"   └─ Will retry (attempt {attempt + 1}/{max_retries + 1})")
                    else:
                        self._log(f"[TIMEOUT]  Final timeout for waypoint: {waypoint}")
                        self._log(f"[TIMEOUT]   └─ Skipping after {max_retries + 1} failed attempt(s)")
                        skip_count += 1
                        break
            
            # Brief pause between waypoints
            time.sleep(1)
        
        # Generate final report
        self._log(f"\n{'='*60}")
        self._log(f"[INFO] Patrol Report")
        self._log(f"{'='*60}")
        self._log(f"[INFO] Total waypoints: {len(self.patrol_waypoints)}")
        self._log(f"[INFO] Successful: {success_count}")
        self._log(f"[INFO] Skipped: {skip_count}")
        self._log(f"[INFO] Total retries: {retry_count}")
        self._log(f"[INFO] Success rate: {success_count}/{len(self.patrol_waypoints)} ({100*success_count//len(self.patrol_waypoints)}%)")
        self._log(f"{'='*60}")
        
        return success_count == len(self.patrol_waypoints)
    
    def wait_until_ready(self, timeout=30):
        """
        Wait until robot is in Standby status (ready for commands)
        
        Args:
            timeout: Maximum wait time (seconds)
            
        Returns:
            bool: True if robot is ready
        """
        self._log("[INFO] Waiting for robot to be ready...")
        
        elapsed = 0
        while elapsed < timeout:
            if self.robot_status == RobotStatus.STANDBY:
                self._log("[INFO] Robot is ready")
                return True
            elif self.robot_status == RobotStatus.ERROR:
                self._log("[ERROR] Robot in error state")
                return False
            
            time.sleep(0.5)
            elapsed += 0.5
        
        self._log(f"[TIMEOUT]  Timeout waiting for ready state")
        return False


# Example usage
if __name__ == "__main__":
    # Initialize control system
    controller = Temi_Control_Def(
        broker_host="192.168.8.132",
        broker_port=1883,
        temi_serial="00121506569",
        silent=False
    )
    
    # Connect to robot
    if not controller.connect():
        print("[ERROR] Failed to connect to robot")
        exit(1)
    
    try:
        # Wait for robot to be ready
        controller.wait_until_ready()
        
        # Print initial status
        controller.print_status()
        
        # Example 1: Single waypoint navigation
        # controller.goto_waypoint("a13")
        # time.sleep(10)
        
        # Example 2: Load waypoints and execute patrol
        # waypoints = controller.load_waypoints_from_file("waypoints.txt")
        # if waypoints:
        #     controller.execute_patrol(wait_time=15)
        
        # Keep running to monitor status
        print("Press Ctrl+C to exit")
        while True:
            time.sleep(5)
            controller.print_status()
            
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        controller.disconnect()
