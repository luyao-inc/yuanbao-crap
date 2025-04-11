#!/usr/bin/env python3
import asyncio
import sys
import os
from deepseek_client import DeepSeekClient

async def test_image_extraction(image_path):
    """测试从图像中提取表格"""
    print(f"测试从图像 {image_path} 中提取表格")
    
    # 确保tmp目录存在
    os.makedirs("tmp", exist_ok=True)
    
    # 初始化DeepSeek客户端
    client = DeepSeekClient()
    
    # 首先尝试检测表格区域
    cropped_path, error = client.detect_table_in_image(image_path)
    
    if error:
        print(f"检测表格区域失败: {error}")
        return
    
    print(f"成功检测表格区域: {cropped_path}")
    
    # 提取表格内容
    table_data = client.extract_table_from_image(cropped_path or image_path)
    
    if isinstance(table_data, dict) and "error" in table_data:
        print(f"提取表格数据失败: {table_data['error']}")
        return
    
    # 打印提取的表格数据
    print("\n提取的表格数据:")
    print("表头:", table_data.get("headers", []))
    print("行数:", len(table_data.get("rows", [])))
    
    # 格式化表格输出
    if "headers" in table_data and "rows" in table_data:
        headers = table_data["headers"]
        rows = table_data["rows"]
        
        # 计算列宽度
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 打印表头
        header_row = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers) if i < len(col_widths))
        separator = "-+-".join("-" * w for w in col_widths)
        
        print("\n格式化表格:")
        print(header_row)
        print(separator)
        
        # 打印数据行
        for row in rows:
            row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row) if i < len(col_widths))
            print(row_str)

async def test_text_extraction(text):
    """测试从文本中提取表格"""
    print("测试从文本中提取表格")
    
    # 初始化DeepSeek客户端
    client = DeepSeekClient()
    
    # 提取表格内容
    table_data = client.process_table_text(text)
    
    if isinstance(table_data, dict) and "error" in table_data:
        print(f"提取表格数据失败: {table_data['error']}")
        return
    
    # 打印提取的表格数据
    print("\n提取的表格数据:")
    print("表头:", table_data.get("headers", []))
    print("行数:", len(table_data.get("rows", [])))
    
    # 格式化表格输出
    if "headers" in table_data and "rows" in table_data:
        headers = table_data["headers"]
        rows = table_data["rows"]
        
        # 计算列宽度
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 打印表头
        header_row = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers) if i < len(col_widths))
        separator = "-+-".join("-" * w for w in col_widths)
        
        print("\n格式化表格:")
        print(header_row)
        print(separator)
        
        # 打印数据行
        for row in rows:
            row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row) if i < len(col_widths))
            print(row_str)

if __name__ == "__main__":
    # 检查参数
    if len(sys.argv) > 1:
        # 图像路径
        if os.path.exists(sys.argv[1]):
            asyncio.run(test_image_extraction(sys.argv[1]))
        else:
            print(f"错误: 文件 {sys.argv[1]} 不存在")
    else:
        # 测试示例表格文本
        sample_text = """
时间 | 方向 | 开仓 | 止盈 | 止损
20250411220 | 多 | 81000 | 83259 | 80000
        """
        asyncio.run(test_text_extraction(sample_text)) 