# 贡献指南

感谢您对 **WalletLabel-Bot** 加密钱包标签 Telegram 机器人项目的关注！我们欢迎任何形式的贡献，无论是提交 Bug 报告、提出功能建议，还是直接贡献代码。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
  - [提交 Issue](#提交-issue)
  - [提交 Pull Request](#提交-pull-request)
- [代码规范](#代码规范)
- [代码风格指南](#代码风格指南)
- [开发环境](#开发环境)
- [测试指南](#测试指南)
- [贡献类型](#贡献类型)

## 行为准则

本项目遵循 [Contributor Covenant](.github/CODE_OF_CONDUCT.md) 行为准则。参与项目即表示您同意遵守其条款。

## 如何贡献

### 提交 Issue

如果您发现了 Bug 或有新功能建议，请通过 Issue 告诉我们：

1. **Bug 报告**：请包含以下信息
   - 问题描述（清晰简洁）
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（操作系统、Python 版本、依赖版本等）
   - 错误日志或截图（如适用）
   - 相关的配置参数

2. **功能建议**：请包含以下信息
   - 功能描述
   - 为什么需要这个功能
   - 实现思路（可选）
   - 相关的参考资料（如适用）

### 提交 Pull Request

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

**PR 规范：**
- 标题清晰描述改动内容，使用中文或英文均可
- 详细说明改动的原因和内容
- 关联相关的 Issue（如 `Fixes #123`）
- 确保代码通过所有测试和代码检查
- 更新相关文档（如 README、CHANGELOG）
- 如果添加了新功能，请添加相应的测试用例

## 代码规范

项目使用以下工具进行代码规范管理：

- **Black** - 代码格式化
- **isort** - 导入排序
- **flake8** - 代码检查
- **pytest** - 单元测试

**代码规范：**
- 使用 4 空格缩进
- 变量和函数使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE
- 函数和类需要 docstring 说明（使用 Google 风格）
- 类型注解（Type Hints）是推荐的
- 避免魔法数字，使用常量定义
- 敏感信息（如 API Key）使用环境变量

**运行代码检查：**
```bash
# 格式化代码
black .
isort .

# 代码检查
flake8 .

# 运行测试
python -m pytest test_all.py -v
```

## 代码风格指南

### Git 提交规范

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**提交类型（type）：**
- `feat` - 新功能、新命令
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 代码格式（不影响代码运行）
- `refactor` - 重构（既不是新增功能，也不是修改 bug）
- `perf` - 性能优化
- `test` - 增加测试
- `chore` - 构建过程或辅助工具的变动
- `ci` - CI/CD 配置变更
- `revert` - 回退提交

**示例：**
```
feat(commands): add portfolio analysis command

- Add /portfolio command with detailed holdings analysis
- Implement pie chart visualization for asset allocation
- Add risk assessment scoring
- Update command help documentation

Closes #789
```

**提交规范：**
- 标题不超过 72 个字符
- 使用中文或英文均可，但要保持一致
- 标题使用祈使句（"添加" 而不是 "添加了"）
- 正文详细说明改动的原因和内容
- 关联相关 Issue（如 `Closes #123`、`Fixes #456`）

### 命名约定

```python
# 变量名 - snake_case，描述性命名
wallet_address = "0x..."
user_id = 12345
max_cache_size = 1000

# 函数名 - snake_case，动词开头
def query_wallet_label(address: str) -> dict:
    """查询钱包标签信息"""
    pass

def send_telegram_message(chat_id: int, text: str) -> None:
    """发送 Telegram 消息"""
    pass

# 类名 - PascalCase
class WalletLabelBot:
    """钱包标签机器人"""
    pass

class DatabaseManager:
    """数据库管理器"""
    pass

class LabelService:
    """标签服务"""
    pass

# 常量 - UPPER_SNAKE_CASE
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = "data/wallet_labels.db"
CACHE_TTL = 3600  # 缓存过期时间（秒）
MAX_RETRIES = 3
RATE_LIMIT = 30  # 每分钟请求数限制

# 私有变量/方法 - 下划线前缀
class WalletLabelBot:
    def __init__(self):
        self._db = None
        self._cache = {}
    
    def _validate_address(self, address: str) -> bool:
        """内部地址验证方法"""
        pass
```

#### 文件命名
```
# Python 文件 - snake_case
wallet_bot.py
database.py
label_service.py
__init__.py

# 配置文件 - snake_case
config.yaml
settings.py

# 测试文件 - test_ 前缀
test_wallet_bot.py
test_database.py
```

### 注释规范

#### Docstring（Google 风格）
```python
def analyze_portfolio(address: str, chain: str = "ethereum") -> dict:
    """分析钱包投资组合

    Args:
        address: 钱包地址
        chain: 区块链网络，默认为 ethereum

    Returns:
        包含投资组合信息的字典：
        - total_value: 总价值（USD）
        - holdings: 持仓列表
        - risk_score: 风险评分（0-100）
        - last_updated: 最后更新时间

    Raises:
        ValueError: 地址格式不正确
        APIError: 区块链 API 请求失败

    Example:
        >>> result = analyze_portfolio("0x...", "ethereum")
        >>> print(f"Total: ${result['total_value']:,.2f}")
    """
    pass
```

#### 行内注释
```python
# ✅ 好的注释 - 解释为什么这样做
# 使用 LRU 缓存减少 API 调用，提升查询速度 50%+
@lru_cache(maxsize=1000)
def get_wallet_label(address: str) -> dict:
    pass

# ✅ 好的注释 - 解释安全考虑
# 脱敏处理，只显示地址前6后4位，保护用户隐私
masked_address = f"{address[:6]}...{address[-4:]}"

# ❌ 不好的注释 - 重复代码内容
# 查询数据库
result = db.query(sql)
```

### 导入排序规范

```python
# 1. 标准库
import os
import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime

# 2. 第三方库
import requests
import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler

# 3. 本地库
from wallet_label_bot.database import DatabaseManager
from wallet_label_bot.label_service import LabelService
from wallet_label_bot.utils import format_number, validate_address
from wallet_label_bot.config import Config
```

### 错误处理规范

```python
# ✅ 使用自定义异常
class BotError(Exception):
    """机器人基础异常"""
    pass

class APIError(BotError):
    """API 调用异常"""
    def __init__(self, message: str, status_code: int = 500):
        self.status_code = status_code
        super().__init__(message)

# ✅ 捕获具体异常
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.exceptions.Timeout as e:
    logger.warning(f"API 请求超时: {e}")
    raise APIError("请求超时，请稍后重试", status_code=504)
except requests.exceptions.ConnectionError as e:
    logger.error(f"连接失败: {e}")
    raise APIError("无法连接到服务器", status_code=503)

# ❌ 不要静默异常
try:
    bot.send_message(chat_id, text)
except:  # 太宽泛且静默
    pass
```

### 安全规范

```python
# ✅ 使用环境变量存储敏感信息
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")

# ✅ 输入验证
def validate_eth_address(address: str) -> bool:
    """验证以太坊地址格式"""
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in address[2:])

# ✅ SQL 参数化查询，防止注入
cursor.execute(
    "SELECT * FROM wallets WHERE address = ?",
    (address,)
)
```

## 开发环境

1. **克隆仓库**
   ```bash
   git clone https://github.com/lccuhk/wallet-label-bot.git
   cd wallet-label-bot
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入必要的配置（Telegram Bot Token、RPC 节点等）
   ```

5. **验证安装**
   ```bash
   # 运行测试
   python -m pytest test_all.py -v
   ```

6. **启动机器人**
   ```bash
   python main.py
   ```

## 测试指南

### 运行测试

```bash
# 运行所有测试
python -m pytest test_all.py -v

# 运行特定测试
python -m pytest test_all.py::test_wallet_query -v

# 生成覆盖率报告
python -m pytest test_all.py --cov=. --cov-report=html
```

### 编写测试

- 测试文件放在根目录或 `tests/` 目录下
- 测试函数以 `test_` 开头
- 使用 pytest 框架
- 为新功能添加相应的单元测试
- 确保测试覆盖关键逻辑路径
- 使用 mock 避免实际调用区块链节点

## 贡献类型

我们欢迎各种类型的贡献：

### 🐛 Bug 修复
- 修复机器人响应错误
- 修复钱包查询逻辑错误
- 修复数据库操作问题
- 修复 API 调用问题

### ✨ 新功能
- 添加新的公链支持（Ethereum、BSC、Polygon、Solana 等）
- 添加 NFT 分析功能
- 添加 DeFi 协议追踪
- 添加钱包标签分类系统
- 添加批量查询功能
- 添加导出功能（CSV、JSON 等）
- 添加统计和可视化功能

### 📚 文档
- 改进 README 文档
- 添加使用教程和示例
- 补充代码注释
- 翻译文档
- 添加部署指南

### 🎨 代码质量
- 重构代码以提高可读性
- 优化性能
- 添加类型注解
- 改进测试覆盖率
- 优化数据库查询

### 🔒 安全
- 修复安全漏洞
- 改进敏感信息处理
- 添加安全审计

### 🌐 多语言
- 添加多语言支持
- 翻译机器人回复消息
- 本地化文档

## 问题？

如果您在贡献过程中遇到任何问题，欢迎通过以下方式联系我们：

- 提交 [Issue](https://github.com/lccuhk/wallet-label-bot/issues)
- 查看 [README.md](README.md) 了解更多项目信息
- 查看 [CHANGELOG.md](CHANGELOG.md) 了解版本历史

再次感谢您的贡献！🎉
