#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from process_image import is_duplicate_data, save_to_csv

def test_deduplication():
    """测试去重功能"""
    print("\n=== 测试去重功能 ===\n")
    
    # 测试数据
    test_cases = [
        {
            "记录时间": "20250411_132449",
            "方向": "空",
            "开仓价": "80500-81300",
            "止盈价": "78000",
            "止损价": "83500"
        },
        {
            "记录时间": "20250411_134643",
            "方向": "空",
            "开仓价": "80500-81300",
            "止盈价": "78000",
            "止损价": "83500"
        },
        {
            "记录时间": "20250411_135259",
            "方向": "空",
            "开仓价": "80,500-81,300",  # 注意逗号格式
            "止盈价": "78,000",
            "止损价": "83,500"
        },
        {
            "记录时间": "20250411_140000",
            "方向": "多",  # 不同方向，不应被视为重复
            "开仓价": "80500-81300",
            "止盈价": "78000",
            "止损价": "83500"
        },
        {
            "记录时间": "20250411_141000",
            "方向": "空",
            "开仓价": "81300", # 价格差异大于0.5%，不应被视为重复
            "止盈价": "78000",
            "止损价": "83500"
        }
    ]
    
    # 准备测试CSV文件
    test_csv = "test_dedup.csv"
    if os.path.exists(test_csv):
        os.remove(test_csv)
    
    # 写入表头
    with open(test_csv, 'w', encoding='utf-8') as f:
        f.write("记录时间,方向,开仓价,止盈价,止损价\n")
    
    # 测试直接调用is_duplicate_data函数
    print("\n=== 测试is_duplicate_data函数 ===")
    
    # 初始化空的测试数据
    test_data = []
    
    # Case 1: 空列表，应返回False
    is_dup = is_duplicate_data(test_cases[0], test_data)
    print(f"Case 1: 空列表应返回False - 结果: {'成功' if not is_dup else '失败'}")
    
    # 添加第一条记录到测试数据
    test_data.append(test_cases[0])
    
    # Case 2: 完全相同的数据
    is_dup = is_duplicate_data(test_cases[1], test_data)
    print(f"Case 2: 完全相同的数据应返回True - 结果: {'成功' if is_dup else '失败'}")
    
    # Case 3: 格式不同但数值相同
    is_dup = is_duplicate_data(test_cases[2], test_data)
    print(f"Case 3: 格式不同但数值相同应返回True - 结果: {'成功' if is_dup else '失败'}")
    
    # Case 4: 方向不同
    is_dup = is_duplicate_data(test_cases[3], test_data)
    print(f"Case 4: 方向不同应返回False - 结果: {'成功' if not is_dup else '失败'}")
    
    # Case 5: 价格差异超过0.5%
    is_dup = is_duplicate_data(test_cases[4], test_data)
    print(f"Case 5: 价格差异超过0.5%应返回False - 结果: {'成功' if not is_dup else '失败'}")
    
    # 测试通过CSV文件逐条插入
    print("\n=== 测试通过CSV文件插入 ===")
    
    # 第一条数据应该被插入
    result1 = save_to_csv(test_cases[0], test_csv)
    print(f"Case 1: 第一条数据应该被插入 - 结果: {'成功' if result1 else '失败'}")
    
    # 第二条与第一条完全相同的数据不应被插入
    result2 = save_to_csv(test_cases[1], test_csv)
    print(f"Case 2: 重复数据不应被插入 - 结果: {'成功' if not result2 else '失败'}")
    
    # 第三条在格式上有差异但数值相同，不应被插入
    result3 = save_to_csv(test_cases[2], test_csv)
    print(f"Case 3: 格式不同但数值相同不应被插入 - 结果: {'成功' if not result3 else '失败'}")
    
    # 第四条方向不同，应该被插入
    result4 = save_to_csv(test_cases[3], test_csv)
    print(f"Case 4: 方向不同的数据应该被插入 - 结果: {'成功' if result4 else '失败'}")
    
    # 第五条价格超出误差范围，应该被插入
    result5 = save_to_csv(test_cases[4], test_csv)
    print(f"Case 5: 价格超出误差范围的数据应该被插入 - 结果: {'成功' if result5 else '失败'}")
    
    # 显示最终文件内容
    print("\n最终CSV文件内容:")
    with open(test_csv, 'r', encoding='utf-8') as f:
        print(f.read())
    
    # 清理测试文件
    if os.path.exists(test_csv):
        os.remove(test_csv)
        
    print("\n测试完成")

if __name__ == "__main__":
    test_deduplication() 