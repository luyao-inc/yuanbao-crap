#!/usr/bin/env python3
import os
import time
import json
import pickle
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from deepseek_client import DeepSeekClient

class YuanbaoPlaywrightCrawler:
    def __init__(self):
        self.url = "https://yuanbao.tencent.com/"
        self.cookies_file = "yuanbao_cookies.pkl"
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup(self):
        """设置Playwright和浏览器"""
        try:
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 清空tmp目录中的所有文件
            print("清空tmp目录中的所有文件...")
            for filename in os.listdir("tmp"):
                file_path = os.path.join("tmp", filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"已删除: {file_path}")
                except Exception as e:
                    print(f"删除文件时出错: {file_path}, {e}")
            
            # 导入Playwright
            from playwright.async_api import async_playwright
            
            # 初始化Playwright
            self.playwright = await async_playwright().start()
            
            # 使用更多启动参数确保窗口最大化和内容可见
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # 非无头模式，以便观察操作
                args=[
                    '--start-maximized',  # 最大化窗口
                    '--window-size=1920,1080',  # 设定窗口大小
                    # 不再设置设备缩放比例，使用原始大小
                    '--disable-infobars',  # 禁用信息栏
                    '--no-default-browser-check',  # 不检查默认浏览器
                    '--disable-extensions',  # 禁用扩展
                    '--disable-popup-blocking',  # 禁用弹窗拦截
                    '--disable-web-security',  # 禁用某些Web安全功能以避免样式警告
                    '--disable-features=IsolateOrigins,site-per-process',  # 禁用站点隔离以提高兼容性
                ]
            )
            
            # 使用一个非常大的视口大小，确保整个页面可以看到
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1600},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                ignore_https_errors=True,  # 忽略HTTPS错误
            )
            
            # 创建新页面
            self.page = await self.context.new_page()
            
            # 导航到腾讯元宝网站
            print("正在打开腾讯元宝网站...")
            await self.page.goto("https://yuanbao.tencent.com/", timeout=60000)
            
            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle")
            
            # 检查是否成功加载了元宝网站
            current_url = self.page.url
            if "yuanbao.tencent.com" not in current_url:
                print(f"警告：当前URL不是腾讯元宝网站: {current_url}")
                print("尝试重定向到正确的URL...")
                await self.page.goto("https://yuanbao.tencent.com/", timeout=60000)
                await self.page.wait_for_load_state("networkidle")
                
                # 再次检查URL
                current_url = self.page.url
                if "yuanbao.tencent.com" not in current_url:
                    print(f"错误：无法导航到腾讯元宝网站，当前URL: {current_url}")
                    return None
            
            print(f"成功加载腾讯元宝，当前URL: {current_url}")
            
            # 等待2秒确保页面完全加载
            await asyncio.sleep(2)
            
            # 保存屏幕截图
            await self.page.screenshot(path="tmp/initial_page.png")
            
            # 不再设置缩放
            await self.page.evaluate("""
                window.scrollTo(0, 0);
                
                // 重写控制台方法以忽略CSS空规则警告
                const originalConsoleWarn = console.warn;
                console.warn = function() {
                    const args = Array.from(arguments);
                    const message = args.join(' ');
                    
                    // 忽略CSS空规则警告
                    if (message.includes('css(emptyRules)') || 
                        message.includes('CSS syntax error') ||
                        message.includes('empty CSS rule')) {
                        return;
                    }
                    
                    // 传递其他警告
                    originalConsoleWarn.apply(console, args);
                };
            """)
            
            # 设置更大的视口大小
            await self.page.set_viewport_size({"width": 1920, "height": 1600})
            
            # 设置控制台消息过滤，忽略CSS空规则警告
            self.page.on("console", lambda msg: None if "css(emptyRules)" in msg.text else print(f"浏览器控制台: {msg.text}"))
            
            print("浏览器设置完成")
            return self
        except Exception as e:
            print(f"设置浏览器时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def load_cookies(self):
        """加载已保存的cookie"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "rb") as f:
                    cookies = pickle.load(f)
                    await self.context.add_cookies(cookies)
                return True
            except Exception as e:
                print(f"加载cookie时出错: {e}")
        return False
    
    async def save_cookies(self):
        """保存当前的cookie"""
        try:
            cookies = await self.context.cookies()
            with open(self.cookies_file, "wb") as f:
                pickle.dump(cookies, f)
            print("Cookie已保存")
        except Exception as e:
            print(f"保存cookie时出错: {e}")
    
    async def login(self):
        """登录腾讯元宝"""
        try:
            print("正在登录腾讯元宝...")
            
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 清空tmp目录中的所有文件
            print("清空tmp目录中的所有文件...")
            for filename in os.listdir("tmp"):
                file_path = os.path.join("tmp", filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"已删除: {file_path}")
                except Exception as e:
                    print(f"删除文件时出错: {file_path}, {e}")
            
            # 尝试加载之前保存的cookies
            cookies_loaded = await self.load_cookies()
            if cookies_loaded:
                print("已加载保存的登录信息")
                
                # 刷新页面并等待加载
                await self.page.reload()
                await self.page.wait_for_load_state("networkidle")
                
                # 验证是否已登录
                print("验证登录状态...")
                
                # 等待一段时间以确保页面完全加载
                await asyncio.sleep(2)
                
                # 尝试定位简介或用户名标识
                profile_indicator = None
                try:
                    profile_indicator = await self.page.query_selector('text="我的简介"')
                    if not profile_indicator:
                        profile_indicator = await self.page.query_selector('text="个人中心"')
                    if not profile_indicator:
                        # 检查 URL 是否包含已登录状态的特定路径
                        current_url = self.page.url
                        if "chat" in current_url and not "login" in current_url:
                            profile_indicator = True
                            print("通过URL确认已登录")
                except Exception as e:
                    print(f"检查登录元素时出错: {e}")
                
                if profile_indicator:
                    print("已成功登录元宝")
                    # 截图记录登录状态
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await self.page.screenshot(path=f"tmp/login_complete_{timestamp}.png")
                    return True
                else:
                    print("登录状态检查失败，尝试重新登录")
            
            # 在未登录情况下，尝试登录流程
            print("需要登录，请在浏览器中扫描QR码或输入账号密码...")
            
            # 截图记录登录前状态
            await self.page.screenshot(path="tmp/before_login_click.png")
            
            # 等待用户手动登录
            print("等待用户在浏览器中完成登录...")
            
            # 等待导航到登录成功后的页面，或检测登录状态
            max_wait_time = 300  # 最长等待5分钟
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # 每5秒检查一次登录状态
                await asyncio.sleep(5)
                
                # 检查是否已登录（URL变化或特定元素出现）
                try:
                    current_url = self.page.url
                    print(f"当前URL: {current_url}")
                    
                    if "chat" in current_url and not "login" in current_url:
                        print("检测到URL变化，可能已登录成功")
                        
                        # 额外等待以确保页面加载完成
                        await asyncio.sleep(2)
                        await self.page.wait_for_load_state("networkidle")
                        
                        # 截图记录登录完成状态
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        await self.page.screenshot(path=f"tmp/login_complete_{timestamp}.png")
                        
                        # 保存cookies以便下次使用
                        await self.save_cookies()
                        
                        return True
                    
                    # 再次尝试检查登录状态元素
                    profile_indicator = await self.page.query_selector('text="我的简介"')
                    if profile_indicator:
                        print("检测到'我的简介'元素，已登录成功")
                        
                        # 截图记录登录完成状态
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        await self.page.screenshot(path=f"tmp/login_complete_{timestamp}.png")
                        
                        # 保存cookies以便下次使用
                        await self.save_cookies()
                        
                        return True
                except Exception as e:
                    print(f"检查登录状态时出错: {e}")
                
                print("仍在等待登录完成...")
            
            print("登录等待超时，请手动确认是否已登录")
            return False
        
        except Exception as e:
            print(f"登录过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def click_new_chat_button(self):
        """点击新建对话按钮"""
        try:
            print("尝试点击'新建对话'按钮...")
            
            # 确保页面加载完成
            await self.page.wait_for_load_state("networkidle")
            
            # 截图记录点击前状态
            await self.page.screenshot(path="tmp/before_new_chat_click.png")
            
            # 尝试定位并点击"新建对话"按钮
            new_chat_button = None
            
            # 尝试多种选择器
            selectors = [
                'text="新建对话"',
                'button:has-text("新建对话")',
                '[class*="new-chat"]',
                '[class*="new"][class*="chat"]',
                'a:has-text("新建对话")',
                'div:has-text("新建对话"):not(:has(*))',
                'span:has-text("新建对话")'
            ]
            
            for selector in selectors:
                try:
                    new_chat_button = await self.page.query_selector(selector)
                    if new_chat_button:
                        print(f"找到'新建对话'按钮，使用选择器: {selector}")
                        await new_chat_button.click()
                        print("已点击'新建对话'按钮")
                        
                        # 等待页面变化
                        await asyncio.sleep(2)
                        await self.page.wait_for_load_state("networkidle")
                        
                        # 截图记录点击后状态
                        await self.page.screenshot(path="tmp/after_new_chat_click.png")
                        
                        return True
                except Exception as e:
                    print(f"尝试选择器 {selector} 失败: {e}")
            
            # 如果还未找到，尝试使用更通用的选择器
            try:
                # 查找可能包含"新建"文本的任何元素
                elements = await self.page.query_selector_all('button, a, div, span')
                for element in elements:
                    text = await element.text_content()
                    if "新建" in text or "新对话" in text:
                        print(f"找到可能的新建对话元素: {text}")
                        await element.click()
                        print("已点击可能的'新建对话'元素")
                        
                        # 等待页面变化
                        await asyncio.sleep(2)
                        await self.page.wait_for_load_state("networkidle")
                        
                        # 截图记录点击后状态
                        await self.page.screenshot(path="tmp/after_new_chat_click.png")
                        
                        return True
            except Exception as e:
                print(f"使用通用方法查找'新建对话'按钮失败: {e}")
            
            print("未能找到或点击'新建对话'按钮")
            # 截图记录错误状态
            await self.page.screenshot(path="tmp/new_chat_error.png")
            
            return False
        
        except Exception as e:
            print(f"点击'新建对话'按钮时出错: {e}")
            import traceback
            traceback.print_exc()
            # 截图记录错误状态
            await self.page.screenshot(path="tmp/new_chat_error.png")
            return False
    
    async def check_and_set_options(self):
        """检查并设置聊天选项（如模型选择等）"""
        try:
            print("检查并设置聊天选项...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 截图记录设置前状态
            await self.page.screenshot(path=f"tmp/yuanbao_before_settings_{timestamp}.png")
            
            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # 切换到高级模型
            await self.select_model("高级专业版")
            
            # 切换到流畅模式
            await self.switch_chat_mode("流畅模式")
            
            # 截图记录设置后状态
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await self.page.screenshot(path=f"tmp/yuanbao_after_settings_{timestamp}.png")
            
            return True
        
        except Exception as e:
            print(f"设置聊天选项时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def ask_question(self, question):
        """在元宝聊天界面提问"""
        try:
            print(f"准备提问: {question}")
            
            # 截图记录提问前状态
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await self.page.screenshot(path=f"tmp/yuanbao_before_question_{timestamp}.png")
            
            # 使用输入消息的通用方法
            message_sent = await self.input_message(question)
            
            if message_sent:
                print("提问成功，等待回答...")
                
                # 尝试滚动到页面底部以确保可以看到回答
                try:
                    # 使用JavaScript滚动到页面底部
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)  # 等待滚动完成
                    
                    # 截图记录滚动后状态
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await self.page.screenshot(path=f"tmp/yuanbao_after_scroll_{timestamp}.png")
                except Exception as e:
                    print(f"滚动页面时出错: {e}")
                
                return True
            else:
                print("提问失败")
                return False
        
        except Exception as e:
            print(f"提问过程中出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 截图记录错误状态
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await self.page.screenshot(path=f"tmp/yuanbao_question_error_{timestamp}.png")
            
            return False
    
    async def extract_answer(self):
        """提取最新的回答内容"""
        try:
            print("提取回答内容...")
            
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 等待答案完全生成
            import asyncio
            await asyncio.sleep(3)
            
            # 等待回答区域元素出现
            print("等待回答区域元素出现...")
            try:
                # 等待消息内容加载完成
                await self.page.wait_for_selector(".message:not(.user), .chat-item:not(.chat-item-user), [class*='assistant']", 
                                                timeout=5000)
                print("回答区域元素已出现")
            except Exception as e:
                print(f"等待回答区域超时，继续尝试截图: {e}")
            
            # 尝试截取完整对话区域
            chat_area = await self.page.query_selector(".conversation-container, .chat-container, [role='region']")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if chat_area:
                # 截取特定对话区域的屏幕截图
                chat_screenshot_path = f"tmp/chat_area_{timestamp}.png"
                await chat_area.screenshot(path=chat_screenshot_path)
                print(f"已捕获对话区域截图: {chat_screenshot_path}")
            
            # 同时截取全屏，确保不会遗漏内容
            full_screenshot_path = f"tmp/full_screen_{timestamp}.png"
            await self.page.screenshot(path=full_screenshot_path, full_page=True)
            print(f"已捕获全屏截图: {full_screenshot_path}")
            
            # 截取当前可见区域
            viewport_screenshot_path = f"tmp/answer_screen_{timestamp}.png"
            await self.page.screenshot(path=viewport_screenshot_path)
            print(f"已捕获可视区域截图: {viewport_screenshot_path}")
            
            # 尝试自动滚动并捕获最后的回答区域
            try:
                # 找到最后一条消息元素
                last_message = await self.page.evaluate("""() => {
                    const messages = document.querySelectorAll('.message:not(.user), .chat-item:not(.chat-item-user), [class*="assistant"]');
                    const lastMsg = messages[messages.length - 1];
                    if (lastMsg) {
                        // 滚动到元素位置
                        lastMsg.scrollIntoView({behavior: 'smooth', block: 'center'});
                        return true;
                    }
                    return false;
                }""")
                
                if last_message:
                    print("已滚动到最后一条消息")
                    # 等待滚动完成
                    await asyncio.sleep(1)
                    # 再次截图
                    last_answer_path = f"tmp/last_answer_{timestamp}.png"
                    await self.page.screenshot(path=last_answer_path)
                    print(f"已捕获最后一条消息截图: {last_answer_path}")
            except Exception as e:
                print(f"滚动到最后一条消息失败: {e}")
            
            # 优先使用OCR识别截图内容
            try:
                from deepseek_client import DeepSeekClient
                client = DeepSeekClient()
                
                # 用于存储所有识别结果
                all_results = []
                
                # 遍历所有截图尝试OCR识别
                print("使用OCR分析所有截图...")
                screenshot_paths = [
                    viewport_screenshot_path, 
                    chat_screenshot_path if 'chat_screenshot_path' in locals() else None,
                    full_screenshot_path,
                    last_answer_path if 'last_answer_path' in locals() else None
                ]
                
                for screenshot_path in screenshot_paths:
                    if screenshot_path and os.path.exists(screenshot_path):
                        print(f"分析截图: {screenshot_path}")
                        ocr_result = client.extract_table_from_image(screenshot_path)
                        
                        if isinstance(ocr_result, dict) and "error" not in ocr_result:
                            print(f"OCR识别成功: {screenshot_path}")
                            
                            # 从OCR结果提取交易策略数据
                            ocr_text = ""
                            
                            # 处理文本
                            if "text" in ocr_result:
                                ocr_text = ocr_result["text"]
                            
                            # 处理表格数据 
                            if "headers" in ocr_result and "rows" in ocr_result:
                                # 已经是表格格式
                                table_data = ocr_result
                                
                                # 从表格数据构建文本
                                ocr_text = "|".join(table_data["headers"]) + "\n"
                                for row in table_data["rows"]:
                                    ocr_text += "|".join(str(cell) for cell in row) + "\n"
                                
                                print(f"OCR直接提取出表格结构: {screenshot_path}")
                            
                            # 检查是否包含交易关键词
                            if any(term in ocr_text.lower() for term in ["方向", "开仓", "止盈", "止损", "多", "空"]):
                                # 根据关键词相关性评分
                                score = 0
                                for term in ["方向", "开仓", "止盈", "止损"]:
                                    if term in ocr_text:
                                        score += 1
                                if "多" in ocr_text or "空" in ocr_text:
                                    score += 1
                                if "|" in ocr_text or "表格" in ocr_text:
                                    score += 1
                                
                                all_results.append({"text": ocr_text, "score": score, "source": screenshot_path})
                                print(f"从 {screenshot_path} 提取的文本相关性得分: {score}")
                
                # 按得分排序提取结果
                if all_results:
                    all_results.sort(key=lambda x: x["score"], reverse=True)
                    best_result = all_results[0]
                    print(f"最佳OCR结果来自: {best_result['source']}, 得分: {best_result['score']}")
                    
                    # 保存最佳OCR结果
                    ocr_text_path = f"tmp/answer_ocr_{timestamp}.txt"
                    with open(ocr_text_path, "w", encoding="utf-8") as f:
                        f.write(best_result["text"])
                    print(f"OCR提取的文本已保存到: {ocr_text_path}")
                    
                    # 返回最佳OCR结果
                    return best_result["text"]
            except Exception as e:
                print(f"OCR处理失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 如果OCR未能提取到有效内容，尝试DOM方法
            print("尝试通过DOM方法提取内容...")
            
            # 尝试通过DOM获取页面文本
            page_text = await self.page.evaluate("""() => {
                // 获取所有可能包含回答的元素
                const elements = document.querySelectorAll('.message:not(.user), .chat-item:not(.chat-item-user), [class*="assistant"], .chat-content, [role="region"]');
                
                // 收集所有元素的文本
                let allText = '';
                for (const el of elements) {
                    allText += (el.innerText || el.textContent || '') + '\\n\\n';
                }
                
                return allText.trim();
            }""")
            
            if page_text:
                # 保存页面文本用于分析
                page_text_path = f"tmp/page_text_{timestamp}.txt"
                with open(page_text_path, "w", encoding="utf-8") as f:
                    f.write(page_text)
                print(f"页面文本已保存到: {page_text_path}")
                
                # 在文本中查找交易表格部分
                lines = page_text.split('\n')
                trading_lines = []
                
                for line in lines:
                    if any(term in line.lower() for term in ["方向", "开仓", "止盈", "止损", "多", "空"]):
                        trading_lines.append(line)
                
                if trading_lines:
                    trading_text = '\n'.join(trading_lines)
                    # 保存提取的交易相关文本
                    trading_text_path = f"tmp/trading_text_{timestamp}.txt"
                    with open(trading_text_path, "w", encoding="utf-8") as f:
                        f.write(trading_text)
                    print(f"提取的交易相关文本已保存到: {trading_text_path}")
                    return trading_text
            
            # 如果仍未提取到内容，保存更多诊断信息
            html_path = f"tmp/page_html_{timestamp}.html"
            html_content = await self.page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"已保存页面HTML用于诊断: {html_path}")
            
            # 如果所有自动方法都失败，请求手动输入
            print("所有自动提取方法失败，请手动查看截图并输入内容")
            
            # 打印截图路径提示
            print(f"\n请检查以下截图文件以查看回答内容:")
            for path in [viewport_screenshot_path, full_screenshot_path]:
                if path and os.path.exists(path):
                    print(f"- {path}")
            
            # 使用异步输入
            import asyncio
            
            # 定义异步输入函数
            async def async_input():
                print("\n请从浏览器中复制交易策略表格内容，然后粘贴到此处。")
                print("输入完成后按两次Enter键结束输入：")
                
                lines = []
                loop = asyncio.get_event_loop()
                while True:
                    line = await loop.run_in_executor(None, input)
                    if line == "" and (not lines or lines[-1] == ""):
                        break
                    lines.append(line)
                
                return "\n".join(lines).strip()
            
            manual_answer = await async_input()
            if manual_answer:
                return manual_answer
            
            return "无法提取回答内容，请查看保存的截图和诊断文件"
            
        except Exception as e:
            print(f"提取答案时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 使用异步输入
            import asyncio
            
            async def async_input():
                print("\n请手动从浏览器中复制交易策略表格内容，然后粘贴到此处。")
                print("输入完成后按两次Enter键结束输入：")
                
                lines = []
                loop = asyncio.get_event_loop()
                while True:
                    line = await loop.run_in_executor(None, input)
                    if line == "" and (not lines or lines[-1] == ""):
                        break
                    lines.append(line)
                
                return "\n".join(lines).strip()
            
            manual_answer = await async_input()
            if manual_answer:
                return manual_answer
            
            return "无法提取回答内容，请查看浏览器截图"
    
    async def save_to_file(self, content):
        """将内容保存到文本文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yuanbao_result_{timestamp}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"结果已保存到文件: {filename}")
            return filename
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return None
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            print("浏览器已关闭")
    
    async def run(self, question):
        """运行完整的爬取流程"""
        try:
            # 登录
            login_success = await self.login()
            if not login_success:
                print("自动登录失败，继续手动登录流程...")
            
            # 点击"新建对话"按钮
            await self.click_new_chat_button()
            
            # 设置选项（即使失败也继续执行）
            try:
                await self.check_and_set_options()
            except Exception as e:
                print(f"设置选项时出错: {e}，继续执行后续步骤...")
            
            # 提问（即使失败也继续，允许手动提问）
            question_sent = await self.ask_question(question)
            if not question_sent:
                print("提问过程中出现问题，可能需要手动介入...")
            
            # 提取答案
            answer = await self.extract_answer()
            if not answer:
                print("未能自动提取答案，使用手动输入...")
            else:
                # 处理提取到的答案，尤其是表格数据
                table_result = await self.process_answer(answer)
                
                # 保存结果
                file_path = await self.save_to_file(answer)
                if file_path:
                    print(f"结果已保存到文件: {file_path}")
                    
                    # 如果成功提取了表格，显示表格路径
                    if table_result:
                        print("表格数据处理成功:")
                        print(f"- 格式化表格文件: {table_result.get('formatted_table_path')}")
                        print(f"- 表格JSON数据: {table_result.get('table_json_path')}")
                else:
                    print("保存文件失败，显示最终结果:")
                    print("-" * 50)
                    print(answer)
                    print("-" * 50)
            
            print("爬取流程完成")
            return True
        
        except Exception as e:
            print(f"运行过程中出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 尝试截图保存当前状态
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await self.page.screenshot(path=f"tmp/yuanbao_error_{timestamp}.png")
                print(f"已保存错误状态截图: tmp/yuanbao_error_{timestamp}.png")
            except:
                pass
            
            print("发生错误，但将尝试手动完成剩余步骤...")
            
            # 尝试手动提取答案
            print("请从浏览器中查看结果...")
            answer = input("请从浏览器中复制答案并粘贴到这里：")
            
            if answer:
                # 尝试处理表格数据
                table_result = await self.process_answer(answer)
                
                file_path = await self.save_to_file(answer)
                if file_path:
                    print(f"结果已保存到文件: {file_path}")
                    
                    # 如果成功提取了表格，显示表格路径
                    if table_result:
                        print("表格数据处理成功:")
                        print(f"- 格式化表格文件: {table_result.get('formatted_table_path')}")
                        print(f"- 表格JSON数据: {table_result.get('table_json_path')}")
                else:
                    print("保存文件失败，显示最终结果:")
                    print("-" * 50)
                    print(answer)
                    print("-" * 50)
            
            return False
        finally:
            # 结束时不要关闭浏览器，以便查看结果
            pass

    async def input_message(self, message):
        """在输入框中输入消息并发送（通用方法）"""
        try:
            print(f"尝试输入消息: {message}")
            
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 截图输入前状态
            await self.page.screenshot(path="tmp/before_input.png")
            
            # 尝试多种输入框选择器
            input_selectors = [
                "textarea",
                "[contenteditable='true']",
                "[role='textbox']",
                ".chat-input textarea",
                ".input-container textarea",
                ".text-input",
                ".ant-input",
                "//div[@contenteditable='true']",
                "//div[contains(@class, 'chat-input')]"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    if selector.startswith("//"):
                        element = await self.page.query_selector(f"xpath={selector}")
                    else:
                        element = await self.page.query_selector(selector)
                    
                    if element and await element.is_visible():
                        input_element = element
                        print(f"找到可见的输入框，使用选择器: {selector}")
                        
                        # 确保输入框在视图中并且可交互
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(1)
                        break
                except Exception as e:
                    print(f"尝试选择器 {selector} 时出错: {e}")
            
            if not input_element:
                print("未找到可见的输入框，尝试JavaScript注入...")
                
                # 使用JavaScript尝试查找输入框并输入文本
                input_success = await self.page.evaluate("""(message) => {
                    function isVisible(elem) {
                        if (!elem) return false;
                        const style = window.getComputedStyle(elem);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               style.opacity !== '0' &&
                               elem.offsetWidth > 0 &&
                               elem.offsetHeight > 0;
                    }
                    
                    // 尝试各种可能的输入元素
                    const inputSelectors = [
                        'textarea', 
                        '[contenteditable="true"]', 
                        '[role="textbox"]',
                        '.chat-input textarea',
                        '.chat-input [contenteditable]',
                        '.input-container textarea',
                        '.message-input',
                        '.text-input'
                    ];
                    
                    for (const selector of inputSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            if (isVisible(el)) {
                                console.log('找到输入元素:', selector);
                                
                                // 滚动到元素位置
                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                
                                // 聚焦元素
                                el.focus();
                                
                                // 根据元素类型设置值
                                if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                                    el.value = message;
                                    
                                    // 触发必要的事件
                                    el.dispatchEvent(new Event('input', {bubbles: true}));
                                    el.dispatchEvent(new Event('change', {bubbles: true}));
                                } else if (el.getAttribute('contenteditable') === 'true') {
                                    el.innerHTML = message;
                                    
                                    // 触发必要的事件
                                    el.dispatchEvent(new Event('input', {bubbles: true}));
                                    el.dispatchEvent(new Event('change', {bubbles: true}));
                                }
                                
                                return true;
                            }
                        }
                    }
                    
                    // 如果无法找到输入元素，返回失败
                    return false;
                }""", message)
                
                if not input_success:
                    print("无法自动定位输入框")
                    # 保存错误状态截图
                    await self.page.screenshot(path="tmp/input_error.png")
                    return False
                else:
                    print("通过JavaScript成功找到输入框并输入消息")
            else:
                # 聚焦输入框并清除现有内容
                await input_element.focus()
                await input_element.fill("")
                
                # 输入新消息
                await input_element.fill(message)
                print("已输入消息")
            
            # 等待一会儿让输入稳定
            await asyncio.sleep(1)
            
            # 尝试通过按Enter键发送
            if input_element:
                await input_element.press("Enter")
                print("已按Enter键尝试发送")
            else:
                # 如果没有找到具体的输入元素但通过JS输入成功，使用页面级的Enter键
                await self.page.keyboard.press("Enter")
                print("已使用页面级键盘按Enter键")
            
            # 尝试查找并点击发送按钮（如果Enter键没有触发发送）
            send_button_found = False
            send_selectors = [
                "button:has-text('发送')",
                "button.send-button",
                "[aria-label='发送']",
                "//button[contains(text(), '发送')]",
                "//button[contains(@class, 'send')]",
                "button:right-of(textarea)",
                "button.ant-btn"
            ]
            
            for selector in send_selectors:
                try:
                    if selector.startswith("//"):
                        send_button = await self.page.query_selector(f"xpath={selector}")
                    else:
                        send_button = await self.page.query_selector(selector)
                    
                    if send_button and await send_button.is_visible():
                        await send_button.click()
                        print(f"已点击发送按钮: {selector}")
                        send_button_found = True
                        break
                except Exception as e:
                    print(f"尝试发送按钮选择器 {selector} 时出错: {e}")
            
            # 截图记录发送后状态
            await self.page.screenshot(path="tmp/after_input.png")
            
            return True
        except Exception as e:
            print(f"输入消息时出错: {e}")
            import traceback
            traceback.print_exc()
            # 截图记录错误状态
            await self.page.screenshot(path="tmp/message_input_error.png")
            return False

    async def select_model(self, model_name):
        """选择指定的模型"""
        try:
            print(f"尝试选择模型: {model_name}")
            
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 截图记录模型选择前状态
            await self.page.screenshot(path="tmp/before_model_select.png")
            
            # 查找模型选择器
            model_selector_found = False
            model_selectors = [
                "button:has-text('模型')",
                "[aria-label='选择模型']",
                "//button[contains(., '模型')]",
                ".model-selector",
                "button.model-select"
            ]
            
            for selector in model_selectors:
                try:
                    if selector.startswith("//"):
                        model_selector = await self.page.query_selector(f"xpath={selector}")
                    else:
                        model_selector = await self.page.query_selector(selector)
                    
                    if model_selector and await model_selector.is_visible():
                        await model_selector.click()
                        print(f"已点击模型选择器: {selector}")
                        model_selector_found = True
                        await asyncio.sleep(1)
                        break
                except Exception as e:
                    print(f"尝试模型选择器 {selector} 时出错: {e}")
            
            if not model_selector_found:
                print("未找到模型选择器，尝试使用JavaScript查找并点击")
                
                # 使用JavaScript寻找可能的模型选择器
                model_selector_clicked = await self.page.evaluate("""() => {
                    // 查找可能的模型选择器
                    function findModelSelector() {
                        // 通过文本内容查找
                        const elements = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                        
                        // 查找包含"模型"文本的元素
                        for (const el of elements) {
                            const text = el.innerText || el.textContent || '';
                            if (text.includes('模型') || text.includes('Model')) {
                                el.click();
                                console.log('找到并点击了模型选择器');
                                return true;
                            }
                        }
                        
                        // 如果找不到明确标记的元素，尝试查找可能的下拉菜单或选择器
                        const potentialSelectors = Array.from(document.querySelectorAll(
                            '.dropdown, .selector, [class*="model"], [class*="select"]'
                        ));
                        
                        for (const el of potentialSelectors) {
                            if (window.getComputedStyle(el).display !== 'none') {
                                el.click();
                                console.log('找到并点击了可能的模型选择器');
                                return true;
                            }
                        }
                        
                        return false;
                    }
                    
                    return findModelSelector();
                }""")
                
                if model_selector_clicked:
                    print("通过JavaScript找到并点击了可能的模型选择器")
                    model_selector_found = True
                    await asyncio.sleep(1)
            
            if not model_selector_found:
                print("未找到模型选择器")
                await self.page.screenshot(path="tmp/model_selector_not_found.png")
                return False
            
            # 选择指定的模型
            model_selected = False
            
            # 查找指定模型选项
            model_option_selectors = [
                f"text='{model_name}'",
                f"text='{model_name}'",
                f"//div[contains(text(), '{model_name}')]",
                f"//span[contains(text(), '{model_name}')]",
                f"//li[contains(., '{model_name}')]"
            ]
            
            for selector in model_option_selectors:
                try:
                    if selector.startswith("//"):
                        model_option = await self.page.query_selector(f"xpath={selector}")
                    else:
                        model_option = await self.page.query_selector(selector)
                    
                    if model_option and await model_option.is_visible():
                        await model_option.click()
                        print(f"已选择模型: {model_name}")
                        model_selected = True
                        await asyncio.sleep(1)
                        break
                except Exception as e:
                    print(f"尝试选择模型 {model_name} 时出错: {e}")
            
            if not model_selected:
                print(f"未找到指定模型: {model_name}，尝试使用JavaScript查找并选择")
                
                # 使用JavaScript查找并选择模型
                model_selected_js = await self.page.evaluate("""(modelName) => {
                    // 查找包含指定模型名称的元素
                    const elements = Array.from(document.querySelectorAll('*'));
                    
                    for (const el of elements) {
                        const text = el.innerText || el.textContent || '';
                        if (text.includes(modelName) && 
                            window.getComputedStyle(el).display !== 'none' &&
                            window.getComputedStyle(el).visibility !== 'hidden') {
                            
                            // 点击该元素
                            el.click();
                            console.log('找到并选择了模型:', modelName);
                            return true;
                        }
                    }
                    
                    return false;
                }""", model_name)
                
                if model_selected_js:
                    print(f"通过JavaScript成功选择模型: {model_name}")
                    model_selected = True
                    await asyncio.sleep(1)
            
            # 截图记录模型选择后状态
            await self.page.screenshot(path="tmp/after_model_select.png")
            
            return model_selected
        
        except Exception as e:
            print(f"选择模型时出错: {e}")
            import traceback
            traceback.print_exc()
            await self.page.screenshot(path="tmp/model_select_error.png")
            return False

    async def switch_chat_mode(self, mode):
        """切换聊天模式（例如：流畅模式，精准模式）"""
        try:
            print(f"尝试切换到 {mode} 模式")
            
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 截图记录模式切换前状态
            await self.page.screenshot(path=f"tmp/before_switch_to_{mode}.png")
            
            # 查找模式选择器
            mode_selector_found = False
            mode_selectors = [
                "button:has-text('模式')",
                "[aria-label='切换模式']",
                "//button[contains(., '模式')]",
                ".mode-selector",
                "button.mode-select"
            ]
            
            for selector in mode_selectors:
                try:
                    if selector.startswith("//"):
                        mode_selector = await self.page.query_selector(f"xpath={selector}")
                    else:
                        mode_selector = await self.page.query_selector(selector)
                    
                    if mode_selector and await mode_selector.is_visible():
                        await mode_selector.click()
                        print(f"已点击模式选择器: {selector}")
                        mode_selector_found = True
                        await asyncio.sleep(1)
                        break
                except Exception as e:
                    print(f"尝试模式选择器 {selector} 时出错: {e}")
            
            if not mode_selector_found:
                print("未找到模式选择器，尝试使用JavaScript查找并点击")
                
                # 使用JavaScript寻找可能的模式选择器
                mode_selector_clicked = await self.page.evaluate("""() => {
                    // 查找可能的模式选择器
                    function findModeSelector() {
                        // 通过文本内容查找
                        const elements = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                        
                        // 查找包含"模式"文本的元素
                        for (const el of elements) {
                            const text = el.innerText || el.textContent || '';
                            if (text.includes('模式') || text.includes('Mode')) {
                                el.click();
                                console.log('找到并点击了模式选择器');
                                return true;
                            }
                        }
                        
                        // 如果找不到明确标记的元素，尝试查找可能的下拉菜单或选择器
                        const potentialSelectors = Array.from(document.querySelectorAll(
                            '.dropdown, .selector, [class*="mode"], [class*="select"]'
                        ));
                        
                        for (const el of potentialSelectors) {
                            if (window.getComputedStyle(el).display !== 'none') {
                                el.click();
                                console.log('找到并点击了可能的模式选择器');
                                return true;
                            }
                        }
                        
                        return false;
                    }
                    
                    return findModeSelector();
                }""")
                
                if mode_selector_clicked:
                    print("通过JavaScript找到并点击了可能的模式选择器")
                    mode_selector_found = True
                    await asyncio.sleep(1)
            
            # 选择指定的模式
            mode_selected = False
            
            # 查找指定模式选项
            mode_option_selectors = [
                f"text='{mode}'",
                f"//div[contains(text(), '{mode}')]",
                f"//span[contains(text(), '{mode}')]",
                f"//li[contains(., '{mode}')]"
            ]
            
            for selector in mode_option_selectors:
                try:
                    if selector.startswith("//"):
                        mode_option = await self.page.query_selector(f"xpath={selector}")
                    else:
                        mode_option = await self.page.query_selector(selector)
                    
                    if mode_option and await mode_option.is_visible():
                        await mode_option.click()
                        print(f"已选择模式: {mode}")
                        mode_selected = True
                        await asyncio.sleep(1)
                        break
                except Exception as e:
                    print(f"尝试选择模式 {mode} 时出错: {e}")
            
            if not mode_selected:
                print(f"未找到指定模式: {mode}，尝试使用JavaScript查找并选择")
                
                # 使用JavaScript查找并选择模式
                mode_selected_js = await self.page.evaluate("""(modeName) => {
                    // 查找包含指定模式名称的元素
                    const elements = Array.from(document.querySelectorAll('*'));
                    
                    for (const el of elements) {
                        const text = el.innerText || el.textContent || '';
                        if (text.includes(modeName) && 
                            window.getComputedStyle(el).display !== 'none' &&
                            window.getComputedStyle(el).visibility !== 'hidden') {
                            
                            // 点击该元素
                            el.click();
                            console.log('找到并选择了模式:', modeName);
                            return true;
                        }
                    }
                    
                    return false;
                }""", mode)
                
                if mode_selected_js:
                    print(f"通过JavaScript成功选择模式: {mode}")
                    mode_selected = True
                    await asyncio.sleep(1)
            
            # 截图记录模式切换后状态
            await self.page.screenshot(path=f"tmp/after_switch_to_{mode}.png")
            
            return mode_selected
        
        except Exception as e:
            print(f"切换聊天模式时出错: {e}")
            import traceback
            traceback.print_exc()
            await self.page.screenshot(path=f"tmp/switch_mode_error_{mode}.png")
            return False

    async def upload_file(self, file_path, file_input_selector=None, confirm_selector=None, wait_for_upload=True, timeout=60000):
        """上传文件
        
        参数:
            file_path: 要上传的文件路径
            file_input_selector: 文件输入框选择器，如果为None将尝试自动查找
            confirm_selector: 确认按钮选择器，如果为None将尝试自动查找
            wait_for_upload: 是否等待上传完成
            timeout: 等待超时时间（毫秒）
            
        返回:
            bool: 上传成功返回True，失败返回False
        """
        try:
            print(f"开始上传文件: {file_path}")
            
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 确保文件存在
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return False
            
            # 截图上传前状态
            await self.page.screenshot(path="tmp/before_upload.png")
            
            # 如果没有提供文件输入选择器，尝试自动寻找
            if not file_input_selector:
                file_input_selectors = [
                    "input[type='file']",
                    "//input[@type='file']",
                    "[accept='*/*']",
                    "[accept='.pdf,.doc,.docx,.txt']",
                    "[accept='image/*']"
                ]
                
                for selector in file_input_selectors:
                    try:
                        if selector.startswith("//"):
                            file_input = await self.page.query_selector(f"xpath={selector}")
                        else:
                            file_input = await self.page.query_selector(selector)
                        
                        if file_input:
                            file_input_selector = selector
                            print(f"找到文件输入框: {selector}")
                            break
                    except Exception as e:
                        print(f"查找文件输入框 {selector} 时出错: {e}")
            
            # 如果仍找不到文件输入框，尝试查找上传按钮并点击
            if not file_input_selector:
                print("未找到文件输入框，尝试查找上传按钮...")
                
                upload_button_selectors = [
                    "button:has-text('上传')",
                    "button:has-text('Upload')",
                    "span:has-text('上传')",
                    "span:has-text('Upload')",
                    "//button[contains(., '上传')]",
                    "//button[contains(., 'Upload')]",
                    "//span[contains(., '上传')]",
                    "//span[contains(., 'Upload')]",
                    "[aria-label='上传文件']",
                    "[aria-label='Upload file']"
                ]
                
                for selector in upload_button_selectors:
                    try:
                        if selector.startswith("//"):
                            upload_button = await self.page.query_selector(f"xpath={selector}")
                        else:
                            upload_button = await self.page.query_selector(selector)
                        
                        if upload_button and await upload_button.is_visible():
                            await upload_button.click()
                            print(f"已点击上传按钮: {selector}")
                            await asyncio.sleep(1)
                            
                            # 点击后可能会显示文件选择器，再次尝试查找
                            for selector in file_input_selectors:
                                try:
                                    if selector.startswith("//"):
                                        file_input = await self.page.query_selector(f"xpath={selector}")
                                    else:
                                        file_input = await self.page.query_selector(selector)
                                    
                                    if file_input:
                                        file_input_selector = selector
                                        print(f"点击按钮后找到文件输入框: {selector}")
                                        break
                                except Exception as e:
                                    print(f"查找文件输入框 {selector} 时出错: {e}")
                            
                            break
                    except Exception as e:
                        print(f"尝试点击上传按钮 {selector} 时出错: {e}")
            
            # 如果仍然找不到文件输入框，尝试使用JavaScript
            if not file_input_selector:
                print("常规方法无法找到文件输入框，尝试使用JavaScript...")
                
                # 使用JavaScript查找或创建文件输入框
                file_input_created = await self.page.evaluate("""() => {
                    try {
                        // 查找现有的文件输入框
                        let fileInput = document.querySelector('input[type="file"]');
                        
                        // 如果找不到，创建一个新的
                        if (!fileInput) {
                            fileInput = document.createElement('input');
                            fileInput.type = 'file';
                            fileInput.id = 'tempFileInput';
                            fileInput.style.position = 'fixed';
                            fileInput.style.top = '0';
                            fileInput.style.left = '0';
                            fileInput.style.opacity = '0';
                            document.body.appendChild(fileInput);
                            
                            console.log('已创建临时文件输入框');
                            return true;
                        } else {
                            console.log('找到现有文件输入框');
                            return true;
                        }
                    } catch (e) {
                        console.error('创建文件输入框时出错:', e);
                        return false;
                    }
                }""")
                
                if file_input_created:
                    file_input_selector = "#tempFileInput, input[type='file']"
                    print("已使用JavaScript找到或创建文件输入框")
                else:
                    print("无法找到或创建文件输入框")
                    await self.page.screenshot(path="tmp/error_setting_file.png")
                    return False
            
            # 上传文件
            if file_input_selector:
                try:
                    print(f"尝试上传文件到选择器: {file_input_selector}")
                    await self.page.set_input_files(file_input_selector, file_path)
                    print(f"文件已设置到输入框: {file_path}")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"设置文件到输入框时出错: {e}")
                    await self.page.screenshot(path="tmp/error_setting_file.png")
                    return False
            
            # 如果需要确认上传，查找并点击确认按钮
            if not confirm_selector:
                confirm_selectors = [
                    "button:has-text('确认')",
                    "button:has-text('Confirm')",
                    "button:has-text('上传')",
                    "button:has-text('Upload')",
                    "button:has-text('确定')",
                    "button:has-text('OK')",
                    "//button[contains(., '确认')]",
                    "//button[contains(., '确定')]",
                    "//button[contains(., '上传')]",
                    "//button[contains(., 'Confirm')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Upload')]"
                ]
                
                for selector in confirm_selectors:
                    try:
                        if selector.startswith("//"):
                            confirm_button = await self.page.query_selector(f"xpath={selector}")
                        else:
                            confirm_button = await self.page.query_selector(selector)
                        
                        if confirm_button and await confirm_button.is_visible():
                            await confirm_button.click()
                            print(f"已点击确认按钮: {selector}")
                            break
                    except Exception as e:
                        print(f"尝试点击确认按钮 {selector} 时出错: {e}")
            else:
                try:
                    await self.page.click(confirm_selector)
                    print(f"已点击指定的确认按钮: {confirm_selector}")
                except Exception as e:
                    print(f"点击指定的确认按钮时出错: {e}")
            
            # 等待上传完成
            if wait_for_upload:
                print(f"等待上传完成，超时时间: {timeout/1000}秒")
                
                start_time = time.time()
                upload_complete = False
                
                while time.time() - start_time < timeout/1000:
                    try:
                        # 检查是否有上传完成的指示
                        upload_status = await self.page.evaluate("""() => {
                            // 查找上传状态指示器
                            const progressIndicators = document.querySelectorAll('.progress, .uploading, .loading, [role="progressbar"]');
                            
                            // 如果没有进度指示器，可能上传已完成
                            if (progressIndicators.length === 0) {
                                return 'complete';
                            }
                            
                            // 检查进度指示器是否表明上传完成
                            for (const indicator of progressIndicators) {
                                // 隐藏的进度条可能表示已完成
                                if (window.getComputedStyle(indicator).display === 'none' || 
                                    window.getComputedStyle(indicator).visibility === 'hidden') {
                                    return 'complete';
                                }
                                
                                // 检查进度条是否为100%
                                if (indicator.style.width === '100%' || 
                                    indicator.getAttribute('aria-valuenow') === '100') {
                                    return 'complete';
                                }
                            }
                            
                            // 检查是否有成功消息
                            const successMessages = document.querySelectorAll('.success, .uploaded, .complete');
                            if (successMessages.length > 0) {
                                return 'complete';
                            }
                            
                            // 检查是否有错误消息
                            const errorMessages = document.querySelectorAll('.error, .failed, .upload-error');
                            if (errorMessages.length > 0) {
                                return 'error';
                            }
                            
                            return 'uploading';
                        }""")
                        
                        if upload_status == 'complete':
                            upload_complete = True
                            print("检测到上传已完成")
                            break
                        elif upload_status == 'error':
                            print("检测到上传出错")
                            break
                        
                        # 等待一段时间再检查
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"检查上传状态时出错: {e}")
                        await asyncio.sleep(1)
                
                if upload_complete:
                    print("文件上传成功")
                    # 截图记录上传后状态
                    await self.page.screenshot(path="tmp/after_upload.png")
                    return True
                else:
                    print("上传超时或出错")
                    # 截图记录错误状态
                    await self.page.screenshot(path="tmp/error_upload.png")
                    return False
            else:
                # 如果不等待上传完成，假设上传成功
                print("已开始上传文件，不等待完成")
                # 截图记录当前状态
                await self.page.screenshot(path="tmp/after_upload.png")
                return True
        
        except Exception as e:
            print(f"上传文件时出错: {e}")
            import traceback
            traceback.print_exc()
            # 截图记录错误状态
            await self.page.screenshot(path="tmp/error_upload.png")
            return False

    async def extract_table_content(self, answer_text=None, screenshot_path=None):
        """从回答文本或截图中提取表格内容"""
        try:
            from deepseek_client import DeepSeekClient
            client = DeepSeekClient()
            
            table_data = None
            
            # 从OCR截图中提取
            if screenshot_path and os.path.exists(screenshot_path):
                print(f"尝试从截图中提取表格: {screenshot_path}")
                table_data = client.extract_table_from_image(screenshot_path)
                
                if isinstance(table_data, dict) and "headers" in table_data and "rows" in table_data:
                    print("成功从截图中提取表格数据")
                    return table_data
            
            # 如果没有提供文本但有截图，尝试获取文本内容
            if not answer_text and screenshot_path and os.path.exists(screenshot_path):
                # 使用OCR提取文本
                ocr_result = client.extract_table_from_image(screenshot_path)
                if isinstance(ocr_result, dict) and "text" in ocr_result:
                    answer_text = ocr_result["text"]
                    print(f"从截图中提取到文本: {answer_text[:100]}...")
            
            # 从文本中提取
            if answer_text:
                # 1. 直接检查是否包含完整交易策略数据
                trading_data = self.extract_trading_data_from_text(answer_text)
                if trading_data:
                    print("成功从文本中直接提取交易数据")
                    return trading_data
                
                # 2. 使用DeepSeek处理文本内容
                print("尝试使用DeepSeek处理文本内容")
                table_data = client.process_table_text(answer_text)
                
                if isinstance(table_data, dict) and "headers" in table_data and "rows" in table_data:
                    print("成功从文本中提取表格数据 (通过DeepSeek)")
                    return table_data
                
                # 3. 尝试使用正则表达式或模式匹配
                table_data = self.parse_table_with_patterns(answer_text)
                if table_data:
                    print("成功从文本中提取表格数据 (通过模式匹配)")
                    return table_data
            
            print("未能从回答中提取表格内容")
            return None
            
        except Exception as e:
            print(f"提取表格内容时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_trading_data_from_text(self, text):
        """从文本中提取交易策略数据
        
        识别以下格式的交易数据:
        1. 表格格式: 时间|方向|开仓|止盈|止损
        2. 键值对格式: 方向: 多, 开仓价: 81000, 止盈价: 83259, 止损价: 80000
        3. 单行格式: 多/81000/83259/80000
        
        Args:
            text (str): 要处理的文本
            
        Returns:
            dict: 包含表格数据的字典，包括headers和rows字段
        """
        try:
            lines = text.strip().split("\n")
            
            # 1. 查找包含表格的行 (检查是否包含竖线分隔符)
            table_lines = []
            for line in lines:
                # 检查是否包含交易关键字并且含有分隔符
                if ("|" in line or "\t" in line) and any(term in line for term in ["方向", "时间", "开仓", "止盈", "止损", "多", "空"]):
                    table_lines.append(line)
            
            # 如果找到可能的表格行
            if table_lines:
                # 确定分隔符
                separator = "|" if "|" in table_lines[0] else "\t"
                
                # 处理表头和数据行
                headers = []
                rows = []
                
                # 尝试找到表头行
                header_line = None
                for line in table_lines:
                    if any(term in line for term in ["方向", "时间", "开仓", "止盈", "止损"]):
                        header_line = line
                        break
                
                if header_line:
                    # 提取表头
                    headers = [h.strip() for h in header_line.split(separator) if h.strip()]
                    
                    # 提取数据行
                    for line in table_lines:
                        if line != header_line and any(term in line for term in ["多", "空"]) or any(c.isdigit() for c in line):
                            row_data = [cell.strip() for cell in line.split(separator) if cell.strip()]
                            if len(row_data) >= 3:  # 至少有方向、开仓、止盈/止损三个值
                                rows.append(row_data)
                
                if headers and rows:
                    return {"headers": headers, "rows": rows}
            
            # 2. 从键值对格式提取数据 (方向: 多, 开仓价: 81000, 止盈价: 83259, 止损价: 80000)
            direction = None
            open_price = None
            take_profit = None
            stop_loss = None
            time_value = None
            
            # 搜索关键字对应的值
            import re
            
            # 查找方向
            direction_match = re.search(r"方向[：:]\s*([多空做]|多单|空单|多头|空头)", text)
            if direction_match:
                direction = direction_match.group(1)
            
            # 查找时间
            time_match = re.search(r"时间[：:]\s*([0-9]+)", text)
            if time_match:
                time_value = time_match.group(1)
            
            # 查找开仓价
            open_match = re.search(r"开仓[价格]*[：:]\s*([0-9,.]+)", text)
            if open_match:
                open_price = open_match.group(1).replace(",", "")
            
            # 查找止盈价
            tp_match = re.search(r"止盈[价格]*[：:]\s*([0-9,.]+)", text)
            if tp_match:
                take_profit = tp_match.group(1).replace(",", "")
            
            # 查找止损价
            sl_match = re.search(r"止损[价格]*[：:]\s*([0-9,.]+)", text)
            if sl_match:
                stop_loss = sl_match.group(1).replace(",", "")
            
            # 如果提取到关键数据，构建表格格式
            if any([direction, open_price, take_profit, stop_loss]):
                headers = ["时间", "方向", "开仓价", "止盈价", "止损价"]
                rows = [[
                    time_value or "",
                    direction or "",
                    open_price or "",
                    take_profit or "",
                    stop_loss or ""
                ]]
                return {"headers": headers, "rows": rows}
            
            # 3. 特定模式：在文本中查找类似 "多/81000/83259/80000" 的组合
            # 这种格式通常是 方向/开仓价/止盈价/止损价
            for line in lines:
                # 查找以多或空开头，后面跟数字的格式
                pattern = r"(多|空)\s*[\/|]\s*([0-9,.]+)\s*[\/|]\s*([0-9,.]+)\s*[\/|]\s*([0-9,.]+)"
                match = re.search(pattern, line)
                
                if match:
                    direction = match.group(1)
                    open_price = match.group(2).replace(",", "")
                    take_profit = match.group(3).replace(",", "")
                    stop_loss = match.group(4).replace(",", "")
                    
                    headers = ["方向", "开仓价", "止盈价", "止损价"]
                    rows = [[direction, open_price, take_profit, stop_loss]]
                    return {"headers": headers, "rows": rows}
            
            # 4. 寻找页面中可能包含的表格结构
            # 在整个文本中查找包含交易策略关键字的段落
            trading_paragraph = None
            for line in lines:
                if sum(1 for term in ["方向", "开仓", "止盈", "止损"] if term in line) >= 2:
                    trading_paragraph = line
                    break
            
            if trading_paragraph:
                # 尝试拆分成表格格式
                # 可能的分隔符：空格、冒号、逗号
                for sep in [' ', ':', '：', ',', '，']:
                    parts = [p.strip() for p in trading_paragraph.split(sep) if p.strip()]
                    if len(parts) >= 4:
                        # 这可能是包含关键信息的段落
                        # 尝试提取方向、开仓价、止盈价、止损价
                        for i, part in enumerate(parts):
                            if '方向' in part and i+1 < len(parts):
                                direction = parts[i+1]
                            elif '开仓' in part and i+1 < len(parts):
                                open_price = parts[i+1].replace(",", "")
                            elif '止盈' in part and i+1 < len(parts):
                                take_profit = parts[i+1].replace(",", "")
                            elif '止损' in part and i+1 < len(parts):
                                stop_loss = parts[i+1].replace(",", "")
                
                # 如果提取到关键数据，构建表格格式
                if any([direction, open_price, take_profit, stop_loss]):
                    headers = ["方向", "开仓价", "止盈价", "止损价"]
                    rows = [[
                        direction or "",
                        open_price or "",
                        take_profit or "",
                        stop_loss or ""
                    ]]
                    return {"headers": headers, "rows": rows}
            
            return None
            
        except Exception as e:
            print(f"提取交易数据时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_table_with_patterns(self, text):
        """使用多种模式匹配方法解析文本中的表格
        
        Args:
            text (str): 要解析的文本
            
        Returns:
            dict: 表格数据，包含headers和rows
        """
        try:
            import re
            
            # 1. 查找Markdown风格的表格
            md_pattern = r"\|(.*)\|\n\|[-:| ]+\|\n((?:\|.*\|\n)+)"
            md_match = re.search(md_pattern, text, re.MULTILINE)
            
            if md_match:
                header_line = md_match.group(1)
                data_lines = md_match.group(2).strip().split("\n")
                
                headers = [h.strip() for h in header_line.split("|") if h.strip()]
                rows = []
                
                for line in data_lines:
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                    if cells:
                        rows.append(cells)
                
                if headers and rows:
                    return {"headers": headers, "rows": rows}
            
            # 2. 查找特定的时间格式：20250411之类的日期加时间，然后是多/空
            date_pattern = r"(\d{8}|\d{6}|\d{4}\d{2}\d{2})(\d{4}|\d{2}:\d{2})?\s*[|\/]\s*(多|空)\s*[|\/]\s*(\d+)"
            date_matches = re.findall(date_pattern, text)
            
            if date_matches:
                headers = ["时间", "方向", "开仓价", "止盈价", "止损价"]
                rows = []
                
                for match in date_matches:
                    # 收集该行附近的所有数字，可能是开仓价、止盈价、止损价
                    line_text = text[text.find(match[0]):text.find(match[0]) + 200]  # 查看匹配行后的200个字符
                    numbers = re.findall(r"(\d{5,})", line_text)  # 找出5位及以上的数字，可能是价格
                    
                    # 构建行数据
                    time_stamp = match[0] + (match[1] or "")
                    direction = match[2]
                    prices = numbers[:3]  # 最多取3个价格：开仓、止盈、止损
                    
                    # 确保有足够的价格数据
                    while len(prices) < 3:
                        prices.append("")
                    
                    rows.append([time_stamp, direction] + prices)
                
                if rows:
                    return {"headers": headers, "rows": rows}
            
            # 3. 查找以方向（多/空）开头，后面跟数字的格式
            direction_pattern = r"(多|空)[^0-9]*(\d{4,})[^0-9]*(\d{4,})[^0-9]*(\d{4,})"
            direction_matches = re.findall(direction_pattern, text)
            
            if direction_matches:
                headers = ["方向", "开仓价", "止盈价", "止损价"]
                rows = []
                
                for match in direction_matches:
                    rows.append(list(match))
                
                if rows:
                    return {"headers": headers, "rows": rows}
            
            return None
            
        except Exception as e:
            print(f"使用模式解析表格时出错: {e}")
            return None
    
    async def process_answer(self, answer_text):
        """处理回答，提取表格并保存结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 确保tmp目录存在
            os.makedirs("tmp", exist_ok=True)
            
            # 使用DeepSeek分析和格式化文本
            from deepseek_client import DeepSeekClient
            deepseek_client = DeepSeekClient()
            
            print("使用DeepSeek处理和格式化交易策略数据...")
            
            # 使用DeepSeek提取和格式化表格
            format_prompt = """
            从以下文本中提取BTC交易策略的关键信息，并格式化为包含以下列的表格：
            1. 时间
            2. 方向
            3. 开仓
            4. 止盈
            5. 止损
            
            如果某些字段不存在，请标记为"N/A"。确保输出为纯表格格式，不要有任何额外解释:
            
            ```
            {}
            ```
            """.format(answer_text)
            
            formatted_result = deepseek_client.format_trading_strategy(answer_text, format_prompt)
            
            if formatted_result and isinstance(formatted_result, str) and len(formatted_result) > 10:
                print("DeepSeek成功格式化交易策略数据")
                
                # 保存格式化后的结果
                formatted_text_path = f"tmp/formatted_answer_{timestamp}.txt"
                with open(formatted_text_path, "w", encoding="utf-8") as f:
                    f.write(formatted_result)
                print(f"格式化结果已保存到: {formatted_text_path}")
                
                # 尝试从格式化文本中提取表格结构
                table_data = await self.extract_table_content(formatted_result)
                
                if not table_data:
                    # 如果无法从格式化文本中提取表格，尝试直接解析
                    print("无法从格式化文本中提取表格，尝试直接解析")
                    
                    # 分析文本，识别表格结构
                    lines = [line.strip() for line in formatted_result.split('\n') if line.strip()]
                    
                    # 查找表头行
                    header_line = None
                    for line in lines:
                        if '时间' in line and '方向' in line and ('开仓' in line or '止盈' in line or '止损' in line):
                            header_line = line
                            break
                    
                    if header_line:
                        # 确定分隔符
                        separator = '|' if '|' in header_line else ' '
                        
                        # 提取表头
                        headers = [h.strip() for h in header_line.split(separator) if h.strip()]
                        
                        # 查找数据行
                        rows = []
                        for line in lines:
                            if line != header_line and (('多' in line or '空' in line) or any(c.isdigit() for c in line)):
                                cells = [c.strip() for c in line.split(separator) if c.strip()]
                                if len(cells) >= 3:  # 至少有3个单元格才可能是有效数据行
                                    # 确保数据行与表头长度匹配
                                    while len(cells) < len(headers):
                                        cells.append("N/A")
                                    if len(cells) > len(headers):
                                        cells = cells[:len(headers)]
                                    rows.append(cells)
                        
                        if rows:
                            table_data = {
                                "headers": headers,
                                "rows": rows
                            }
                            print("成功从格式化文本中提取表格结构")
                
                # 如果成功提取了表格结构
                if table_data:
                    # 生成格式化的表格文本
                    if "headers" in table_data and "rows" in table_data:
                        headers = table_data["headers"]
                        rows = table_data["rows"]
                        
                        # 计算每列的最大宽度
                        col_widths = [len(str(h)) for h in headers]
                        for row in rows:
                            for i, cell in enumerate(row):
                                if i < len(col_widths):
                                    col_widths[i] = max(col_widths[i], len(str(cell)))
                        
                        # 生成表格字符串
                        table_str = []
                        
                        # 添加表头
                        header_row = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers) if i < len(col_widths))
                        table_str.append(header_row)
                        
                        # 添加分隔线
                        separator = "-+-".join("-" * w for w in col_widths)
                        table_str.append(separator)
                        
                        # 添加数据行
                        for row in rows:
                            row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row) if i < len(col_widths))
                            table_str.append(row_str)
                        
                        # 保存格式化的表格文本
                        formatted_table_path = f"yuanbao_table_{timestamp}.txt"
                        with open(formatted_table_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(table_str))
                        print(f"格式化表格已保存到: {formatted_table_path}")
                        
                        # 保存表格数据为JSON
                        table_json_path = f"tmp/table_data_{timestamp}.json"
                        with open(table_json_path, "w", encoding="utf-8") as f:
                            json.dump(table_data, f, ensure_ascii=False, indent=2)
                        print(f"表格数据已保存到: {table_json_path}")
                        
                        # 返回提取的表格数据和路径
                        return {
                            "table_data": table_data,
                            "formatted_table_path": formatted_table_path,
                            "table_json_path": table_json_path
                        }
                
                # 如果没有成功提取表格结构但有格式化文本
                print("未能提取表格结构，但有格式化文本")
                formatted_table_path = f"yuanbao_table_{timestamp}.txt"
                with open(formatted_table_path, "w", encoding="utf-8") as f:
                    f.write(formatted_result)
                print(f"格式化结果已保存到: {formatted_table_path}")
                
                return {
                    "table_data": None,
                    "formatted_table_path": formatted_table_path
                }
            
            # 如果DeepSeek格式化失败，回退到原始提取方法
            print("DeepSeek格式化失败，尝试标准表格提取")
            
            # 先尝试直接从文本中提取表格内容
            print("尝试从文本中提取表格结构...")
            table_data = await self.extract_table_content(answer_text, None)
            
            # 如果直接从文本提取失败，且页面上可能有表格，再尝试截图方法
            if not table_data:
                # 检查文本中是否可能包含表格（有多个|符号的行）
                has_table_pattern = any(line.count('|') > 1 for line in answer_text.split('\n'))
                
                if has_table_pattern:
                    print("文本中可能包含表格，尝试使用截图方法...")
                    # 截图当前页面以捕获表格
                    screenshot_path = f"tmp/full_screenshot_{timestamp}.png"
                    await self.page.screenshot(path=screenshot_path)
                    print(f"已保存页面截图用于表格提取: {screenshot_path}")
                    
                    # 通过截图提取表格内容
                    table_data = await self.extract_table_content(answer_text, screenshot_path)
                else:
                    print("文本中未检测到表格模式，跳过截图处理")
            
            # 处理和保存结果
            if table_data:
                print("成功提取表格数据")
                
                # 保存提取的表格数据为JSON
                table_json_path = f"tmp/table_data_{timestamp}.json"
                with open(table_json_path, "w", encoding="utf-8") as f:
                    json.dump(table_data, f, ensure_ascii=False, indent=2)
                print(f"表格数据已保存到: {table_json_path}")
                
                # 生成格式化的表格文本
                if "headers" in table_data and "rows" in table_data:
                    headers = table_data["headers"]
                    rows = table_data["rows"]
                    
                    # 计算每列的最大宽度
                    col_widths = [len(str(h)) for h in headers]
                    for row in rows:
                        for i, cell in enumerate(row):
                            if i < len(col_widths):
                                col_widths[i] = max(col_widths[i], len(str(cell)))
                    
                    # 生成表格字符串
                    table_str = []
                    
                    # 添加表头
                    header_row = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers) if i < len(col_widths))
                    table_str.append(header_row)
                    
                    # 添加分隔线
                    separator = "-+-".join("-" * w for w in col_widths)
                    table_str.append(separator)
                    
                    # 添加数据行
                    for row in rows:
                        row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row) if i < len(col_widths))
                        table_str.append(row_str)
                    
                    # 保存格式化的表格文本
                    formatted_table_path = f"yuanbao_table_{timestamp}.txt"
                    with open(formatted_table_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(table_str))
                    print(f"格式化表格已保存到: {formatted_table_path}")
                    
                    # 返回提取的表格数据和路径
                    return {
                        "table_data": table_data,
                        "formatted_table_path": formatted_table_path,
                        "table_json_path": table_json_path
                    }
            
            # 如果没有成功提取表格
            print("未能提取表格数据")
            return None
        
        except Exception as e:
            print(f"处理回答时出错: {e}")
            import traceback
            traceback.print_exc()
            return None


async def main():
    # 创建爬虫实例
    crawler = await YuanbaoPlaywrightCrawler().setup()
    
    # 检查爬虫是否成功初始化
    if crawler is None:
        print("爬虫初始化失败，程序退出")
        return
    
    # 定义问题
    question = "请给我一套BTC日内交易策略，按类似如下格式返回：方向：空/开仓价格：87345/止盈价格：85221/止损价格：88123："
    
    try:
        # 运行爬虫
        await crawler.run(question)
        
        # 任务完成后等待用户手动关闭
        input("任务已完成，按Enter键关闭浏览器...")
    finally:
        await crawler.close()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main()) 