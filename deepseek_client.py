#!/usr/bin/env python3
import os
import requests
import json
import base64
from dotenv import load_dotenv
from PIL import Image
import cv2
import numpy as np
import io
import re

# 加载环境变量
load_dotenv()

class DeepSeekClient:
    def __init__(self, api_key=None, config_path="deepseek_config.txt"):
        """初始化DeepSeek API客户端"""
        # 优先使用传入的API密钥，其次尝试从配置文件读取，最后使用环境变量
        self.api_key = api_key or self._read_from_config(config_path) or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("警告: 未找到DeepSeek API密钥，某些功能可能无法正常工作")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def _read_from_config(self, config_path):
        """从配置文件中读取API密钥"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line and line.strip().startswith('DEEPSEEK_API_KEY'):
                            key, value = line.strip().split('=', 1)
                            return value.strip()
            return None
        except Exception as e:
            print(f"读取DeepSeek配置文件失败: {e}")
            return None
    
    def extract_table_from_image(self, image_path):
        """使用DeepSeek API从图像中提取表格内容"""
        try:
            # 读取图像
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 准备API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "deepseek-vision",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "这张图片中包含一个表格，请精确提取表格内容，以下面的格式返回JSON数据：{\"headers\":[列标题], \"rows\":[[行1数据], [行2数据], ...]}。仅返回JSON数据，不要包含任何其他解释文本。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                "temperature": 0
            }
            
            # 发送请求到DeepSeek API
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["choices"][0]["message"]["content"]
                
                # 尝试解析JSON响应
                try:
                    # 提取JSON部分
                    if "```json" in response_text:
                        json_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        json_text = response_text.split("```")[1].strip()
                    else:
                        json_text = response_text
                    
                    # 尝试解析JSON
                    table_data = json.loads(json_text)
                    return table_data
                except json.JSONDecodeError:
                    print(f"无法解析API返回的JSON: {response_text}")
                    return {"error": "JSON解析失败", "raw_response": response_text}
                except Exception as e:
                    print(f"处理API响应时出错: {e}")
                    return {"error": str(e), "raw_response": response_text}
            else:
                print(f"API请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return {"error": f"API请求失败，状态码: {response.status_code}", "details": response.text}
                
        except Exception as e:
            print(f"调用DeepSeek API时出错: {e}")
            return {"error": str(e)}
    
    def process_table_text(self, text):
        """处理文本内容，从中提取表格结构"""
        try:
            # 准备API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": f"以下是一个从网页上复制的表格内容。请提取表格结构，并以JSON格式返回，格式为：{{\"headers\":[列标题], \"rows\":[[行1数据], [行2数据], ...]}}\n\n{text}\n\n仅返回JSON数据，不要包含任何其他解释文本。"
                    }
                ],
                "temperature": 0
            }
            
            # 发送请求到DeepSeek API
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["choices"][0]["message"]["content"]
                
                # 尝试解析JSON响应
                try:
                    # 提取JSON部分
                    if "```json" in response_text:
                        json_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        json_text = response_text.split("```")[1].strip()
                    else:
                        json_text = response_text
                    
                    # 尝试解析JSON
                    table_data = json.loads(json_text)
                    return table_data
                except json.JSONDecodeError:
                    print(f"无法解析API返回的JSON: {response_text}")
                    return {"error": "JSON解析失败", "raw_response": response_text}
                except Exception as e:
                    print(f"处理API响应时出错: {e}")
                    return {"error": str(e), "raw_response": response_text}
            else:
                print(f"API请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return {"error": f"API请求失败，状态码: {response.status_code}", "details": response.text}
                
        except Exception as e:
            print(f"调用DeepSeek API时出错: {e}")
            return {"error": str(e)}
    
    def detect_table_in_image(self, image_path):
        """检测图像中的表格区域并返回裁剪后的表格图像"""
        try:
            # 读取图像
            img = cv2.imread(image_path)
            if img is None:
                return None, "无法读取图像"
            
            # 转换为灰度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 二值化处理
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # 查找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # 找到最大的矩形轮廓（可能是表格）
            max_area = 0
            max_rect = None
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area = w * h
                
                # 过滤掉太小或太大的区域
                if area > max_area and area > (img.shape[0] * img.shape[1]) * 0.05 and area < (img.shape[0] * img.shape[1]) * 0.9:
                    aspect_ratio = float(w) / h
                    # 矩形比例应该合理（不是线条）
                    if 0.2 < aspect_ratio < 5:
                        max_area = area
                        max_rect = (x, y, w, h)
            
            # 如果找到表格区域，裁剪并保存
            if max_rect:
                x, y, w, h = max_rect
                # 稍微扩大区域，确保捕获完整表格
                x = max(0, x - 10)
                y = max(0, y - 10)
                w = min(img.shape[1] - x, w + 20)
                h = min(img.shape[0] - y, h + 20)
                
                # 裁剪表格图像
                table_img = img[y:y+h, x:x+w]
                
                # 转换为PIL图像
                table_img_rgb = cv2.cvtColor(table_img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(table_img_rgb)
                
                # 保存图像到内存
                img_byte_arr = io.BytesIO()
                pil_img.save(img_byte_arr, format='JPEG')
                
                # 保存检测到的表格
                cropped_path = image_path.replace('.png', '_table.png').replace('.jpg', '_table.jpg')
                cv2.imwrite(cropped_path, table_img)
                
                return cropped_path, None
            else:
                return None, "未检测到表格"
                
        except Exception as e:
            print(f"检测表格时出错: {e}")
            return None, str(e)
    
    def format_trading_strategy(self, text, prompt=None):
        """使用DeepSeek API格式化交易策略文本

        Args:
            text (str): 需要格式化的交易策略文本
            prompt (str, optional): 格式化提示。如果不提供，将使用默认提示。

        Returns:
            str: 格式化后的交易策略文本
        """
        try:
            # 默认格式化提示
            if not prompt:
                prompt = """
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
                """.format(text)
            
            # 准备请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 调用DeepSeek API进行格式化
            print("调用DeepSeek API格式化交易策略...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,  # 使用低温度确保准确性
                    "max_tokens": 800
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    # 从回复中提取表格部分
                    # 移除可能的Markdown表格标记和其他说明文本
                    lines = content.strip().split('\n')
                    table_lines = []
                    in_table = False
                    
                    for line in lines:
                        # 移除Markdown代码块标记
                        if line.strip() in ['```', '```markdown', '```table']:
                            in_table = True
                            continue
                        if in_table and line.strip() == '```':
                            break
                        
                        # 检查是否包含表格相关关键词
                        if any(keyword in line for keyword in ['时间', '方向', '开仓', '止盈', '止损', '多', '空']) or \
                           ('|' in line and any(c.isdigit() for c in line)):
                            # 移除行首的数字标记
                            line = re.sub(r'^\d+\.\s+', '', line.strip())
                            table_lines.append(line)
                    
                    if not table_lines and in_table:
                        # 如果没有找到明确的表格行但检测到代码块，使用所有非空行
                        table_lines = [line for line in lines if line.strip() and 
                                      not line.strip().startswith('```')]
                    
                    if not table_lines:
                        # 如果仍然没有找到表格行，使用所有包含关键词的行
                        table_lines = [line for line in lines if any(keyword in line for keyword in 
                                                                  ['时间', '方向', '开仓', '止盈', '止损', '多', '空'])]
                    
                    # 如果找到了表格行
                    if table_lines:
                        formatted_table = '\n'.join(table_lines)
                        print("成功格式化交易策略")
                        return formatted_table
                    
                    # 如果没有找到表格行，返回整个内容
                    print("未找到明确的表格行，返回完整内容")
                    return content
                
                print("API响应中未找到有效内容")
                return None
            else:
                print(f"API请求失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"格式化交易策略时出错: {e}")
            return None 