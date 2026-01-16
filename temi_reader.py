#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Temi 机器人状态信息读取器
从 MQTT Broker (192.168.8.132) 读取 Temi 机器人 (192.168.8.130) 的状态数据
"""
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime


class TemiStatusReader:
    """Temi 机器人状态读取器"""
    
    def __init__(self, broker_host="192.168.8.132", broker_port=1883, temi_serial="00121506569"):
        """
        初始化读取器
        
        Args:
            broker_host: MQTT Broker 地址
            broker_port: MQTT Broker 端口
            temi_serial: Temi 机器人序列号
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.temi_serial = temi_serial
        self.client = None
        self.latest_status = None
        self.message_count = 0
        
    def on_connect(self, client, userdata, flags, rc, *args, **kwargs):
        """MQTT 连接成功回调"""
        if rc == 0:
            print(f"\n{'='*80}")
            print("✅ 成功连接到 MQTT Broker")
            print(f"{'='*80}")
            print(f"Broker 地址: {self.broker_host}:{self.broker_port}")
            print(f"机器人序列号: {self.temi_serial}")
            
            # 订阅机器人状态主题
            topic = f"temi/{self.temi_serial}/status/info"
            result = client.subscribe(topic, qos=1)
            print(f"\n📡 已订阅主题: {topic}")
            print(f"{'='*80}\n")
        else:
            print(f"❌ 连接失败，返回码: {rc}")
    
    def on_message(self, client, userdata, msg):
        """接收到 MQTT 消息的回调"""
        self.message_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # 解析 JSON 数据
            self.latest_status = json.loads(msg.payload.decode('utf-8'))
            
            print(f"\n{'='*80}")
            print(f"📩 消息 #{self.message_count} | {timestamp}")
            print(f"{'='*80}")
            
            # 显示关键信息
            self._display_key_info()
            
            # 显示完整数据 (可选)
            if self.message_count == 1:  # 只在第一次显示完整数据
                self._display_full_data()
            
            print(f"{'='*80}\n")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
        except Exception as e:
            print(f"❌ 处理消息时出错: {e}")
    
    def _display_key_info(self):
        """显示关键信息摘要"""
        if not self.latest_status:
            return
        
        # 电池信息
        battery = self.latest_status.get("battery_percentage")
        if battery is not None:
            battery_icon = "🔋" if battery > 20 else "🪫"
            battery_status = "正常" if battery > 30 else "低电量"
            print(f"{battery_icon} 电池电量: {battery}% ({battery_status})")
        
        # 位置点信息
        waypoints = self.latest_status.get("waypoint_list", [])
        if waypoints:
            print(f"📍 已保存位置点: {len(waypoints)} 个")
            print(f"   前 10 个位置点: {', '.join(waypoints[:10])}")
            if len(waypoints) > 10:
                print(f"   ... 还有 {len(waypoints) - 10} 个位置点")
        
        # 其他可能的字段
        if "position" in self.latest_status:
            pos = self.latest_status["position"]
            if isinstance(pos, dict):
                x = pos.get("x", "N/A")
                y = pos.get("y", "N/A")
                print(f"📌 当前位置: X={x:.2f}, Y={y:.2f}")
        
        if "tilt_angle" in self.latest_status:
            tilt = self.latest_status["tilt_angle"]
            print(f"↕️  头部倾斜: {tilt}°")
    
    def _display_full_data(self):
        """显示完整的 JSON 数据"""
        print(f"\n{'-'*80}")
        print("📄 完整状态数据 (JSON):")
        print(f"{'-'*80}")
        print(json.dumps(self.latest_status, indent=2, ensure_ascii=False))
        print(f"{'-'*80}")
    
    def on_disconnect(self, client, userdata, rc, *args, **kwargs):
        """MQTT 断开连接回调"""
        print(f"\n⚠️  已断开连接 (返回码: {rc})")
    
    def start_reading(self, duration=60, continuous=False):
        """
        开始读取状态信息
        
        Args:
            duration: 读取持续时间(秒)，仅在 continuous=False 时有效
            continuous: 是否持续读取，True 表示一直运行直到手动中断
        """
        print(f"\n{'='*80}")
        print("Temi 机器人状态信息读取器")
        print(f"{'='*80}")
        print(f"MQTT Broker: {self.broker_host}:{self.broker_port}")
        print(f"Temi 机器人: {self.temi_serial} (192.168.8.130)")
        print(f"{'='*80}\n")
        
        try:
            # 创建 MQTT 客户端
            client_id = f"temi_reader_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            try:
                # paho-mqtt 2.x
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=client_id
                )
            except (AttributeError, TypeError):
                # paho-mqtt 1.x
                self.client = mqtt.Client(client_id=client_id)
            
            # 设置回调函数
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # 连接到 MQTT Broker
            print("🔌 正在连接到 MQTT Broker...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # 启动网络循环
            self.client.loop_start()
            
            # 根据模式运行
            if continuous:
                print("⏱️  持续读取模式，按 Ctrl+C 退出\n")
                while True:
                    time.sleep(1)
            else:
                print(f"⏱️  将读取 {duration} 秒，按 Ctrl+C 可提前退出\n")
                time.sleep(duration)
            
        except KeyboardInterrupt:
            print(f"\n\n{'='*80}")
            print("⏸️  用户中断")
            print(f"{'='*80}")
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理资源
            if self.client:
                print(f"\n📊 统计信息: 共接收 {self.message_count} 条消息")
                print("\n🔌 正在断开连接...")
                self.client.loop_stop()
                self.client.disconnect()
                print("✅ 已安全断开连接\n")
    
    def get_latest_status(self):
        """获取最新的状态数据"""
        return self.latest_status
    
    def get_battery_percentage(self):
        """获取电池百分比"""
        if self.latest_status:
            return self.latest_status.get("battery_percentage")
        return None
    
    def get_waypoint_list(self):
        """获取位置点列表"""
        if self.latest_status:
            return self.latest_status.get("waypoint_list", [])
        return []


def main():
    """主函数"""
    # 配置参数
    BROKER_HOST = "192.168.8.132"  # MQTT Broker 地址 (当前计算机)
    BROKER_PORT = 1883
    TEMI_SERIAL = "00121506569"    # Temi 机器人序列号
    
    # 创建读取器
    reader = TemiStatusReader(BROKER_HOST, BROKER_PORT, TEMI_SERIAL)
    
    # 开始读取 (持续模式)
    reader.start_reading(continuous=True)
    
    # 如果需要定时读取，使用：
    # reader.start_reading(duration=60, continuous=False)


if __name__ == "__main__":
    main()
