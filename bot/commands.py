"""
Bot 命令处理模块
"""

import re
from typing import Optional, Tuple
from datetime import datetime
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import settings
from models import get_db_context, User, UserTier, QueryHistory, generate_invite_code
from core import label_engine, analysis_engine, risk_engine, blockchain_api
from .utils import (
    format_label_message,
    format_analysis_message,
    format_risk_message,
    format_profile_message,
    format_subscribe_message,
    format_batch_result,
)


def get_or_create_user(update: Update) -> User:
    """获取或创建用户"""
    telegram_user = update.effective_user
    if not telegram_user:
        raise ValueError("无法获取用户信息")

    with get_db_context() as db:
        user = db.query(User).filter(User.telegram_id == telegram_user.id).first()

        if not user:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                invite_code=generate_invite_code(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user created: {telegram_user.id} (@{telegram_user.username})")

        # 更新用户信息
        if user.username != telegram_user.username:
            user.username = telegram_user.username
        if user.first_name != telegram_user.first_name:
            user.first_name = telegram_user.first_name
        if user.last_name != telegram_user.last_name:
            user.last_name = telegram_user.last_name
        if user.language_code != telegram_user.language_code:
            user.language_code = telegram_user.language_code

        db.commit()
        db.refresh(user)

        return user


def validate_address(address: str) -> Tuple[bool, Optional[str]]:
    """验证地址格式"""
    address = address.strip()
    patterns = settings.address_patterns

    for chain, pattern in patterns.items():
        if re.match(pattern, address):
            return True, chain

    return False, None


def record_query(user_id: int, address: str, query_type: str, result_summary: str = ""):
    """记录查询历史"""
    try:
        with get_db_context() as db:
            history = QueryHistory(
                user_id=user_id,
                address=address,
                query_type=query_type,
                result_summary=result_summary,
            )
            db.add(history)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to record query: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始命令"""
    user = get_or_create_user(update)

    welcome_text = f"""
👋 欢迎使用 **WalletLabel Bot** - 钱包地址标签查询机器人

我可以帮你：
🏷️ 查询钱包地址的身份标签（交易所、鲸鱼、黑客等）
📊 分析地址的持仓和交易行为
⚠️ 评估地址的风险等级
🔍 批量查询多个地址

{'=' * 40}

📝 **使用方法**：
直接发送钱包地址即可查询
或使用以下命令：

/check [地址] - 查询地址标签
/analyze [地址] - 深度分析（会员）
/risk [地址] - 风险评级
/batch [地址1] [地址2] ... - 批量查询（年卡+）
/profile - 个人中心
/subscribe - 升级会员
/invite - 邀请好友
/help - 帮助

{'=' * 40}

🎁 **新用户福利**：
前100名用户免费升级月卡7天！
邀请好友注册，双方各得7天会员！

现在发送一个地址试试吧！
"""

    await update.message.reply_text(
        welcome_text.strip(),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """帮助命令"""
    help_text = f"""
📖 **WalletLabel Bot 使用帮助**

{'=' * 40}

🔍 **基础查询**（免费版可用）：
直接发送地址，或使用 /check [地址]
支持公链：ETH、BSC、Polygon、BTC、TRON、SOL

📊 **深度分析**（月卡+可用）：
/analyze [地址]
包含持仓分布、交易行为、信任评分

⚠️ **风险评级**（月卡+可用）：
/risk [地址]
多因素综合评估，4级风险判定

📋 **批量查询**（年卡+可用）：
/batch [地址1] [地址2] ... [地址10]
一次查询最多10个地址

👤 **个人中心**：
/profile - 查看会员状态和查询次数
/subscribe - 升级会员解锁更多功能
/invite - 获取邀请链接，邀请得会员

{'=' * 40}

💡 **小贴士**：
• 免费用户每日可查询3次
• 地址支持0x开头的EVM地址、BTC、TRON、SOL
• 查询结果仅供参考，不构成投资建议

{'=' * 40}

📱 支持的公链：
• Ethereum (ETH)
• Binance Smart Chain (BSC)
• Polygon (MATIC)
• Bitcoin (BTC)
• TRON (TRX)
• Solana (SOL)
"""

    await update.message.reply_text(
        help_text.strip(),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查询地址标签"""
    user = get_or_create_user(update)

    # 检查权限
    if not user.can_query:
        if user.tier == UserTier.FREE and user.queries_today >= user.daily_limit:
            await update.message.reply_text(
                f"⚠️ 今日免费查询次数已用完 ({user.queries_today}/{user.daily_limit})\n\n"
                f"💡 发送 /subscribe 升级会员，解锁无限查询！",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "⚠️ 您的账户无法使用此功能，请联系客服。",
                parse_mode="Markdown",
            )
        return

    # 获取地址参数
    if not context.args:
        await update.message.reply_text(
            "❌ 请提供要查询的地址\n\n"
            "使用方法: `/check 0x...`",
            parse_mode="Markdown",
        )
        return

    address = context.args[0].strip()

    # 验证地址格式
    is_valid, detected_chain = validate_address(address)
    if not is_valid:
        await update.message.reply_text(
            f"❌ 地址格式不正确: `{address}`\n\n"
            f"支持的地址格式:\n"
            f"• EVM: 0x开头 (ETH/BSC/Polygon)\n"
            f"• BTC: 1/3/bc1开头\n"
            f"• TRON: T开头\n"
            f"• SOLANA: 字母数字串",
            parse_mode="Markdown",
        )
        return

    # 发送处理中消息
    processing_msg = await update.message.reply_text(
        "🔍 正在查询地址信息，请稍候...",
        parse_mode="Markdown",
    )

    try:
        # 查询标签
        chain = detected_chain or "ethereum"
        blockchain_info = blockchain_api.get_address_info(address, chain)
        label = label_engine.get_label(address, chain, blockchain_info)

        # 格式化消息
        message = format_label_message(label, blockchain_info)

        # 增加查询次数
        with get_db_context() as db:
            db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
            if db_user:
                db_user.increment_queries()
                db.commit()

        # 记录查询历史
        record_query(
            user.id,
            address,
            "check",
            f"{label.label} - {label.risk_name_cn}",
        )

        # 发送结果
        await processing_msg.edit_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    except Exception as e:
        logger.error(f"Check command error: {e}")
        await processing_msg.edit_text(
            f"❌ 查询失败，请稍后重试\n\n"
            f"错误信息: {str(e)}",
            parse_mode="Markdown",
        )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """深度分析地址"""
    user = get_or_create_user(update)

    # 检查权限
    if not user.can_query:
        await update.message.reply_text(
            "⚠️ 您的账户无法使用此功能，请联系客服。",
            parse_mode="Markdown",
        )
        return

    if not user.can_analyze:
        await update.message.reply_text(
            "⚠️ 深度分析功能仅对会员开放\n\n"
            "💡 发送 /subscribe 升级会员，解锁深度分析和风险评级功能！",
            parse_mode="Markdown",
        )
        return

    # 获取地址参数
    if not context.args:
        await update.message.reply_text(
            "❌ 请提供要分析的地址\n\n"
            "使用方法: `/analyze 0x...`",
            parse_mode="Markdown",
        )
        return

    address = context.args[0].strip()

    # 验证地址格式
    is_valid, detected_chain = validate_address(address)
    if not is_valid:
        await update.message.reply_text(
            f"❌ 地址格式不正确: `{address}`",
            parse_mode="Markdown",
        )
        return

    # 发送处理中消息
    processing_msg = await update.message.reply_text(
        "📊 正在进行深度分析，请稍候...\n"
        "（分析需要5-10秒）",
        parse_mode="Markdown",
    )

    try:
        # 执行分析
        chain = detected_chain or "ethereum"
        analysis = analysis_engine.analyze_address(address, chain)
        label = label_engine.get_label(address, chain, analysis.get("blockchain_info"))

        # 格式化消息
        message = format_analysis_message(analysis, label)

        # 增加查询次数
        with get_db_context() as db:
            db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
            if db_user:
                db_user.increment_queries()
                db.commit()

        # 记录查询历史
        record_query(
            user.id,
            address,
            "analyze",
            f"深度分析完成",
        )

        # 发送结果
        await processing_msg.edit_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    except Exception as e:
        logger.error(f"Analyze command error: {e}")
        await processing_msg.edit_text(
            f"❌ 分析失败，请稍后重试\n\n"
            f"错误信息: {str(e)}",
            parse_mode="Markdown",
        )


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """风险评级"""
    user = get_or_create_user(update)

    # 检查权限
    if not user.can_query:
        await update.message.reply_text(
            "⚠️ 您的账户无法使用此功能，请联系客服。",
            parse_mode="Markdown",
        )
        return

    if not user.can_analyze:
        await update.message.reply_text(
            "⚠️ 风险评级功能仅对会员开放\n\n"
            "💡 发送 /subscribe 升级会员，解锁风险评级功能！",
            parse_mode="Markdown",
        )
        return

    # 获取地址参数
    if not context.args:
        await update.message.reply_text(
            "❌ 请提供要评估的地址\n\n"
            "使用方法: `/risk 0x...`",
            parse_mode="Markdown",
        )
        return

    address = context.args[0].strip()

    # 验证地址格式
    is_valid, detected_chain = validate_address(address)
    if not is_valid:
        await update.message.reply_text(
            f"❌ 地址格式不正确: `{address}`",
            parse_mode="Markdown",
        )
        return

    # 发送处理中消息
    processing_msg = await update.message.reply_text(
        "⚠️ 正在进行风险评估，请稍候...",
        parse_mode="Markdown",
    )

    try:
        # 执行风险评估
        chain = detected_chain or "ethereum"
        label = label_engine.get_label(address, chain)
        blockchain_info = blockchain_api.get_address_info(address, chain)
        analysis = analysis_engine.analyze_address(address, chain)
        risk_assessment = risk_engine.assess_risk(address, chain, label, blockchain_info, analysis)

        # 格式化消息
        message = format_risk_message(risk_assessment, label)

        # 增加查询次数
        with get_db_context() as db:
            db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
            if db_user:
                db_user.increment_queries()
                db.commit()

        # 记录查询历史
        record_query(
            user.id,
            address,
            "risk",
            f"{risk_assessment.get('risk_name', '未知')} - {risk_assessment.get('risk_score', 0):.1f}分",
        )

        # 发送结果
        await processing_msg.edit_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    except Exception as e:
        logger.error(f"Risk command error: {e}")
        await processing_msg.edit_text(
            f"❌ 风险评估失败，请稍后重试\n\n"
            f"错误信息: {str(e)}",
            parse_mode="Markdown",
        )


async def batch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """批量查询"""
    user = get_or_create_user(update)

    # 检查权限
    if not user.can_query:
        await update.message.reply_text(
            "⚠️ 您的账户无法使用此功能，请联系客服。",
            parse_mode="Markdown",
        )
        return

    if not user.can_batch_query:
        await update.message.reply_text(
            "⚠️ 批量查询功能仅对年卡和专业版会员开放\n\n"
            "💡 发送 /subscribe 升级年卡会员，解锁批量查询功能！",
            parse_mode="Markdown",
        )
        return

    # 获取地址参数
    if not context.args:
        await update.message.reply_text(
            "❌ 请提供要查询的地址列表\n\n"
            "使用方法: `/batch 0x... 0x... 0x...`\n"
            "最多支持10个地址",
            parse_mode="Markdown",
        )
        return

    addresses = [addr.strip() for addr in context.args[:10]]

    # 验证地址格式
    valid_addresses = []
    invalid_addresses = []

    for addr in addresses:
        is_valid, _ = validate_address(addr)
        if is_valid:
            valid_addresses.append(addr)
        else:
            invalid_addresses.append(addr)

    if not valid_addresses:
        await update.message.reply_text(
            "❌ 没有有效的地址，请检查地址格式",
            parse_mode="Markdown",
        )
        return

    # 发送处理中消息
    processing_msg = await update.message.reply_text(
        f"📊 正在批量查询 {len(valid_addresses)} 个地址，请稍候...\n"
        f"（每个地址约需2-3秒）",
        parse_mode="Markdown",
    )

    try:
        # 执行批量查询
        results = []
        for address in valid_addresses:
            try:
                chain = blockchain_api.detect_chain(address) or "ethereum"
                label = label_engine.get_label(address, chain)
                blockchain_info = blockchain_api.get_address_info(address, chain)
                analysis = analysis_engine.analyze_address(address, chain)
                risk_assessment = risk_engine.assess_risk(address, chain, label, blockchain_info, analysis)

                results.append({
                    "address": address,
                    "label": label,
                    "risk_assessment": risk_assessment,
                })

                # 记录查询历史
                record_query(
                    user.id,
                    address,
                    "batch",
                    f"{risk_assessment.get('risk_name', '未知')}",
                )

            except Exception as e:
                logger.error(f"Batch query error for {address}: {e}")
                results.append({
                    "address": address,
                    "error": str(e),
                })

        # 增加查询次数
        with get_db_context() as db:
            db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
            if db_user:
                for _ in valid_addresses:
                    db_user.increment_queries()
                db.commit()

        # 格式化消息
        message = format_batch_result(results)

        if invalid_addresses:
            message += f"\n\n⚠️ 以下地址格式不正确，已跳过:\n"
            for addr in invalid_addresses:
                message += f"   • `{addr}`\n"

        # 发送结果
        await processing_msg.edit_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    except Exception as e:
        logger.error(f"Batch command error: {e}")
        await processing_msg.edit_text(
            f"❌ 批量查询失败，请稍后重试\n\n"
            f"错误信息: {str(e)}",
            parse_mode="Markdown",
        )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """个人中心"""
    user = get_or_create_user(update)
    message = format_profile_message(user)

    keyboard = [
        [
            InlineKeyboardButton("💎 升级会员", callback_data="subscribe"),
            InlineKeyboardButton("🎁 邀请好友", callback_data="invite"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """订阅会员"""
    user = get_or_create_user(update)
    message = format_subscribe_message()

    keyboard = [
        [
            InlineKeyboardButton(f"💎 月卡 ¥{settings.PRICE_MONTHLY}", callback_data="subscribe_monthly"),
            InlineKeyboardButton(f"👑 年卡 ¥{settings.PRICE_YEARLY}", callback_data="subscribe_yearly"),
        ],
        [
            InlineKeyboardButton(f"⚡ 专业版 ¥{settings.PRICE_PRO}/月", callback_data="subscribe_pro"),
        ],
        [
            InlineKeyboardButton("🎁 使用邀请码", callback_data="use_invite"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """邀请好友"""
    user = get_or_create_user(update)

    bot_username = context.bot.username if context.bot else "WalletLabelBot"
    invite_link = f"https://t.me/{bot_username}?start={user.invite_code}"

    message = f"""
🎁 **邀请好友计划**

{'=' * 40}

📊 **您的邀请信息**:
• 邀请码: `{user.invite_code}`
• 已邀请: {user.invite_count} 人
• 邀请链接: {invite_link}

{'=' * 40}

🎉 **邀请奖励**:
• 每邀请1位好友注册，双方各得 **7天会员**
• 邀请好友付费，您获得 **50%** 返利
• 年卡用户邀请返利 **翻倍**

{'=' * 40}

💡 **使用方法**:
1. 分享您的邀请链接给好友
2. 好友通过链接注册后自动绑定
3. 双方自动获得7天会员奖励
4. 好友付费后，返利自动到账

{'=' * 40}

📝 发送 /use_invite [邀请码] 使用邀请码
"""

    keyboard = [
        [
            InlineKeyboardButton("📤 分享邀请链接", switch_inline_query=f"邀请你使用WalletLabel Bot！{invite_link}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message.strip(),
        parse_mode="Markdown",
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


async def use_invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """使用邀请码"""
    user = get_or_create_user(update)

    if not context.args:
        await update.message.reply_text(
            "❌ 请提供邀请码\n\n"
            "使用方法: `/use_invite WLXXXXXXXX`",
            parse_mode="Markdown",
        )
        return

    invite_code = context.args[0].strip().upper()

    # 检查是否已经使用过邀请码
    if user.invited_by:
        await update.message.reply_text(
            "⚠️ 您已经使用过邀请码，无法重复使用",
            parse_mode="Markdown",
        )
        return

    # 检查邀请码是否是自己的
    if invite_code == user.invite_code:
        await update.message.reply_text(
            "⚠️ 不能使用自己的邀请码",
            parse_mode="Markdown",
        )
        return

    try:
        with get_db_context() as db:
            # 查找邀请人
            inviter = db.query(User).filter(User.invite_code == invite_code).first()

            if not inviter:
                await update.message.reply_text(
                    f"❌ 邀请码 `{invite_code}` 不存在",
                    parse_mode="Markdown",
                )
                return

            # 更新邀请关系
            db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
            db_user.invited_by = inviter.id

            # 增加邀请人邀请数
            inviter.invite_count += 1

            # 双方各得7天会员
            db_user.extend_subscription(7)
            inviter.extend_subscription(7)

            db.commit()

            await update.message.reply_text(
                f"✅ 邀请码使用成功！\n\n"
                f"🎁 您和邀请人 @{inviter.username or inviter.telegram_id} 各获得 **7天会员**！\n\n"
                f"发送 /profile 查看您的会员状态",
                parse_mode="Markdown",
            )

            # 通知邀请人
            try:
                await context.bot.send_message(
                    chat_id=inviter.telegram_id,
                    text=f"🎉 邀请成功！\n\n"
                         f"您邀请的用户 @{user.username or user.telegram_id} 已注册\n"
                         f"🎁 您获得 **7天会员** 奖励！\n\n"
                         f"当前已邀请: {inviter.invite_count} 人",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Failed to notify inviter: {e}")

    except Exception as e:
        logger.error(f"Use invite error: {e}")
        await update.message.reply_text(
            f"❌ 使用邀请码失败，请稍后重试\n\n"
            f"错误信息: {str(e)}",
            parse_mode="Markdown",
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通消息（直接发送地址）"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # 忽略命令消息
    if text.startswith("/"):
        return

    # 检查是否是地址
    is_valid, _ = validate_address(text)
    if is_valid:
        # 模拟调用 /check 命令
        context.args = [text]
        await check_command(update, context)
    else:
        # 提示用户
        await update.message.reply_text(
            "❓ 请发送钱包地址进行查询，或使用 /help 查看帮助\n\n"
            "支持的地址格式:\n"
            "• EVM: 0x开头 (ETH/BSC/Polygon)\n"
            "• BTC: 1/3/bc1开头\n"
            "• TRON: T开头\n"
            "• SOLANA: 字母数字串",
            parse_mode="Markdown",
        )
