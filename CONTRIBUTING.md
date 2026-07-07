# 贡献指南

感谢您对 **WalletLabel-Bot** 加密钱包标签 Telegram 机器人项目的关注！我们欢迎任何形式的贡献，无论是提交 Bug 报告、提出功能建议，还是直接贡献代码。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
  - [提交 Issue](#提交-issue)
  - [提交 Pull Request](#提交-pull-request)
- [代码规范](#代码规范)
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
