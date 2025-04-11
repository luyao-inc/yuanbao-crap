#!/usr/bin/env python3
import asyncio
import os
import sys
import json
import argparse
import csv
from datetime import datetime
from yuanbao_playwright import YuanbaoPlaywrightCrawler

def save_to_csv(data, csv_path="outputs.csv"):
    """将交易策略数据保存到CSV文件
    
    Args:
        data (dict): 包含表格数据的字典，需要有headers和rows字段
        csv_path (str): CSV文件路径
    
    Returns:
        bool: 是否成功保存
    """
    try:
        # 确定是否需要写入表头（如果文件不存在）
        file_exists = os.path.isfile(csv_path)
        
        # 准备当前时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 打开CSV文件进行写入
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            # 定义CSV字段
            fieldnames = ['记录时间', '时间', '方向', '开仓价', '止盈价', '止损价']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 如果文件是新创建的，写入表头
            if not file_exists:
                writer.writeheader()
            
            # 如果是标准表格数据格式
            if isinstance(data, dict) and 'table_data' in data and data['table_data']:
                table_data = data['table_data']
                
                if 'headers' in table_data and 'rows' in table_data:
                    # 获取表头和数据行
                    headers = table_data['headers']
                    rows = table_data['rows']
                    
                    # 映射表头到标准字段
                    header_map = {}
                    for i, header in enumerate(headers):
                        for field in ['时间', '方向', '开仓', '开仓价', '止盈', '止盈价', '止损', '止损价']:
                            if field in header:
                                if field.startswith('开仓'):
                                    header_map[i] = '开仓价'
                                elif field.startswith('止盈'):
                                    header_map[i] = '止盈价'
                                elif field.startswith('止损'):
                                    header_map[i] = '止损价'
                                else:
                                    header_map[i] = field
                    
                    # 写入每一行数据
                    for row in rows:
                        row_dict = {'记录时间': timestamp}
                        
                        # 填充行数据
                        for i, cell in enumerate(row):
                            if i in header_map:
                                row_dict[header_map[i]] = cell
                        
                        # 写入行
                        writer.writerow(row_dict)
                    
                    print(f"交易策略数据已写入CSV文件: {csv_path}")
                    return True
            
            # 如果是直接提供的数据行
            elif isinstance(data, list) and len(data) > 0:
                # 假设数据是一个字典列表，每个字典包含相应的字段
                for row_dict in data:
                    row_dict['记录时间'] = timestamp
                    writer.writerow(row_dict)
                
                print(f"交易策略数据已写入CSV文件: {csv_path}")
                return True
            
            # 如果是单行数据字典
            elif isinstance(data, dict) and any(key in data for key in ['方向', '开仓价', '止盈价', '止损价']):
                data['记录时间'] = timestamp
                writer.writerow(data)
                
                print(f"交易策略数据已写入CSV文件: {csv_path}")
                return True
            
            print("无法识别数据格式，无法写入CSV")
            return False
                
    except Exception as e:
        print(f"保存CSV时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

async def get_trading_strategy(question=None, wait_time=90, auto_close=False):
    """从元宝获取交易策略并提取表格数据"""
    print("启动元宝交易策略提取...")
    
    # 确保tmp目录存在
    os.makedirs("tmp", exist_ok=True)
    
    # 默认问题
    if not question:
        question = "请给我一套BTC日内交易策略，只给一条单一方向的策略，只回复方向/开仓价/止盈价/止损价这几个参数和对应的数据，以表格形式呈现，不要有任何其他内容"
    
    # 创建爬虫实例
    crawler = await YuanbaoPlaywrightCrawler().setup()
    
    # 检查爬虫是否成功初始化
    if crawler is None:
        print("爬虫初始化失败，程序退出")
        return None
    
    try:
        # 登录
        login_success = await crawler.login()
        if not login_success:
            print("自动登录失败，继续手动登录流程...")
        
        # 点击"新建对话"按钮
        await crawler.click_new_chat_button()
        
        # 设置选项（模型选择、模式切换等）
        await crawler.check_and_set_options()
        
        # 提问
        question_sent = await crawler.ask_question(question)
        if not question_sent:
            print("提问失败，请检查连接和浏览器状态")
            return None
        
        # 等待回答完成（默认90秒，可以通过参数调整）
        print(f"等待回答完成，最多等待{wait_time}秒...")
        await asyncio.sleep(wait_time)
        
        # 提取回答
        answer = await crawler.extract_answer()
        if answer:
            print("成功提取回答内容")
            
            # 处理提取到的答案，提取表格数据
            table_result = await crawler.process_answer(answer)
            
            # 自动关闭浏览器（如果指定）
            if auto_close:
                await crawler.close()
                print("浏览器已自动关闭")
            
            # 保存结果到CSV
            if table_result and "table_data" in table_result and table_result["table_data"]:
                save_to_csv(table_result)
            else:
                # 尝试手动解析答案文本
                print("尝试手动解析答案内容...")
                from deepseek_client import DeepSeekClient
                client = DeepSeekClient()
                parsed_data = client.process_table_text(answer)
                if parsed_data and "headers" in parsed_data and "rows" in parsed_data:
                    save_to_csv({"table_data": parsed_data})
                else:
                    print("无法自动解析为表格数据，请检查输出或手动处理")
            
            # 返回提取的数据
            return {
                "answer": answer,
                "table_data": table_result["table_data"] if table_result else None,
                "table_path": table_result["formatted_table_path"] if table_result else None
            }
        else:
            print("未能提取到回答内容")
            
            # 提示用户手动输入数据
            print("\n请手动查看截图并输入交易策略数据:")
            direction = input("方向 (例如:多/空): ")
            open_price = input("开仓价: ")
            take_profit = input("止盈价: ")
            stop_loss = input("止损价: ")
            
            # 如果用户至少输入了一项，保存到CSV
            if any([direction.strip(), open_price.strip(), take_profit.strip(), stop_loss.strip()]):
                manual_data = {
                    "方向": direction.strip(),
                    "开仓价": open_price.strip(),
                    "止盈价": take_profit.strip(),
                    "止损价": stop_loss.strip()
                }
                save_to_csv(manual_data)
                print("手动输入的数据已保存到CSV")
                
                return {"answer": None, "table_data": None, "manual_data": manual_data}
            
            return None
    except Exception as e:
        print(f"获取交易策略时出错: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 如果未自动关闭，确保爬虫关闭浏览器前用户有足够时间查看
        if not auto_close:
            print("\n查看完成后，按Enter键关闭浏览器...")
            try:
                input()
                await crawler.close()
                print("浏览器已关闭")
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="从元宝获取交易策略数据")
    parser.add_argument("--question", type=str, help="要提问的问题，默认是请求BTC交易策略")
    parser.add_argument("--wait-time", type=int, default=90, help="等待回答的最长时间（秒），默认为90秒")
    parser.add_argument("--auto-close", action="store_true", help="回答完成后自动关闭浏览器，默认需要手动确认关闭")
    parser.add_argument("--csv-path", type=str, default="outputs.csv", help="CSV输出文件路径，默认为outputs.csv")
    parser.add_argument("--process-image", type=str, help="处理已存在的截图文件并提取表格数据")
    args = parser.parse_args()
    
    # 如果指定了处理图像模式
    if args.process_image:
        process_existing_image(args.process_image, args.csv_path)
        return
    
    # 运行异步函数
    result = asyncio.run(get_trading_strategy(
        question=args.question,
        wait_time=args.wait_time,
        auto_close=args.auto_close
    ))
    
    # 显示结果
    if result:
        print("\n====== 获取到的交易策略 ======")
        
        # 显示表格数据（如果有）
        if result.get("table_data"):
            print("交易策略表格数据:")
            if "headers" in result["table_data"] and "rows" in result["table_data"]:
                # 打印表头
                print(" | ".join(result["table_data"]["headers"]))
                print("-" * 50)
                
                # 打印数据行
                for row in result["table_data"]["rows"]:
                    print(" | ".join(str(cell) for cell in row))
            
            # 显示保存的表格文件路径
            if result.get("table_path"):
                print(f"\n详细表格已保存到文件: {result['table_path']}")
        elif result.get("manual_data"):
            # 显示手动输入的数据
            print("手动输入的交易策略数据:")
            data = result["manual_data"]
            print(f"方向: {data.get('方向', 'N/A')}")
            print(f"开仓价: {data.get('开仓价', 'N/A')}")
            print(f"止盈价: {data.get('止盈价', 'N/A')}")
            print(f"止损价: {data.get('止损价', 'N/A')}")
        elif result.get("answer"):
            # 如果没有提取到表格，显示原始回答
            print("未能提取表格结构，显示原始回答:\n")
            print(result["answer"])
        
        print(f"\n数据已保存到CSV文件: {args.csv_path}")
    else:
        print("未能获取交易策略，请检查错误信息或手动查看浏览器")

def process_existing_image(image_path, csv_path="outputs.csv"):
    """从已存在的截图文件中提取表格数据并保存到CSV
    
    Args:
        image_path (str): 图像文件路径
        csv_path (str): CSV输出文件路径
    """
    try:
        print(f"处理现有图像: {image_path}")
        
        if not os.path.exists(image_path):
            print(f"错误: 图像文件不存在: {image_path}")
            return
        
        # 使用DeepSeek分析图像
        from deepseek_client import DeepSeekClient
        client = DeepSeekClient()
        
        # 提取图像中的表格内容
        print("分析图像中的表格内容...")
        result = client.extract_table_from_image(image_path)
        
        # 如果直接识别出表格结构
        if isinstance(result, dict) and "headers" in result and "rows" in result:
            print("成功从图像中识别出表格结构")
            table_data = result
            save_to_csv({"table_data": table_data}, csv_path)
            
            # 显示表格内容
            print("\n识别到的表格内容:")
            print(" | ".join(table_data["headers"]))
            print("-" * 50)
            for row in table_data["rows"]:
                print(" | ".join(str(cell) for cell in row))
                
            print(f"\n数据已保存到CSV文件: {csv_path}")
            return
        
        # 如果没有直接识别出表格结构，但提取了文本
        if isinstance(result, dict) and "text" in result:
            text = result["text"]
            print(f"从图像中提取到的文本:\n{text[:500]}...")
            
            # 使用PlaywrightCrawler中的方法处理文本
            from yuanbao_playwright import YuanbaoPlaywrightCrawler
            crawler = YuanbaoPlaywrightCrawler()
            
            # 从文本中提取交易数据
            trading_data = crawler.extract_trading_data_from_text(text)
            if trading_data:
                print("成功从文本中提取交易数据")
                save_to_csv({"table_data": trading_data}, csv_path)
                
                # 显示表格内容
                print("\n提取到的交易数据:")
                print(" | ".join(trading_data["headers"]))
                print("-" * 50)
                for row in trading_data["rows"]:
                    print(" | ".join(str(cell) for cell in row))
                    
                print(f"\n数据已保存到CSV文件: {csv_path}")
                return
            
            # 尝试使用模式匹配方法
            pattern_data = crawler.parse_table_with_patterns(text)
            if pattern_data:
                print("成功通过模式匹配提取表格数据")
                save_to_csv({"table_data": pattern_data}, csv_path)
                
                # 显示表格内容
                print("\n提取到的交易数据:")
                print(" | ".join(pattern_data["headers"]))
                print("-" * 50)
                for row in pattern_data["rows"]:
                    print(" | ".join(str(cell) for cell in row))
                    
                print(f"\n数据已保存到CSV文件: {csv_path}")
                return
            
            # 如果自动方法都失败，提示用户手动输入
            print("\n自动提取失败，请手动输入交易策略数据:")
            direction = input("方向 (例如:多/空): ")
            open_price = input("开仓价: ")
            take_profit = input("止盈价: ")
            stop_loss = input("止损价: ")
            
            # 如果用户至少输入了一项，保存到CSV
            if any([direction.strip(), open_price.strip(), take_profit.strip(), stop_loss.strip()]):
                manual_data = {
                    "方向": direction.strip(),
                    "开仓价": open_price.strip(),
                    "止盈价": take_profit.strip(),
                    "止损价": stop_loss.strip()
                }
                save_to_csv(manual_data, csv_path)
                print("手动输入的数据已保存到CSV")
            else:
                print("未输入任何数据，操作取消")
                
        else:
            print("无法从图像中提取任何有效数据")
            
    except Exception as e:
        print(f"处理图像时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 