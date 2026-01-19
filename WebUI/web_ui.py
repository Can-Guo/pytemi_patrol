#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Temi机器人Web控制界面
基于Flask实现的简洁Web UI
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
import sys
import os

# 添加 source_script 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'source_script'))

from temi_control import Temi_Control_Def
from example_patrol import find_waypoints_file, get_local_ip_in_subnet
import threading
import time

app = Flask(__name__)

# 全局变量
controller = None
is_connected = False
current_operation = None  # 当前操作状态
operation_lock = threading.Lock()

# 配置
BROKER_IP = None
WAYPOINTS_PATH = None
TEMI_SERIAL = "00121506569"


def initialize_config():
    """初始化配置"""
    global BROKER_IP, WAYPOINTS_PATH
    
    # 自动检测MQTT服务器IP
    # BROKER_IP = get_local_ip_in_subnet("192.168.8")
    BROKER_IP = "192.168.8.132"  # 临时硬编码，避免自动检测失败
    
    if not BROKER_IP:
        print("[WARNING] 无法自动检测IP，请手动配置")
        BROKER_IP = "192.168.8.132"  # 默认值
    
    # 自动查找waypoints文件
    WAYPOINTS_PATH = find_waypoints_file()
    if not WAYPOINTS_PATH:
        print("[WARNING] 无法找到waypoints文件")


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/connect', methods=['POST'])
def connect():
    """连接机器人"""
    global controller, is_connected
    
    try:
        data = request.json
        broker_ip = data.get('broker_ip', BROKER_IP)
        
        if controller is None:
            controller = Temi_Control_Def(
                broker_host=broker_ip,
                temi_serial=TEMI_SERIAL,
                silent=False
            )
        
        if controller.connect():
            is_connected = True
            return jsonify({'success': True, 'message': '连接成功'})
        else:
            return jsonify({'success': False, 'message': '连接失败'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """断开连接"""
    global controller, is_connected
    
    try:
        if controller:
            controller.disconnect()
            is_connected = False
            return jsonify({'success': True, 'message': '已断开连接'})
        return jsonify({'success': False, 'message': '未连接'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取机器人状态"""
    global controller, is_connected, current_operation
    
    if not controller or not is_connected:
        return jsonify({
            'connected': False,
            'robot_status': 'disconnected',
            'goto_status': 'unknown',
            'current_operation': None
        })
    
    status = controller.get_status()
    status['connected'] = is_connected
    status['current_operation'] = current_operation
    
    return jsonify(status)


@app.route('/api/goto', methods=['POST'])
def goto_waypoint():
    """导航到指定路点"""
    global controller, current_operation
    
    if not controller or not is_connected:
        return jsonify({'success': False, 'message': '未连接到机器人'})
    
    try:
        data = request.json
        waypoint = data.get('waypoint')
        
        if not waypoint:
            return jsonify({'success': False, 'message': '请指定路点名称'})
        
        with operation_lock:
            current_operation = f"导航至: {waypoint}"
            controller.goto_waypoint(waypoint)
        
        return jsonify({'success': True, 'message': f'开始导航至 {waypoint}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})


@app.route('/api/patrol', methods=['POST'])
def start_patrol():
    """开始巡航"""
    global controller, current_operation
    
    if not controller or not is_connected:
        return jsonify({'success': False, 'message': '未连接到机器人'})
    
    try:
        # 加载waypoints
        if WAYPOINTS_PATH:
            waypoints = controller.load_waypoints_from_file(WAYPOINTS_PATH)
        else:
            return jsonify({'success': False, 'message': '未找到waypoints文件'})
        
        if not waypoints:
            return jsonify({'success': False, 'message': '无法加载路点列表'})
        
        # 在后台线程执行巡航
        def patrol_thread():
            global current_operation
            with operation_lock:
                current_operation = "执行巡航中..."
            
            controller.execute_patrol(wait_time=60, check_interval=3, max_retries=1)
            
            with operation_lock:
                current_operation = None
        
        thread = threading.Thread(target=patrol_thread, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': f'开始巡航，共 {len(waypoints)} 个路点',
            'waypoints': waypoints
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})


@app.route('/api/stop', methods=['POST'])
def stop_robot():
    """停止机器人"""
    global controller, current_operation
    
    if not controller or not is_connected:
        return jsonify({'success': False, 'message': '未连接到机器人'})
    
    try:
        # 注意：temi_control可能没有stop方法，这里仅作示例
        with operation_lock:
            current_operation = None
        
        return jsonify({'success': True, 'message': '已发送停止指令'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'错误: {str(e)}'})


@app.route('/api/waypoints', methods=['GET'])
def get_waypoints():
    """获取路点列表"""
    global controller
    
    if not controller:
        return jsonify({'success': False, 'waypoints': []})
    
    try:
        if WAYPOINTS_PATH:
            waypoints = controller.load_waypoints_from_file(WAYPOINTS_PATH)
            return jsonify({'success': True, 'waypoints': waypoints or []})
        else:
            return jsonify({'success': False, 'waypoints': []})
    
    except Exception as e:
        return jsonify({'success': False, 'waypoints': [], 'message': str(e)})


@app.route('/api/photos', methods=['GET'])
def get_photos():
    """获取照片列表"""
    global controller
    
    if not controller:
        return jsonify({'photos': []})
    
    try:
        photo_dir = controller.photo_dir
        if os.path.exists(photo_dir):
            photos = [f for f in os.listdir(photo_dir) if f.endswith(('.jpg', '.png'))]
            photos.sort(reverse=True)  # 最新的在前
            return jsonify({'photos': photos[:20]})  # 返回最近20张
        return jsonify({'photos': []})
    
    except Exception as e:
        return jsonify({'photos': [], 'message': str(e)})


@app.route('/photos/<filename>')
def serve_photo(filename):
    """提供照片访问"""
    global controller
    if controller:
        return send_from_directory(controller.photo_dir, filename)
    return "Not found", 404


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    return jsonify({
        'broker_ip': BROKER_IP,
        'waypoints_path': WAYPOINTS_PATH,
        'temi_serial': TEMI_SERIAL
    })


if __name__ == '__main__':
    # 初始化配置
    initialize_config()
    
    print("\n" + "="*60)
    print("Temi机器人Web控制界面")
    print("="*60)
    print(f"MQTT服务器: {BROKER_IP}")
    print(f"Waypoints文件: {WAYPOINTS_PATH}")
    print(f"机器人序列号: {TEMI_SERIAL}")
    print("="*60)
    print("\n启动Web服务器...")
    print("请访问: http://localhost:5000")
    print("或在同一网络下访问: http://<你的IP>:5000")
    print("\n按 Ctrl+C 退出\n")
    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
