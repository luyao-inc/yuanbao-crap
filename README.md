# 元宝交易策略提取器

一个自动从腾讯元宝AI平台提取比特币交易策略的工具，定期获取并记录最新的交易策略数据。

## 功能特点

- 自动登录腾讯元宝AI平台
- 自动发送提示获取BTC日内交易策略
- 自动截图保存AI回答
- 从图像中提取交易策略数据(方向/开仓价/止盈价/止损价)
- 将提取的数据保存到CSV文件
- 智能去重，避免记录重复的策略
- 定时执行，无需人工干预

## 系统需求

- Python 3.9+
- Playwright
- DeepSeek API (用于图像分析)

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/yuanbao-btc-strategy.git
cd yuanbao-btc-strategy

# 创建虚拟环境
python -m venv yuanbao_env
source yuanbao_env/bin/activate  # Linux/Mac
# 或 yuanbao_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
python -m playwright install
```

## 配置

1. 在`prompt.txt`中设置提示词
2. 在`act_time.txt`中设置执行间隔(分钟)

## 使用方法

### 自动定时执行

```bash
python yuanbao_scheduler.py
```

这将按照`act_time.txt`中设置的间隔时间(默认15分钟)自动执行策略获取任务。

### 单次执行图像处理

```bash 
python process_image.py <图像路径>
```

## 文件说明

- `yuanbao_scheduler.py` - 主调度程序，负责定时任务执行
- `yuanbao_playwright.py` - 使用Playwright实现浏览器自动化
- `process_image.py` - 图像处理和数据提取
- `prompt.txt` - 提示词文件，可自定义
- `act_time.txt` - 执行间隔设置文件，单位为分钟
- `outputs.csv` - 输出的策略数据文件

## 输出格式

输出的CSV文件包含以下字段:
- 记录时间 - 策略获取的时间戳
- 方向 - 多/空
- 开仓价 - 建议的开仓价格
- 止盈价 - 建议的止盈价格
- 止损价 - 建议的止损价格

## 注意事项

- 请确保网络连接稳定
- 首次运行需要登录腾讯元宝平台
- 程序会自动处理Cookie，减少登录频率

## 许可证

MIT License 