#!/usr/bin/env python3
import os
import time
import pickle
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    # 初始化Playwright
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        
        # 创建上下文
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        # 创建页面
        page = await context.new_page()
        
        # 存储cookie的文件
        cookies_file = "yuanbao_cookies.pkl"
        
        # 确保tmp目录存在并清空文件
        os.makedirs("tmp", exist_ok=True)
        print("清空tmp目录中的所有文件...")
        for filename in os.listdir("tmp"):
            file_path = os.path.join("tmp", filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"已删除: {file_path}")
            except Exception as e:
                print(f"删除文件时出错: {file_path}, {e}")
        
        # 打开腾讯元宝页面
        print("打开腾讯元宝页面...")
        await page.goto("https://yuanbao.tencent.com/")
        await page.wait_for_load_state("networkidle")
        
        # 尝试加载cookie实现自动登录
        if os.path.exists(cookies_file):
            print("尝试加载已保存的cookie...")
            try:
                with open(cookies_file, "rb") as f:
                    cookies = pickle.load(f)
                await context.add_cookies(cookies)
                print("已加载cookie")
                
                # 刷新页面以应用cookie
                await page.reload()
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"加载cookie失败: {e}")
        
        # 等待用户手动登录（如果需要）
        print("请确认是否已成功登录...")
        await page.screenshot(path="login_status.png")
        input("如果需要登录，请在浏览器中完成登录，然后按Enter继续...")
        
        # 保存当前的cookies
        cookies = await context.cookies()
        with open(cookies_file, "wb") as f:
            pickle.dump(cookies, f)
        print("已保存cookies供下次使用")
        
        # 点击"新建对话"按钮 - 使用坐标点击
        print("\n准备点击'新建对话'按钮...")
        await page.screenshot(path="before_new_chat.png")
        
        # 尝试通过文本内容查找
        print("尝试查找'新建对话'按钮...")
        try:
            # 尝试找到包含文本的按钮
            new_chat_button = await page.get_by_role("button", name="新建对话").first
            if new_chat_button:
                print("找到'新建对话'按钮，点击中...")
                await new_chat_button.click()
            else:
                # 直接使用坐标点击（左侧菜单中"新建对话"按钮的可能位置）
                print("未找到按钮，使用坐标点击左侧的'新建对话'按钮...")
                await page.mouse.click(120, 223)  # 尝试点击截图中的按钮位置
        except Exception as e:
            print(f"点击按钮时出错: {e}")
            print("使用坐标点击...")
            await page.mouse.click(120, 223)  # 尝试点击截图中的按钮位置
        
        # 等待页面更新
        print("等待新对话加载...")
        await asyncio.sleep(3)
        await page.screenshot(path="after_new_chat.png")
        
        # 定义要提问的问题
        question = "请给我一套BTC日内交易策略，按类似如下格式返回：方向：空/开仓价格：87345/止盈价格：85221/止损价格：88123："
        
        # 设置选项
        print("\n尝试查找并设置选项...")
        try:
            # 查找设置按钮（网页右上角可能的位置）
            await page.mouse.click(1330, 77)  # 尝试点击设置按钮
            await asyncio.sleep(1)
            await page.screenshot(path="settings_panel.png")
            
            # 尝试选择R1推理和联网搜索
            # 这些坐标需要根据实际界面调整
            # 假设联网搜索选项在设置面板的位置
            await page.mouse.click(700, 300)
            await asyncio.sleep(0.5)
            # 假设R1推理选项在设置面板的位置
            await page.mouse.click(700, 350)
            await asyncio.sleep(0.5)
            
            # 关闭设置面板（点击确定或关闭按钮）
            await page.mouse.click(800, 500)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"设置选项时出错: {e}")
        
        # 滚动到页面底部确保输入框可见
        print("\n滚动到页面底部寻找输入框...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        await page.screenshot(path="page_bottom.png")
        
        # 尝试点击页面底部中央位置（可能是输入框位置）
        print("尝试点击输入框可能的位置...")
        await page.mouse.click(960, 900)  # 屏幕底部中间位置
        await asyncio.sleep(1)
        
        # 尝试输入问题
        print(f"\n尝试输入问题: {question}")
        try:
            # 尝试在当前焦点元素输入文本
            await page.keyboard.type(question)
            await asyncio.sleep(1)
            
            # 发送问题 - 按回车
            print("按Enter键发送问题...")
            await page.keyboard.press("Enter")
            
            # 等待回答生成
            print("等待回答生成...")
            await page.screenshot(path="after_question.png")
            await asyncio.sleep(60)  # 等待60秒
            
            # 保存回答截图
            await page.screenshot(path="answer.png")
            print("已保存回答截图")
            
            # 提取回答文本
            print("\n请从浏览器中手动复制回答内容")
            answer = input("请粘贴回答内容（完成后按Enter）: ")
            
            # 保存回答到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yuanbao_result_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(answer)
            print(f"已保存回答到文件: {filename}")
        
        except Exception as e:
            print(f"操作过程中出错: {e}")
            print("请在浏览器中手动完成操作")
        
        # 等待用户确认关闭
        input("按Enter键关闭浏览器...")
        
        # 关闭浏览器
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 