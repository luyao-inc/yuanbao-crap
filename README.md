# 元宝交易策略自动化系统

一个自动从腾讯元宝AI平台提取比特币交易策略，并能在币安平台自动执行交易的完整系统。

## 功能特点

- 自动登录腾讯元宝AI平台
- 自动发送提示获取BTC日内交易策略
- 自动截图保存AI回答
- 从图像中提取交易策略数据(方向/开仓价/止盈价/止损价)
- 将提取的数据保存到CSV文件
- 自动连接币安API执行交易策略
- 智能设置止盈止损
- 定时执行，无需人工干预

## 系统需求

- Python 3.9+
- Playwright
- DeepSeek API (用于图像分析)
- 币安API账号（用于自动交易）

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/yuanbao-crap.git
cd yuanbao-crap

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

### 元宝爬虫配置
1. 在`prompt.txt`中设置提示词
2. 在`act_time.txt`中设置执行间隔(分钟)

### 币安交易配置
1. 复制`trade_set.txt`文件，并填入您的币安API密钥：
```
投资金额=100
杠杆倍数=2
交易标的=BTCUSDT
保证金模式=逐仓
API_KEY=YOUR_BINANCE_API_KEY_HERE
API_SECRET=YOUR_BINANCE_API_SECRET_HERE
```

## 使用方法

### 自动定时执行（完整流程）

```bash
python yuanbao_scheduler.py
```

这将按照`act_time.txt`中设置的间隔时间(默认15分钟)自动执行策略获取和交易任务。

### 仅执行元宝策略获取

```bash
python yuanbao_trader.py
```

### 仅执行币安交易（基于已有策略）

```bash
python binance_trader.py
```

### 单次执行图像处理

```bash 
python process_image.py <图像路径>
```

## 文件说明

- `yuanbao_scheduler.py` - 主调度程序，负责定时任务执行
- `yuanbao_playwright.py` - 使用Playwright实现浏览器自动化
- `binance_trader.py` - 币安交易API客户端
- `yuanbao_trader.py` - 元宝策略获取模块
- `process_image.py` - 图像处理和数据提取
- `prompt.txt` - 提示词文件，可自定义
- `act_time.txt` - 执行间隔设置文件，单位为分钟
- `trade_set.txt` - 币安交易参数配置
- `outputs.csv` - 输出的策略数据文件

## 输出格式

输出的CSV文件包含以下字段:
- 记录时间 - 策略获取的时间戳
- 方向 - 多/空
- 开仓价 - 建议的开仓价格
- 止盈价 - 建议的止盈价格
- 止损价 - 建议的止损价格

## 安全注意事项

- 请勿将包含API密钥的配置文件上传到公共仓库
- 币安API密钥请设置适当的权限，建议仅开启交易权限
- 首次运行需要登录腾讯元宝平台
- 程序会自动处理Cookie，减少登录频率

## 风险声明

- 本项目仅供学习和研究使用
- 交易有风险，使用自动交易系统前请充分了解相关风险
- 作者不对使用本系统造成的任何损失负责

## 许可证

MIT License 