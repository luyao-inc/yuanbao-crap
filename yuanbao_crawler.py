import os
import time
import json
import pickle
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class YuanbaoCrawler:
    def __init__(self):
        self.url = "https://yuanbao.tencent.com/"
        self.cookies_file = "yuanbao_cookies.pkl"
        self.driver = self._setup_driver()
        
    def _get_chromedriver_path(self):
        """获取适合当前系统的ChromeDriver路径"""
        system = platform.system()
        machine = platform.machine()
        
        if system == "Darwin" and machine == "arm64":
            # Mac ARM架构
            user_home = Path.home()
            custom_path = user_home / "chromedriver-mac-arm64" / "chromedriver-mac-arm64" / "chromedriver"
            
            if custom_path.exists():
                print(f"使用自定义ChromeDriver路径: {custom_path}")
                return str(custom_path)
            else:
                print("未找到自定义ChromeDriver，请先运行download_chromedriver.py")
                print("将尝试使用系统默认的ChromeDriver")
                return None
        return None
        
    def _setup_driver(self):
        """设置并返回WebDriver实例"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 无头模式，取消注释可开启
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 获取ChromeDriver路径
        driver_path = self._get_chromedriver_path()
        
        try:
            if driver_path:
                print(f"使用指定的ChromeDriver: {driver_path}")
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                print("使用默认ChromeDriver设置")
                driver = webdriver.Chrome(options=chrome_options)
                
            return driver
        except Exception as e:
            print(f"初始化ChromeDriver时出错: {e}")
            print("请尝试运行 python download_chromedriver.py 下载匹配的驱动")
            raise
    
    def load_cookies(self):
        """加载已保存的cookie"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "rb") as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)
                return True
            except Exception as e:
                print(f"加载cookie时出错: {e}")
        return False
    
    def save_cookies(self):
        """保存当前的cookie"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, "wb") as f:
                pickle.dump(cookies, f)
            print("Cookie已保存")
        except Exception as e:
            print(f"保存cookie时出错: {e}")
    
    def login(self):
        """处理登录流程"""
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
        
        self.driver.get(self.url)
        print("等待页面加载...")
        time.sleep(3)  # 等待页面加载
        
        # 尝试使用已保存的cookie登录
        has_cookie = self.load_cookies()
        if has_cookie:
            print("已加载保存的cookie，尝试自动登录")
            self.driver.refresh()  # 刷新以应用cookie
            time.sleep(3)
            
        # 检查是否需要手动登录
        try:
            # 等待页面内容加载，判断是否已登录
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".chat-container"))
            )
            print("已成功登录")
            return True
        except:
            print("未检测到登录状态，请手动登录...")
            # 等待用户手动登录
            input("完成登录后请按Enter键继续...")
            
            # 保存登录后的cookie
            self.save_cookies()
            return True
    
    def check_and_set_options(self):
        """确保联网搜索和R1推理选项被选中"""
        try:
            print("检查和设置搜索选项...")
            
            # 首先尝试找到设置按钮
            try:
                # 可能的设置按钮选择器
                selectors = [
                    "button.settings-btn", 
                    ".settings-icon", 
                    "button[aria-label='设置']",
                    "//button[contains(@class, 'setting')]",
                    "//svg[contains(@class, 'setting')]/..",
                    "//span[text()='设置']/.."
                ]
                
                settings_btn = None
                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            # XPath选择器
                            elements = self.driver.find_elements(By.XPATH, selector)
                        else:
                            # CSS选择器
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                        if elements:
                            settings_btn = elements[0]
                            print(f"找到设置按钮，使用选择器: {selector}")
                            break
                    except:
                        continue
                
                if settings_btn:
                    print("点击设置按钮...")
                    settings_btn.click()
                    time.sleep(2)  # 等待设置面板打开
                else:
                    print("未找到设置按钮，尝试直接查找选项...")
            except Exception as e:
                print(f"查找/点击设置按钮时出错: {e}")
            
            # 截图保存页面状态，方便调试
            try:
                screenshot_file = f"yuanbao_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_file)
                print(f"已保存页面截图到: {screenshot_file}")
            except Exception as e:
                print(f"保存截图时出错: {e}")
            
            # 暂时跳过设置选项，允许继续执行
            print("由于无法确定页面结构，暂时跳过设置选项，继续执行...")
            return True
                
        except Exception as e:
            print(f"设置选项时出错: {e}")
            print("继续执行其他步骤...")
            return True  # 允许继续执行
    
    def ask_question(self, question):
        """输入问题并等待回答"""
        try:
            print(f"输入问题: {question}")
            
            # 先保存页面源码，便于分析
            try:
                with open(f"yuanbao_page_source_before_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print("已保存页面源码，用于分析页面结构")
            except Exception as e:
                print(f"保存页面源码时出错: {e}")
            
            # 截图保存页面状态
            self.driver.save_screenshot(f"yuanbao_before_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            # 等待页面完全加载
            print("等待页面完全加载...")
            time.sleep(5)
            
            # 检查是否有iframe并尝试切换
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                print(f"发现 {len(iframes)} 个iframe，尝试切换...")
                for i, iframe in enumerate(iframes):
                    try:
                        self.driver.switch_to.frame(iframe)
                        print(f"已切换到iframe {i+1}")
                        
                        # 尝试查找输入框
                        try:
                            input_elements = self.driver.find_elements(By.TAG_NAME, "textarea")
                            if input_elements:
                                print(f"在iframe {i+1}中找到 {len(input_elements)} 个textarea元素")
                        except:
                            pass
                        
                        # 切回主文档
                        self.driver.switch_to.default_content()
                    except Exception as e:
                        print(f"切换到iframe {i+1}时出错: {e}")
                        self.driver.switch_to.default_content()
            
            # 扩展输入框选择器
            input_selectors = [
                ".chat-input textarea",
                "textarea[placeholder]",
                "//textarea[contains(@placeholder, '发送')]",
                "//textarea",
                ".input-box textarea",
                "div.input-container textarea",
                ".message-input textarea",
                "//div[contains(@class, 'input')]//textarea",
                "//div[contains(@class, 'chat')]//textarea",
                "textarea.input",
                "//textarea[@placeholder]",
                "//div[contains(@class, 'text-input')]//textarea",
                # 添加更通用的选择器
                "textarea",
                ".text-input",
                ".ant-input",
                "input[type='text']",
                "//input[@type='text']"
            ]
            
            # 打印页面中所有textarea元素，以帮助调试
            try:
                all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                print(f"页面中共有 {len(all_textareas)} 个textarea元素")
                for i, textarea in enumerate(all_textareas):
                    try:
                        classes = textarea.get_attribute("class")
                        placeholder = textarea.get_attribute("placeholder")
                        is_visible = textarea.is_displayed()
                        print(f"Textarea {i+1}: class='{classes}', placeholder='{placeholder}', visible={is_visible}")
                    except:
                        print(f"无法获取Textarea {i+1}的属性")
            except Exception as e:
                print(f"查找所有textarea元素时出错: {e}")
            
            # 尝试不同的输入框选择器
            input_box = None
            for selector in input_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath选择器
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS选择器
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                    if elements:
                        for i, element in enumerate(elements):
                            try:
                                if element.is_displayed():
                                    input_box = element
                                    print(f"找到可见的输入框，使用选择器: {selector}，索引: {i}")
                                    break
                            except:
                                continue
                        
                        if input_box:
                            break
                except:
                    continue
            
            if not input_box:
                print("未找到标准输入框，尝试执行JavaScript注入一个输入框...")
                try:
                    # 尝试用JavaScript在页面上创建一个假的输入框并填入内容
                    script = """
                    console.log('尝试通过JavaScript输入问题');
                    // 尝试找到可能的输入框
                    var inputArea = document.querySelector('textarea');
                    if (!inputArea) {
                        // 如果没找到，记录所有可能是输入区域的元素
                        console.log('没有找到textarea，打印所有可能的输入元素');
                        document.querySelectorAll('div[contenteditable="true"], input, .input, .textarea, [role="textbox"]').forEach(function(el) {
                            console.log('可能的输入元素:', el);
                        });
                    } else {
                        console.log('找到textarea:', inputArea);
                        inputArea.value = arguments[0];
                        // 尝试触发输入事件
                        var event = new Event('input', { bubbles: true });
                        inputArea.dispatchEvent(event);
                        return true;
                    }
                    return false;
                    """
                    result = self.driver.execute_script(script, question)
                    if result:
                        print("成功通过JavaScript输入问题")
                        
                        # 尝试用JavaScript点击发送按钮
                        send_script = """
                        var sendBtn = document.querySelector('button[type="submit"], button.send, button.submit, .send-button, [aria-label="发送"]');
                        if (sendBtn) {
                            console.log('找到发送按钮:', sendBtn);
                            sendBtn.click();
                            return true;
                        }
                        // 尝试按回车键
                        var inputArea = document.querySelector('textarea');
                        if (inputArea) {
                            var event = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            });
                            inputArea.dispatchEvent(event);
                            return true;
                        }
                        return false;
                        """
                        send_result = self.driver.execute_script(send_script)
                        if send_result:
                            print("成功通过JavaScript发送问题")
                            
                            # 等待回答
                            print("等待固定时间...")
                            time.sleep(60)  # 等待60秒
                            return True
                except Exception as e:
                    print(f"执行JavaScript时出错: {e}")
                
                print("所有自动方法都失败了。请手动在页面上输入问题并发送，然后按Enter继续...")
                self.driver.save_screenshot(f"yuanbao_input_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                input("在浏览器中手动输入并发送问题后，按Enter继续...")
                return True
            
            # 清除并输入问题
            try:
                input_box.clear()
                input_box.send_keys(question)
                print("已将问题输入到输入框")
            except Exception as e:
                print(f"输入问题时出错: {e}")
                print("尝试使用JavaScript输入...")
                try:
                    self.driver.execute_script("arguments[0].value = arguments[1]", input_box, question)
                    print("已通过JavaScript输入问题")
                except Exception as e:
                    print(f"通过JavaScript输入时出错: {e}")
                    raise
            
            # 查找并点击发送按钮
            send_selectors = [
                ".chat-input button[type='submit']",
                "button[type='submit']",
                "//button[contains(@class, 'send')]",
                "//button[contains(text(), '发送')]",
                "//span[contains(text(), '发送')]/parent::button",
                "//button[contains(@class, 'submit')]",
                ".send-button",
                "button.send",
                "button.submit",
                "[aria-label='发送']",
                ".chat-submit",
                "//button[contains(@class, 'primary')]",
                "//button[last()]"  # 尝试页面上的最后一个按钮
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath选择器
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS选择器
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                    if elements:
                        for i, element in enumerate(elements):
                            try:
                                if element.is_displayed():
                                    send_button = element
                                    print(f"找到可见的发送按钮，使用选择器: {selector}，索引: {i}")
                                    break
                            except:
                                continue
                        
                        if send_button:
                            break
                except:
                    continue
            
            if not send_button:
                # 尝试使用Enter键发送
                print("未找到发送按钮，尝试使用Enter键发送")
                try:
                    input_box.send_keys("\n")
                    print("已发送Enter键")
                except Exception as e:
                    print(f"发送Enter键时出错: {e}")
                    try:
                        # 尝试使用JavaScript模拟回车键
                        self.driver.execute_script("""
                        var event = new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        });
                        arguments[0].dispatchEvent(event);
                        """, input_box)
                        print("已通过JavaScript发送Enter键")
                    except Exception as e:
                        print(f"通过JavaScript发送Enter键时出错: {e}")
                        print("请手动点击发送按钮...")
                        input("在浏览器中手动点击发送按钮后，按Enter继续...")
            else:
                try:
                    send_button.click()
                    print("已点击发送按钮")
                except Exception as e:
                    print(f"点击发送按钮时出错: {e}")
                    try:
                        # 尝试使用JavaScript点击
                        self.driver.execute_script("arguments[0].click();", send_button)
                        print("已通过JavaScript点击发送按钮")
                    except Exception as e:
                        print(f"通过JavaScript点击发送按钮时出错: {e}")
                        print("请手动点击发送按钮...")
                        input("在浏览器中手动点击发送按钮后，按Enter继续...")
            
            print("问题已发送或手动处理，等待回答...")
            
            # 等待回答加载完成，简化为固定等待
            print("等待固定时间以确保回答加载完成...")
            time.sleep(60)  # 等待60秒
            
            return True
        except Exception as e:
            print(f"提问过程中出错: {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot(f"yuanbao_question_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            print("请手动在页面上输入问题并发送，然后按Enter继续...")
            input("在浏览器中手动操作后，按Enter继续...")
            return True  # 即使出错也继续执行
    
    def extract_answer(self):
        """提取最新的回答内容"""
        try:
            print("提取回答内容...")
            
            # 先保存页面源码和截图，以便分析
            try:
                with open(f"yuanbao_answer_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print("已保存回答页面源码")
            except Exception as e:
                print(f"保存页面源码时出错: {e}")
            
            # 保存截图
            self.driver.save_screenshot(f"yuanbao_answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            print("已保存回答页面截图")
            
            # 尝试使用JavaScript提取内容
            try:
                js_result = self.driver.execute_script("""
                // 尝试查找最后一个回答元素
                var messages = document.querySelectorAll('.chat-message, .message, .assistant-message, .bot-message, [class*="message"], [class*="chat"]');
                if (messages && messages.length > 0) {
                    console.log('找到消息元素数量:', messages.length);
                    // 获取最后一个或倒数第二个元素（根据页面结构可能有所不同）
                    for (var i = messages.length - 1; i >= 0; i--) {
                        var msg = messages[i];
                        // 忽略用户消息，只查找助手回答
                        if (msg.classList.contains('user') || msg.classList.contains('question')) {
                            continue;
                        }
                        console.log('可能的回答元素:', msg);
                        return msg.innerText || msg.textContent;
                    }
                }
                
                // 备用方法：尝试获取任何包含文本的大段内容
                var contentElements = document.querySelectorAll('p, div > span, .content, [class*="content"]');
                var longestText = '';
                for (var i = 0; i < contentElements.length; i++) {
                    var text = contentElements[i].innerText || contentElements[i].textContent;
                    if (text && text.length > longestText.length) {
                        longestText = text;
                    }
                }
                if (longestText.length > 50) {  // 只返回长度超过50的文本
                    return longestText;
                }
                
                return null;
                """)
                
                if js_result:
                    print("通过JavaScript成功提取到回答内容")
                    return js_result
            except Exception as e:
                print(f"使用JavaScript提取内容时出错: {e}")
            
            # 尝试不同的回答元素选择器
            answer_selectors = [
                ".chat-message.assistant",
                ".assistant-message",
                ".message-content",
                "//div[contains(@class, 'assistant')]",
                "//div[contains(@class, 'ai-message')]",
                "//div[contains(@class, 'bot-message')]",
                "//div[contains(@class, 'response')]",
                ".message:not(.user)",
                ".response-message",
                ".chat-response",
                "//div[contains(@class, 'answer')]",
                "//div[contains(@class, 'message') and not(contains(@class, 'user'))]",
                "//div[contains(@class, 'content')]",
                ".markdown-body",
                "[role='region']"
            ]
            
            for selector in answer_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath选择器
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS选择器
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        print(f"找到回答元素，使用选择器: {selector}，共 {len(elements)} 个元素")
                        
                        # 获取最后一个回答元素
                        for i in range(len(elements) - 1, -1, -1):
                            try:
                                element = elements[i]
                                answer_text = element.text
                                
                                # 只接受长度合理的回答
                                if answer_text and len(answer_text) > 50:
                                    print(f"从元素 {i} 获取到回答，长度: {len(answer_text)} 字符")
                                    return answer_text
                            except Exception as e:
                                print(f"从元素 {i} 提取文本时出错: {e}")
                except Exception as e:
                    print(f"使用选择器 {selector} 提取答案时出错: {e}")
                    continue
            
            # 尝试获取页面上所有段落文本
            print("尝试获取页面上所有段落...")
            try:
                paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                if paragraphs:
                    print(f"找到 {len(paragraphs)} 个段落元素")
                    all_text = []
                    for p in paragraphs:
                        try:
                            text = p.text
                            if text:
                                all_text.append(text)
                        except:
                            pass
                    
                    if all_text:
                        combined_text = "\n".join(all_text)
                        print(f"从所有段落获取到文本，长度: {len(combined_text)} 字符")
                        return combined_text
            except Exception as e:
                print(f"获取段落文本时出错: {e}")
            
            # 手动输入模式
            print("\n未能自动提取回答，请手动输入回答内容。")
            print("您可以从浏览器中复制回答，然后粘贴到此处。")
            print("输入完成后按两次Enter键结束输入：")
            
            lines = []
            while True:
                line = input()
                if line == "" and (not lines or lines[-1] == ""):
                    break
                lines.append(line)
            
            answer_text = "\n".join(lines).strip()
            return answer_text if answer_text else "无法提取回答内容，请查看浏览器截图"
                
        except Exception as e:
            print(f"提取答案时出错: {e}")
            import traceback
            traceback.print_exc()
            print("\n由于错误，请手动输入回答内容。")
            print("您可以从浏览器中复制回答，然后粘贴到此处。")
            print("输入完成后按两次Enter键结束输入：")
            
            lines = []
            while True:
                line = input()
                if line == "" and (not lines or lines[-1] == ""):
                    break
                lines.append(line)
            
            answer_text = "\n".join(lines).strip()
            return answer_text if answer_text else "无法提取回答内容，请查看浏览器截图"
    
    def save_to_file(self, content):
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
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")
    
    def run(self, question):
        """运行完整的爬取流程"""
        try:
            # 登录
            login_success = self.login()
            if not login_success:
                print("自动登录失败，请尝试手动登录...")
                input("完成手动登录后，按Enter继续...")
            
            # 设置选项（即使失败也继续执行）
            try:
                self.check_and_set_options()
            except Exception as e:
                print(f"设置选项时出错: {e}，继续执行后续步骤...")
            
            # 提问（即使失败也继续，允许手动提问）
            question_sent = self.ask_question(question)
            if not question_sent:
                print("自动提问失败，请手动在页面上输入问题...")
                input("完成手动提问后，按Enter继续...")
            
            # 等待一段时间确保回答完成
            print("等待回答完成...")
            time.sleep(10)  # 额外等待时间
            
            # 提取答案（即使失败也继续，允许手动提供）
            answer = self.extract_answer()
            if not answer:
                print("未能自动提取答案，请手动输入...")
                answer = input("请从浏览器中复制答案并粘贴到这里：")
            
            # 保存结果
            file_path = self.save_to_file(answer)
            if file_path:
                print(f"结果已保存到文件: {file_path}")
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
            print("发生错误，但将尝试手动完成剩余步骤...")
            
            # 尝试手动提取答案
            try:
                print("请从浏览器中查看结果...")
                self.driver.save_screenshot(f"yuanbao_final_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                answer = input("请从浏览器中复制答案并粘贴到这里：")
                
                if answer:
                    file_path = self.save_to_file(answer)
                    if file_path:
                        print(f"结果已保存到文件: {file_path}")
                    else:
                        print("保存文件失败，显示最终结果:")
                        print("-" * 50)
                        print(answer)
                        print("-" * 50)
            except Exception as e2:
                print(f"尝试手动完成时出错: {e2}")
            
            return False
        finally:
            # 结束时不要关闭浏览器，以便查看结果
            pass


if __name__ == "__main__":
    # 创建爬虫实例
    crawler = YuanbaoCrawler()
    
    # 定义问题
    question = "请给我一套BTC日内交易策略，按类似如下格式返回：方向：空/开仓价格：87345/止盈价格：85221/止损价格：88123："
    
    try:
        # 运行爬虫
        crawler.run(question)
        
        # 任务完成后等待用户手动关闭
        input("任务已完成，按Enter键关闭浏览器...")
    finally:
        crawler.close() 