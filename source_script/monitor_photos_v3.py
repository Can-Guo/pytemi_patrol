#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
照片监控与自动分析脚本
监控photos文件夹中的新照片，自动发送到API进行分析
"""
import os
import time
import requests
import csv
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread, Lock

# 配置
API_URL = "https://645t2cmhz085.share.zrok.io/analyze"
#API_URL = "http://161.81.250.66:6001/analyze"

# 使用脚本所在目录的photos文件夹
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(SCRIPT_DIR, "cam_photos")
RESULTS_FILE = os.path.join(SCRIPT_DIR, "analysis_results.csv")
TIME_THRESHOLD = 20  # 时间阈值（秒）
CHECK_INTERVAL = 2   # 检查间隔（秒）
#PROMPT = "Please describe the image."  # 默认提示词
PROMPT = "請描述一下圖片，看地面、地毯、天花板或牆身有否漏水、水氹、滲水、水漬的跡象"

# 全局变量
processed_files = set()  # 已处理的文件集合
file_lock = Lock()       # 文件写入锁
task_queue = Queue()     # 任务队列


def log(message):
    """输出带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def is_recent_file(filepath, threshold_seconds=TIME_THRESHOLD):
    """
    检查文件是否是最近创建的（时间戳在阈值内）
    
    Args:
        filepath: 文件路径
        threshold_seconds: 时间阈值（秒）
    
    Returns:
        bool: 如果文件是最近创建的返回True
    """
    try:
        file_time = os.path.getmtime(filepath)
        current_time = time.time()
        time_diff = current_time - file_time
        return time_diff <= threshold_seconds
    except Exception as e:
        log(f"⚠️  检查文件时间错误: {e}")
        return False


def call_api(image_path, prompt=PROMPT):
    """
    调用API分析图片
    
    Args:
        image_path: 图片路径
        prompt: 提示词
    
    Returns:
        dict: 完整的API响应JSON对象，失败返回None
    """
    try:
        log(f"📤 发送API请求: {os.path.basename(image_path)}")
        
        with open(image_path, "rb") as img_file:
            files = {"uploaded_file": img_file}
            data = {"prompt": prompt}
            response = requests.post(API_URL, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result_json = response.json()
            analyzed_result = result_json.get("analyzed_result", "")
            log(f"✅ API响应成功: {os.path.basename(image_path)}")
            log(f"   └─ 结果: {analyzed_result[:100]}...")  # 显示前100字符
            log(f"   └─ JSON字段: {list(result_json.keys())}")
            return result_json  # 返回完整的JSON对象
        else:
            log(f"❌ API响应错误 {response.status_code}: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        log(f"⏱️  API请求超时: {os.path.basename(image_path)}")
        return None
    except Exception as e:
        log(f"❌ API调用错误: {e}")
        return None


def save_result(filename, result_json):
    """
    保存分析结果到CSV文件（保存所有JSON字段）
    
    Args:
        filename: 图片文件名
        result_json: API返回的完整JSON对象 (dict) 或错误消息 (str)
    """
    try:
        with file_lock:
            # 检查文件是否存在
            file_exists = os.path.exists(RESULTS_FILE)
            
            # 如果result_json是字符串（错误消息），转换为dict
            if isinstance(result_json, str):
                result_data = {
                    'image_filename': filename,
                    'prompt_query': '',
                    'analyzed_result': result_json,
                    'water_leakage': ''
                }
            else:
                result_data = result_json.copy()
            
            # 添加处理时间字段
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_data['处理时间'] = timestamp
            
            # 定义列顺序（包含所有JSON字段）
            fieldnames = ['image_filename', 'prompt_query', 'analyzed_result', 'water_leakage', '处理时间']
            
            with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # 如果是新文件，写入表头
                if not file_exists:
                    writer.writeheader()
                    log(f"📝 创建结果文件: {RESULTS_FILE}")
                    log(f"   └─ 列: {fieldnames}")
                
                # 写入结果行（只写入定义的字段）
                row_data = {key: result_data.get(key, '') for key in fieldnames}
                writer.writerow(row_data)
                
            log(f"💾 结果已保存: {filename}")
            
    except Exception as e:
        log(f"❌保存结果错误: {e}")


def process_image(image_path):
    """
    处理单张图片的完整流程
    
    Args:
        image_path: 图片路径
    """
    filename = os.path.basename(image_path)
    
    log(f"🔄 开始处理: {filename}")
    
    # 调用API（返回完整的JSON对象）
    result_json = call_api(image_path)
    
    if result_json is not None:
        # 保存完整的JSON结果
        save_result(filename, result_json)
        log(f"✅ 处理完成: {filename}")
    else:
        # API调用失败，仍然记录
        save_result(filename, "API调用失败")
        log(f"⚠️  处理失败（已记录）: {filename}")


def worker_thread():
    """
    工作线程：从队列中取出任务并处理
    """
    log("🚀 工作线程已启动")
    
    while True:
        # 从队列获取任务（阻塞等待）
        image_path = task_queue.get()
        
        if image_path is None:  # 结束信号
            break
        
        try:
            # 处理图片
            process_image(image_path)
        except Exception as e:
            log(f"❌ 处理图片错误: {e}")
        finally:
            # 标记任务完成
            task_queue.task_done()


def monitor_photos():
    """
    监控photos文件夹中的新图片
    """
    log("="*70)
    log("📷 照片监控与自动分析系统")
    log("="*70)
    log(f"📁 监控目录: {os.path.abspath(PHOTOS_DIR)}")
    log(f"🌐 API地址: {API_URL}")
    log(f"📊 结果文件: {RESULTS_FILE}")
    log(f"⏱️  时间阈值: {TIME_THRESHOLD}秒")
    log(f"🔄 检查间隔: {CHECK_INTERVAL}秒")
    log("="*70)
    
    # 确保photos目录存在
    if not os.path.exists(PHOTOS_DIR):
        log(f"❌ 监控目录不存在: {PHOTOS_DIR}")
        return
    
    # 显示当前目录中的文件（调试信息）
    try:
        existing_files = [f for f in os.listdir(PHOTOS_DIR) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        log(f"📂 目录中现有 {len(existing_files)} 张图片")
        if existing_files:
            log(f"   示例: {existing_files[:3]}")
    except Exception as e:
        log(f"⚠️  无法读取目录: {e}")
    
    # 启动工作线程
    worker = Thread(target=worker_thread, daemon=True)
    worker.start()
    log("✅ 监控系统已启动")
    log("💡 按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            # 获取photos目录中的所有PNG文件
            try:
                files = [f for f in os.listdir(PHOTOS_DIR) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            except Exception as e:
                log(f"⚠️  读取目录错误: {e}")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 检查每个文件
            for filename in files:
                filepath = os.path.join(PHOTOS_DIR, filename)
                
                # 跳过已处理的文件
                if filename in processed_files:
                    continue
                
                # 检查文件是否存在且是最近创建的
                if not os.path.exists(filepath):
                    continue
                
                if not is_recent_file(filepath, TIME_THRESHOLD):
                    # 文件太旧，标记为已处理（避免重复检查）
                    processed_files.add(filename)
                    continue
                
                # 新文件：添加到队列
                file_age = time.time() - os.path.getmtime(filepath)
                log(f"🆕 检测到新图片: {filename}")
                log(f"   └─ 文件年龄: {file_age:.1f}秒")
                log(f"   └─ 当前队列任务数: {task_queue.qsize()}")
                
                task_queue.put(filepath)
                processed_files.add(filename)
            
            # 等待一段时间再检查
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        log("\n\n⚠️  收到停止信号，正在关闭...")
        
        # 等待队列中的任务完成
        if not task_queue.empty():
            log(f"⏳ 等待队列中的 {task_queue.qsize()} 个任务完成...")
            task_queue.join()
        
        # 发送结束信号给工作线程
        task_queue.put(None)
        worker.join(timeout=5)
        
        log("✅ 监控系统已停止")
        log(f"📊 共处理 {len(processed_files)} 张图片")
        log(f"📁 结果已保存至: {RESULTS_FILE}")
        

if __name__ == "__main__":
    monitor_photos()
