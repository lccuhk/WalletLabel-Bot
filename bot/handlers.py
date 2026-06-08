"""
Bot 回调处理模块 - 处理内联按钮点击事件
"""

import uuid
from datetime import datetime
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import settings
from models import get_db_context, User, UserTier
from .commands import get_or_create_user
from .utils import format_subscribe_message


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理回调查询"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    callback_data = query.data
    user = get_or_create_user(update)

    logger.info(f"Callback received: {callback_data} from user {user.telegram_id}")

    # 根据回调数据类型分发处理
    if callback_data == "subscribe":
        await handle_subscribe_menu(update, context, user)
    elif callback_data == "subscribe_monthly":
        await handle_subscribe(update, context, user, "monthly")
    elif callback_data == "subscribe_yearly":
        await handle_subscribe(update, context, user, "yearly")
    elif callback_data == "subscribe_pro":
        await handle_subscribe(update, context, user, "pro")
    elif callback_data == "use_invite":
        await handle_use_invite_prompt(update, context, user)
    elif callback_data == "invite":
        await handle_invite_menu(update, context, user)
    elif callback_data == "confirm_payment":
        await handle_confirm_payment(update, context, user)
    elif callback_data == "cancel_payment":
        await handle_cancel_payment(update, context, user)
    elif callback_data.startswith("verify_payment_"):
        order_id = callback_data.replace("verify_payment_", "")
        await handle_verify_payment(update, context, user, order_id)
    else:
        await query.edit_message_text(
            "⚠️ 未知的操作",
            parse_mode="Markdown",
        )


async def handle_subscribe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
    """显示订阅菜单"""
    query = update.callback_query
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

    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, plan: str):
    """处理订阅请求"""
    query = update.callback_query

    plan_info = {
        "monthly": {
            "name": "月卡会员",
            "price": settings.PRICE_MONTHLY,
            "days": 30,
            "tier": UserTier.MONTHLY,
            "emoji": "💎",
        },
        "yearly": {
            "name": "年卡会员",
            "price": settings.PRICE_YEARLY,
            "days": 365,
            "tier": UserTier.YEARLY,
            "emoji": "👑",
        },
        "pro": {
            "name": "专业版",
            "price": settings.PRICE_PRO,
            "days": 30,
            "tier": UserTier.PRO,
            "emoji": "⚡",
        },
    }

    info = plan_info.get(plan)
    if not info:
        await query.edit_message_text(
            "⚠️ 未知的订阅计划",
            parse_mode="Markdown",
        )
        return

    # 生成订单ID
    order_id = f"WL{uuid.uuid4().hex[:12].upper()}"

    # 计算USDT金额（假设1 USDT = ¥7.2）
    usdt_amount = round(info["price"] / 7.2, 2)

    # USDT收款地址
    usdt_address = settings.USDT_TRC20_ADDRESS or "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE"

    message = f"""
{info['emoji']} **{info['name']} 支付订单**

{'=' * 40}

📋 **订单信息**:
• 订单号: `{order_id}`
• 套餐: {info['name']}
• 时长: {info['days']}天
• 价格: ¥{info['price']} (≈ {usdt_amount} USDT)

{'=' * 40}

💳 **支付方式 - USDT (TRC20)**:

`{usdt_address}`

⚠️ **重要提示**:
1. 请确保使用 **TRC20网络** 转账
2. 转账金额必须为 **{usdt_amount} USDT**
3. 转账后请点击下方"我已付款"按钮
4. 系统将自动验证到账情况
5. 通常1-5分钟到账

{'=' * 40}

📞 如有问题，请联系客服: @YourSupport
"""

    keyboard = [
        [
            InlineKeyboardButton("✅ 我已付款", callback_data=f"verify_payment_{order_id}"),
            InlineKeyboardButton("❌ 取消", callback_data="cancel_payment"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 保存订单信息到用户上下文
    context.user_data["pending_order"] = {
        "order_id": order_id,
        "plan": plan,
        "tier": info["tier"],
        "days": info["days"],
        "price": info["price"],
        "usdt_amount": usdt_amount,
        "created_at": datetime.utcnow(),
    }

    await query.edit_message_text(
        message.strip(),
        parse_mode="Markdown",
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


async def handle_use_invite_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
    """提示使用邀请码"""
    query = update.callback_query

    if user.invited_by:
        await query.edit_message_text(
            "⚠️ 您已经使用过邀请码，无法重复使用",
            parse_mode="Markdown",
        )
        return

    message = f"""
🎁 **使用邀请码**

{'=' * 40}

请发送邀请码，格式如下：

`/use_invite WLXXXXXXXX`

或者直接在聊天中发送邀请码。

{'=' * 40}

💡 使用邀请码后，您和邀请人各得 **7天会员**！
"""

    await query.edit_message_text(
        message.strip(),
        parse_mode="Markdown",
    )


async def handle_invite_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
    """显示邀请菜单"""
    query = update.callback_query

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
"""

    keyboard = [
        [
            InlineKeyboardButton("📤 分享邀请链接", switch_inline_query=f"邀请你使用WalletLabel Bot！{invite_link}"),
        ],
        [
            InlineKeyboardButton("🔙 返回", callback_data="subscribe"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        message.strip(),
        parse_mode="Markdown",
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


async def handle_verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, order_id: str):
    """验证支付（模拟）"""
    query = update.callback_query

    pending_order = context.user_data.get("pending_order")
    if not pending_order or pending_order["order_id"] != order_id:
        await query.edit_message_text(
            "⚠️ 订单不存在或已过期，请重新下单",
            parse_mode="Markdown",
        )
        return

    # 模拟支付验证（实际项目中需要对接支付网关）
    # 这里简化处理：直接确认支付成功
    is_paid = True  # 模拟支付成功

    if is_paid:
        try:
            with get_db_context() as db:
                db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()

                # 更新会员等级
                old_tier = db_user.tier
                db_user.tier = pending_order["tier"]
                db_user.extend_subscription(pending_order["days"])
                db_user.total_paid += pending_order["price"]

                db.commit()
                db.refresh(db_user)

                # 检查是否有邀请人，给予返利
                if db_user.invited_by:
                    inviter = db.query(User).filter(User.id == db_user.invited_by).first()
                    if inviter:
                        # 计算返利（50%）
                        rebate_percent = 0.5
                        if inviter.tier == UserTier.YEARLY:
                            rebate_percent = 1.0  # 年卡用户返利翻倍

                        rebate_amount = pending_order["price"] * rebate_percent

                        # 给予邀请人会员时长（按返利金额换算）
                        rebate_days = int(rebate_amount / settings.PRICE_MONTHLY * 30)
                        inviter.extend_subscription(rebate_days)
                        inviter.total_paid += rebate_amount

                        db.commit()

                        # 通知邀请人
                        try:
                            await context.bot.send_message(
                                chat_id=inviter.telegram_id,
                                text=f"🎉 邀请返利到账！\n\n"
                                     f"您邀请的用户 @{db_user.username or db_user.telegram_id} 购买了 {pending_order['tier'].value} 会员\n"
                                     f"🎁 您获得 **{rebate_days}天会员** 奖励！\n\n"
                                     f"当前已邀请: {inviter.invite_count} 人",
                                parse_mode="Markdown",
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify inviter: {e}")

            # 清除订单
            context.user_data.pop("pending_order", None)

            tier_names = {
                UserTier.MONTHLY: "月卡会员",
                UserTier.YEARLY: "年卡会员",
                UserTier.PRO: "专业版",
            }
            tier_name = tier_names.get(pending_order["tier"], "会员")

            message = f"""
✅ **支付成功！**

{'=' * 40}

🎉 恭喜您成功升级为 **{tier_name}**！

📋 **订单信息**:
• 订单号: `{order_id}`
• 套餐: {tier_name}
• 时长: {pending_order['days']}天
• 金额: ¥{pending_order['price']}

{'=' * 40}

🎁 **您已解锁**:
• 无限次地址查询
• 深度持仓分析
• 风险评级报告
{f'• 批量查询功能' if pending_order['tier'] in [UserTier.YEARLY, UserTier.PRO] else ''}
{f'• API接口调用' if pending_order['tier'] == UserTier.PRO else ''}

{'=' * 40}

💡 现在可以发送 /analyze [地址] 体验深度分析功能！
"""

            keyboard = [
                [
                    InlineKeyboardButton("📊 立即体验", switch_inline_query_current_chat="/analyze "),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message.strip(),
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )

            # 通知管理员
            if settings.TELEGRAM_ADMIN_ID:
                try:
                    await context.bot.send_message(
                        chat_id=settings.TELEGRAM_ADMIN_ID,
                        text=f"💰 新订单！\n\n"
                             f"用户: @{user.username or user.telegram_id}\n"
                             f"订单: {order_id}\n"
                             f"套餐: {tier_name}\n"
                             f"金额: ¥{pending_order['price']}",
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin: {e}")

        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            await query.edit_message_text(
                f"❌ 支付验证失败，请稍后重试或联系客服\n\n"
                f"错误信息: {str(e)}",
                parse_mode="Markdown",
            )
    else:
        message = f"""
⚠️ **支付未到账**

{'=' * 40}

订单号: `{order_id}`

系统未检测到您的支付，请确认：
1. 是否使用了正确的TRC20网络
2. 转账金额是否为 {pending_order['usdt_amount']} USDT
3. 是否已经等待足够的区块确认（通常1-5分钟）

{'=' * 40}

如果您已经转账，请稍后再次点击验证按钮。
如有问题，请联系客服: @YourSupport
"""

        keyboard = [
            [
                InlineKeyboardButton("🔄 重新验证", callback_data=f"verify_payment_{order_id}"),
                InlineKeyboardButton("❌ 取消", callback_data="cancel_payment"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )


async def handle_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
    """确认支付（备用）"""
    query = update.callback_query
    await query.edit_message_text(
        "✅ 请使用下方的验证按钮确认支付",
        parse_mode="Markdown",
    )


async def handle_cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
    """取消支付"""
    query = update.callback_query

    # 清除订单
    context.user_data.pop("pending_order", None)

    message = f"""
❌ **支付已取消**

{'=' * 40}

您可以随时发送 /subscribe 重新选择套餐。

如有问题，请联系客服: @YourSupport
"""

    keyboard = [
        [
            InlineKeyboardButton("💎 重新选择套餐", callback_data="subscribe"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        message.strip(),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def handle_start_with_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理带邀请码的start命令"""
    if not context.args:
        return None

    invite_code = context.args[0].strip().upper()

    # 检查邀请码格式
    if not invite_code.startswith("WL") or len(invite_code) != 10:
        return None

    user = get_or_create_user(update)

    # 检查是否已经使用过邀请码
    if user.invited_by:
        return None

    # 检查邀请码是否是自己的
    if invite_code == user.invite_code:
        return None

    try:
        with get_db_context() as db:
            # 查找邀请人
            inviter = db.query(User).filter(User.invite_code == invite_code).first()

            if not inviter:
                return None

            # 更新邀请关系
            db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
            db_user.invited_by = inviter.id

            # 增加邀请人邀请数
            inviter.invite_count += 1

            # 双方各得7天会员
            db_user.extend_subscription(7)
            inviter.extend_subscription(7)

            db.commit()
            db.refresh(db_user)
            db.refresh(inviter)

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

            return f"🎁 邀请码使用成功！\n\n您和邀请人 @{inviter.username or inviter.telegram_id} 各获得 **7天会员**！\n\n"

    except Exception as e:
        logger.error(f"Auto invite error: {e}")
        return None
