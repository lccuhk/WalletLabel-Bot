# WalletLabel Bot 部署指南

## 📋 目录
- [快速开始](#快速开始)
- [Replit 零成本部署](#replit-零成本部署)
- [VPS 部署](#vps-部署)
- [Docker 部署](#docker-部署)
- [环境变量配置](#环境变量配置)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 前置准备

1. **创建 Telegram Bot**
   - 打开 Telegram，搜索 [@BotFather](https://t.me/BotFather)
   - 发送 `/newbot` 命令
   - 按照提示设置 Bot 名称和用户名
   - 保存获取到的 Bot Token

2. **获取 API Key（可选）**
   - Etherscan API Key: https://etherscan.io/apis
   - BscScan API Key: https://bscscan.com/apis
   - PolygonScan API Key: https://polygonscan.com/apis

### 2. 本地运行

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd wallet-label-bot

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 4. 运行测试
python3 test_all.py

# 5. 启动 Bot
python3 run_bot.py
```

---

## 🌐 Replit 零成本部署（推荐）

Replit 提供免费的云服务，适合零成本启动项目。

### 步骤 1: 导入项目到 Replit

1. 访问 [Replit.com](https://replit.com) 并注册账号
2. 点击 "Create Repl"
3. 选择 "Import from GitHub"
4. 输入你的 GitHub 仓库地址
5. 选择语言为 "Python"
6. 点击 "Import"

### 步骤 2: 配置环境变量

1. 在 Replit 项目中，点击左侧的 "Secrets" 选项（锁图标）
2. 添加以下环境变量：

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | 你的 Telegram Bot Token | ✅ |
| `TELEGRAM_ADMIN_ID` | 你的 Telegram 用户 ID | ❌ |
| `USDT_TRC20_ADDRESS` | USDT 收款地址（TRC20） | ❌ |
| `ETHERSCAN_API_KEY` | Etherscan API Key | ❌ |
| `BSCSCAN_API_KEY` | BscScan API Key | ❌ |
| `POLYGONSCAN_API_KEY` | PolygonScan API Key | ❌ |
| `FREE_DAILY_LIMIT` | 免费用户每日查询次数 | ❌ |
| `PRICE_MONTHLY` | 月卡价格（元） | ❌ |
| `PRICE_YEARLY` | 年卡价格（元） | ❌ |
| `PRICE_PRO` | 专业版价格（元/月） | ❌ |

### 步骤 3: 配置运行命令

1. 点击 Replit 顶部的 "Run" 按钮旁边的配置按钮
2. 设置 "Run command" 为：
   ```bash
   python run_bot.py
   ```

### 步骤 4: 启动 Bot

1. 点击 "Run" 按钮
2. 等待依赖安装完成
3. Bot 启动成功后，在 Telegram 中搜索你的 Bot 并发送 `/start`

### 步骤 5: 保持 Bot 在线（可选）

Replit 免费版会在一段时间无活动后休眠。可以使用以下方法保持在线：

**方法 1: 使用 UptimeRobot**
1. 注册 [UptimeRobot](https://uptimerobot.com)
2. 添加新的监控，选择 "HTTP(s)"
3. 填入你的 Replit 项目 URL（格式：`https://<project-name>.<username>.repl.co`）
4. 设置监控间隔为 5 分钟

**方法 2: 添加简单的 Web 服务器**

在项目中添加 `keep_alive.py`：
```python
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "WalletLabel Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
```

然后在 `run_bot.py` 开头添加：
```python
from keep_alive import keep_alive
keep_alive()
```

---

## 💻 VPS 部署

适合有一定技术基础的用户，稳定性更高。

### 系统要求
- Linux 系统（推荐 Ubuntu 20.04+）
- Python 3.8+
- 至少 1GB 内存
- 至少 10GB 硬盘空间

### 部署步骤

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 Python 和 pip
sudo apt install python3 python3-pip python3-venv -y

# 3. 克隆项目
git clone <your-repo-url>
cd wallet-label-bot

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 配置环境变量
cp .env.example .env
nano .env  # 填入你的配置

# 7. 运行测试
python test_all.py

# 8. 使用 systemd 管理服务
sudo nano /etc/systemd/system/wallet-label-bot.service
```

添加以下内容：
```ini
[Unit]
Description=WalletLabel Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/wallet-label-bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/path/to/wallet-label-bot/venv/bin/python run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 9. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable wallet-label-bot
sudo systemctl start wallet-label-bot

# 10. 查看状态
sudo systemctl status wallet-label-bot

# 11. 查看日志
journalctl -u wallet-label-bot -f
```

---

## 🐳 Docker 部署

### 1. 创建 Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建数据目录
RUN mkdir -p data logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "run_bot.py"]
```

### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  wallet-label-bot:
    build: .
    container_name: wallet-label-bot
    restart: always
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - TELEGRAM_BOT_TOKEN=your_bot_token
      - TELEGRAM_ADMIN_ID=your_admin_id
      - USDT_TRC20_ADDRESS=your_usdt_address
      - ETHERSCAN_API_KEY=your_etherscan_key
      - BSCSCAN_API_KEY=your_bscscan_key
      - POLYGONSCAN_API_KEY=your_polygonscan_key
      - FREE_DAILY_LIMIT=3
      - PRICE_MONTHLY=19.9
      - PRICE_YEARLY=199
      - PRICE_PRO=99
```

### 3. 启动容器

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose stop

# 重启
docker-compose restart
```

---

## 🔧 环境变量配置

完整的 `.env` 配置文件：

```env
# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_ID=123456789

# 数据库配置（默认 SQLite，无需修改）
DATABASE_URL=sqlite:///./data/wallet_bot.db

# 区块链 API Key（可选，提高查询准确性）
ETHERSCAN_API_KEY=your_etherscan_api_key
BSCSCAN_API_KEY=your_bscscan_api_key
POLYGONSCAN_API_KEY=your_polygonscan_api_key

# 免费用户配置
FREE_DAILY_LIMIT=3

# 会员价格配置（单位：元）
PRICE_MONTHLY=19.9
PRICE_YEARLY=199
PRICE_PRO=99

# 收款配置
USDT_TRC20_ADDRESS=your_usdt_trc20_address

# 系统配置
TIMEZONE=Asia/Shanghai
LOG_LEVEL=INFO
```

---

## ❓ 常见问题

### Q1: Bot 启动后没有响应？

**A:** 检查以下几点：
1. Bot Token 是否正确
2. 网络连接是否正常
3. 查看日志文件 `logs/bot_*.log`
4. 确保没有其他程序使用相同的 Token

### Q2: 如何获取我的 Telegram 用户 ID？

**A:** 
1. 在 Telegram 中搜索 [@userinfobot](https://t.me/userinfobot)
2. 发送 `/start`
3. 机器人会返回你的用户 ID

### Q3: 免费版 API Key 不够用怎么办？

**A:** 
1. 可以注册多个账号，使用多个 API Key
2. 升级到付费版 API
3. 本项目内置了本地标签数据库，即使没有 API Key 也能正常工作

### Q4: 如何修改会员价格？

**A:** 修改 `.env` 文件中的价格配置，然后重启 Bot。

### Q5: 如何备份数据？

**A:** 定期备份 `data/` 目录下的数据库文件。

```bash
# 创建备份
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# 恢复备份
tar -xzf backup_20240101.tar.gz
```

### Q6: 如何更新 Bot？

**A:**

```bash
# 1. 停止 Bot
sudo systemctl stop wallet-label-bot

# 2. 拉取最新代码
git pull

# 3. 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 4. 运行测试
python test_all.py

# 5. 启动 Bot
sudo systemctl start wallet-label-bot
```

### Q7: Bot 被限制或封禁怎么办？

**A:**
1. 检查 Bot 是否发送了违规内容
2. 联系 Telegram 客服申诉
3. 如有必要，创建新的 Bot 并迁移数据

### Q8: 如何添加更多地址标签？

**A:** 编辑 `core/label_engine.py` 中的 `_get_exchange_labels()` 和 `_get_known_addresses()` 方法，添加更多地址。

---

## 📞 技术支持

如有部署问题，可以：
1. 查看日志文件 `logs/bot_*.log`
2. 运行测试脚本 `python test_all.py` 排查问题
3. 提交 Issue 到项目仓库
