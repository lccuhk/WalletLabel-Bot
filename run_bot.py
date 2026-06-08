#!/usr/bin/env python3
"""
WalletLabel Bot - 钱包地址标签查询机器人
主运行文件
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from config import settings
from models import init_db
from bot import (
    start_command,
    help_command,
    check_command,
    analyze_command,
    risk_command,
    batch_command,
    subscribe_command,
    profile_command,
    invite_command,
    use_invite_command,
    handle_message,
    handle_callback,
    handle_start_with_invite,
)


def setup_logging():
    """配置日志"""
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # 文件输出
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "bot_{time:YYYY-MM-DD}.log",
        level=settings.LOG_LEVEL,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info("Logging setup completed")


async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """包装start命令，处理邀请码"""
    # 检查是否有邀请码参数
    if context.args:
        invite_result = await handle_start_with_invite(update, context)
        if invite_result:
            # 有邀请码，先显示邀请成功消息，再显示欢迎消息
            await update.message.reply_text(
                invite_result,
                parse_mode="Markdown",
            )

    # 调用原始start命令
    await start_command(update, context)


def main():
    """主函数"""
    setup_logging()

    logger.info("=" * 60)
    logger.info("WalletLabel Bot 启动中...")
    logger.info("=" * 60)

    # 检查Bot Token
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("未配置 TELEGRAM_BOT_TOKEN，请在 .env 文件中配置")
        logger.error("复制 .env.example 为 .env 并填写配置")
        sys.exit(1)

    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)

    # 创建Bot应用
    try:
        application = ApplicationBuilder() \
            .token(settings.TELEGRAM_BOT_TOKEN) \
            .connect_timeout(30) \
            .read_timeout(30) \
            .write_timeout(30) \
            .build()

        logger.info("Bot应用创建成功")
    except Exception as e:
        logger.error(f"Bot应用创建失败: {e}")
        sys.exit(1)

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start_wrapper))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("risk", risk_command))
    application.add_handler(CommandHandler("batch", batch_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("invite", invite_command))
    application.add_handler(CommandHandler("use_invite", use_invite_command))

    # 注册回调处理器
    application.add_handler(CallbackQueryHandler(handle_callback))

    # 注册普通消息处理器（处理直接发送的地址）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 注册错误处理器
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理错误"""
        logger.error(f"Update {update} caused error {context.error}")

        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ 发生错误，请稍后重试或联系客服。",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    application.add_error_handler(error_handler)

    # 启动Bot
    logger.info("=" * 60)
    logger.info("WalletLabel Bot 启动成功！")
    logger.info("=" * 60)
    logger.info(f"管理员ID: {settings.TELEGRAM_ADMIN_ID if settings.TELEGRAM_ADMIN_ID else '未设置'}")
    logger.info(f"免费用户每日限制: {settings.FREE_DAILY_LIMIT} 次查询")
    logger.info(f"月卡价格: ¥{settings.PRICE_MONTHLY}")
    logger.info(f"年卡价格: ¥{settings.PRICE_YEARLY}")
    logger.info(f"专业版价格: ¥{settings.PRICE_PRO}/月")
    logger.info("=" * 60)
    logger.info("按 Ctrl+C 停止Bot")
    logger.info("=" * 60)

    # 运行Bot
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nBot 已停止")
    except Exception as e:
        logger.error(f"Bot 运行出错: {e}")
        sys.exit(1)
