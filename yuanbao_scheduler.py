#!/usr/bin/env python3
import os
import time
import asyncio
import subprocess
import schedule
from datetime import datetime
from yuanbao_playwright import YuanbaoPlaywrightCrawler

def read_from_file(file_path, default_value):
    """从文件中读取内容，如果文件不存在则返回默认值"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content
        else:
            print(f"文件不存在: {file_path}，使用默认值: {default_value}")
            return default_value
    except Exception as e:
        print(f"读取文件出错: {e}，使用默认值: {default_value}")
        return default_value

async def run_trading_task():
    """执行交易策略获取任务"""
    crawler = None
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行交易策略获取任务...")
        
        # 创建爬虫实例
        crawler = await YuanbaoPlaywrightCrawler().setup()
        if not crawler:
            print("初始化爬虫失败")
            return False
            
        # 登录腾讯元宝
        print("登录腾讯元宝...")
        login_success = await crawler.login()
        if not login_success:
            print("登录失败")
            await crawler.close()
            return False
                
        # 点击新建对话按钮
        print("点击新建对话按钮...")
        new_chat_success = await crawler.click_new_chat_button()
        if not new_chat_success:
            print("点击新建对话按钮失败")
            await crawler.close()
            return False
        
        # 从prompt.txt读取提示词
        default_question = "请给我一套BTC日内交易策略，内容只包含方向/开仓价/止盈价/止损价的对应数值，例如：空/81,300/78,000/83,500。\n注意事项：\n1.除了数值外不要给我返回其他额外内容；\n2.每次只给我返回当前你认为概率最大的一条数据；\n3.开仓价/止盈价/止损价不要给一个范围，需要给一个具体的数值"
        question = read_from_file('prompt.txt', default_question)
        
        # 输入问题
        print(f"输入问题: {question}")
        input_success = await crawler.input_message(question)
        if not input_success:
            print("输入问题失败")
            await crawler.close()
            return False
            
        # 等待回答
        print("等待回答...")
        await asyncio.sleep(30)  # 等待30秒让AI生成回答
        
        # 截图保存回答
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"tmp/answer_screen_{timestamp}.png"
        await crawler.page.screenshot(path=screenshot_path)
        print(f"已保存答案截图: {screenshot_path}")
        
        # 使用process_image.py处理截图
        print("使用process_image.py处理截图并提取数据...")
        process = subprocess.run(
            ["python", "process_image.py", screenshot_path, "--auto-only"],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            print("数据提取成功")
            print(process.stdout)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 交易策略获取成功")
        else:
            print(f"数据提取失败: {process.stderr}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 交易策略获取失败")
        
        # 关闭浏览器
        print("关闭浏览器...")
        await crawler.close()
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行任务出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 确保关闭浏览器
        if crawler:
            try:
                await crawler.close()
            except:
                pass
                
        return False

def schedule_task():
    """安排执行交易策略获取任务"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 安排定时任务...")
    asyncio.run(run_trading_task())

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动定时执行脚本")
    
    # 从act_time.txt读取间隔时间（分钟）
    default_interval = 15
    try:
        interval = int(read_from_file('act_time.txt', str(default_interval)))
    except ValueError:
        print(f"间隔时间格式错误，使用默认值: {default_interval}分钟")
        interval = default_interval
    
    print(f"每{interval}分钟执行一次交易策略获取任务")
    
    # 立即执行一次
    print("立即执行第一次任务...")
    schedule_task()
    
    # 设置定时任务
    schedule.every(interval).minutes.do(schedule_task)
    
    # 显示下一次执行时间
    next_run = schedule.next_run()
    print(f"\n下一次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    last_minute = -1
    try:
        while True:
            # 每分钟显示一次剩余时间
            current_minute = datetime.now().minute
            if current_minute != last_minute:
                next_run = schedule.next_run()
                remaining = next_run - datetime.now()
                minutes, seconds = divmod(remaining.seconds, 60)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 距离下一次执行还有: {minutes}分{seconds}秒")
                last_minute = current_minute
                
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断，停止定时任务")
    except Exception as e:
        print(f"定时任务出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 