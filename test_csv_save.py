#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 monitor_photos.py 的修改
验证所有 JSON 字段是否正确保存到 CSV
"""
import os
import sys
import csv

# 添加父目录到path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor_photos import call_api, save_result

# 测试配置
TEST_IMAGE = "./pytemi/photos/a12charge_20260108_100446.png"
TEST_CSV = "./test_analysis_results.csv"

def test_api_and_csv():
    """测试 API 调用和 CSV 保存"""
    print("=" * 70)
    print("测试 API 调用和 CSV 保存功能")
    print("=" * 70)
    
    # 删除旧的测试文件
    if os.path.exists(TEST_CSV):
        os.remove(TEST_CSV)
        print(f"✅ 已删除旧测试文件: {TEST_CSV}\n")
    
    # 临时修改 RESULTS_FILE
    import monitor_photos
    original_file = monitor_photos.RESULTS_FILE
    monitor_photos.RESULTS_FILE = TEST_CSV
    
    try:
        # 1. 测试 API 调用
        print("步骤 1: 测试 API 调用")
        print("-" * 70)
        result_json = call_api(TEST_IMAGE)
        
        if result_json:
            print(f"✅ API 调用成功")
            print(f"   返回类型: {type(result_json)}")
            print(f"   JSON 字段: {list(result_json.keys())}")
            print()
            for key, value in result_json.items():
                value_str = str(value)[:80]
                print(f"   - {key}: {value_str}...")
            print()
        else:
            print("❌ API 调用失败")
            return
        
        # 2. 测试 CSV 保存
        print("\n步骤 2: 测试 CSV 保存")
        print("-" * 70)
        save_result("test_image.png", result_json)
        
        # 3. 验证 CSV 内容
        print("\n步骤 3: 验证 CSV 内容")
        print("-" * 70)
        if os.path.exists(TEST_CSV):
            with open(TEST_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                print(f"✅ CSV 文件已创建")
                print(f"   表头: {headers}")
                print(f"\n   数据行:")
                for i, row in enumerate(reader, 1):
                    print(f"\n   行 {i}:")
                    for key, value in row.items():
                        value_str = str(value)[:80]
                        print(f"     {key}: {value_str}...")
        else:
            print("❌ CSV 文件未创建")
            
        # 4. 测试错误情况
        print("\n\n步骤 4: 测试错误处理")
        print("-" * 70)
        save_result("error_test.png", "API调用失败")
        print("✅ 错误消息保存测试完成")
        
        # 5. 显示最终 CSV
        print("\n\n步骤 5: 最终 CSV 文件内容")
        print("=" * 70)
        if os.path.exists(TEST_CSV):
            with open(TEST_CSV, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        
        print("\n" + "=" * 70)
        print("✅ 测试完成！")
        print("=" * 70)
        print(f"\n测试文件保存在: {TEST_CSV}")
        print("请检查以下内容:")
        print("  1. CSV 包含所有 JSON 字段: image_filename, prompt_query, analyzed_result, water_leakage, 处理时间")
        print("  2. 数据正确保存在对应的列中")
        print("  3. 错误情况也被正确记录")
        
    finally:
        # 恢复原始配置
        monitor_photos.RESULTS_FILE = original_file


if __name__ == "__main__":
    test_api_and_csv()
