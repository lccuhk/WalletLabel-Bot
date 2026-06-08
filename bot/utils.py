"""
Bot 工具函数 - 消息格式化
"""

from datetime import datetime, timezone, timedelta
from typing import Dict

from models import AddressLabel, User, UserTier
from config import settings


def get_cn_time(utc_time: datetime) -> datetime:
    return utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))


def format_label_message(label: AddressLabel, blockchain_info: Dict = None) -> str:
    tags_text = ""
    if label.tags:
        tags_text = "\n🏷️ 标签: " + ", ".join([f"#{t}" for t in label.tags[:5]])

    verified_text = "✅ 已认证" if label.is_verified else "⚠️ 未认证"

    message = f"""
{'=' * 40}
🏷️ **地址标签查询结果**
{'=' * 40}

📍 **地址**: `{label.address}`
🔗 **公链**: {label.chain_name if hasattr(label, 'chain_name') else label.chain}

{label.type_emoji} **类型**: {label.type_name_cn}
📛 **名称**: **{label.label}**
🔍 **认证**: {verified_text}

{label.risk_emoji} **风险等级**: {label.risk_name_cn}
📊 **风险评分**: {label.risk_score:.1f}/100
{tags_text}

📝 **描述**:
{label.description or '暂无描述'}

📅 **数据来源**: {label.source}
⏰ **更新时间**: {get_cn_time(label.updated_at).strftime('%Y-%m-%d %H:%M')}

{'=' * 40}
💡 发送 /analyze {label.address} 查看深度分析
💡 发送 /risk {label.address} 查看风险评级
{'=' * 40}
"""

    if blockchain_info:
        balance = blockchain_info.get("native_balance")
        symbol = blockchain_info.get("native_symbol")
        tx_count = blockchain_info.get("transaction_count")
        if balance is not None and symbol:
            message += f"\n💰 余额: {balance:.4f} {symbol}"
        if tx_count:
            message += f"\n📊 交易次数: {tx_count}"

    return message.strip()


def format_analysis_message(analysis: Dict, label: AddressLabel = None) -> str:
    holdings = analysis.get("holdings_analysis", {})
    transactions = analysis.get("transaction_analysis", {})
    behavior = analysis.get("behavior_analysis", {})

    activity_emojis = {
        "very_active": "🔥",
        "active": "⚡",
        "moderate": "📊",
        "inactive": "💤",
    }

    activity_level = transactions.get("activity_level", "inactive")
    activity_emoji = activity_emojis.get(activity_level, "📊")

    behavior_types = {
        "new_address": "🆕 新地址",
        "low_activity": "📉 低活跃",
        "accumulator": "🐋 囤币者",
        "trader": "📈 交易者",
        "distributor": "📤 分发者",
        "regular_user": "👤 普通用户",
        "unknown": "❓ 未知",
    }

    behavior_type = behavior.get("behavior_type", "unknown")
    behavior_text = behavior_types.get(behavior_type, "❓ 未知")

    tokens = holdings.get("tokens", [])
    tokens_text = ""
    if tokens:
        tokens_text = "\n\n💎 **主要持仓**:\n"
        for token in tokens[:5]:
            balance = token.get("balance", 0)
            if balance > 0:
                tokens_text += f"   • {token.get('symbol', 'Unknown')}: {balance:.4f}\n"

    risk_factors = behavior.get("risk_factors", [])
    positive_factors = behavior.get("positive_factors", [])

    risk_text = ""
    if risk_factors:
        risk_text = "\n⚠️ **风险因素**:\n"
        for factor in risk_factors[:3]:
            risk_text += f"   • {factor}\n"

    positive_text = ""
    if positive_factors:
        positive_text = "\n✅ **积极因素**:\n"
        for factor in positive_factors[:3]:
            positive_text += f"   • {factor}\n"

    message = f"""
{'=' * 40}
📊 **地址深度分析报告**
{'=' * 40}

📍 **地址**: `{analysis['address']}`
🔗 **公链**: {analysis.get('chain_name', analysis.get('chain', ''))}

{behavior_text}
{activity_emoji} **活跃度**: {activity_level.replace('_', ' ').title()}
🤝 **信任评分**: {behavior.get('trust_score', 50)}/100

{'=' * 20} 持仓分析 {'=' * 20}
💰 **主币余额**: {holdings.get('native_balance', 0):.4f} {holdings.get('native_symbol', '')}
🎯 **持仓币种**: {holdings.get('token_count', 0)} 种
📊 **分散度**: {holdings.get('diversification_score', 0)}%
📝 {holdings.get('holding_summary', '')}
{tokens_text}

{'=' * 20} 交易分析 {'=' * 20}
📊 **总交易次数**: {transactions.get('total_transactions', 0)}
📤 **转出**: {transactions.get('sent_count', 0)} 次
📥 **转入**: {transactions.get('received_count', 0)} 次
📅 **地址年龄**: {transactions.get('age_days', 0)} 天
⚡ **日均交易**: {transactions.get('tx_per_day', 0)} 次
⏰ **首次交易**: {get_cn_time(transactions['first_transaction']).strftime('%Y-%m-%d') if transactions.get('first_transaction') else '未知'}
⏰ **最近交易**: {get_cn_time(transactions['last_transaction']).strftime('%Y-%m-%d') if transactions.get('last_transaction') else '未知'}
❌ **失败率**: {transactions.get('error_rate', 0):.1%}

📝 {transactions.get('transaction_summary', '')}

{'=' * 20} 行为分析 {'=' * 20}
📝 {behavior.get('behavior_description', '')}
{risk_text}
{positive_text}

{'=' * 40}
💡 发送 /risk {analysis['address']} 查看详细风险评级
{'=' * 40}
"""

    return message.strip()


def format_risk_message(risk_assessment: Dict, label: AddressLabel = None) -> str:
    risk_level = risk_assessment.get("risk_level")
    risk_emoji = risk_assessment.get("risk_emoji", "⚪")
    risk_name = risk_assessment.get("risk_name", "未知")
    risk_score = risk_assessment.get("risk_score", 50)

    bar_length = 20
    filled_length = int(risk_score / 100 * bar_length)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    color_codes = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }
    color_emoji = color_codes.get(risk_level.value if hasattr(risk_level, 'value') else risk_level, "⚪")

    recommendations = risk_assessment.get("recommendations", [])
    rec_text = "\n".join([f"   {r}" for r in recommendations[:8]])

    message = f"""
{'=' * 40}
⚠️ **风险评级报告**
{'=' * 40}

📍 **地址**: `{risk_assessment['address']}`
🔗 **公链**: {risk_assessment.get('chain', '')}

{risk_emoji} **风险等级**: **{risk_name}**
{color_emoji} **综合评分**: {risk_score:.1f}/100

{color_emoji} {bar} {risk_score:.0f}%

📊 **评分构成**:
   • 标签风险: {risk_assessment.get('label_risk_score', 50):.1f}/100
   • 行为信任: {risk_assessment.get('trust_score', 50):.1f}/100

{'=' * 20} 评估建议 {'=' * 20}
{rec_text}

{'=' * 20} 评估摘要 {'=' * 20}
{risk_assessment.get('summary', '')}

{'=' * 40}
⚠️ **免责声明**: 本评估基于公开数据，仅供参考，不构成任何投资建议。
{'=' * 40}
"""

    return message.strip()


def format_profile_message(user: User) -> str:
    tier_names = {
        UserTier.FREE: "🆓 免费版",
        UserTier.MONTHLY: "💎 月卡会员",
        UserTier.YEARLY: "👑 年卡会员",
        UserTier.PRO: "⚡ 专业版",
        UserTier.ADMIN: "⚙️ 管理员",
    }

    tier_name = tier_names.get(user.tier, "未知")

    expires_text = ""
    if user.tier not in [UserTier.FREE, UserTier.ADMIN]:
        if user.subscription_expires_at:
            expires_cn = get_cn_time(user.subscription_expires_at)
            expires_text = f"\n⏰ 到期时间: {expires_cn.strftime('%Y-%m-%d %H:%M')}"

            days_left = (user.subscription_expires_at - datetime.utcnow()).days
            if days_left > 0:
                expires_text += f" (剩余{days_left}天)"
            else:
                expires_text += " (已过期)"

    invite_text = ""
    if user.invite_code:
        invite_text = f"""
🎁 邀请码: `{user.invite_code}`
👥 已邀请: {user.invite_count}人
"""

    message = f"""
👤 **个人中心**

🆔 用户ID: `{user.telegram_id}`
👤 用户名: @{user.username or '未设置'}
📊 会员等级: {tier_name}
{expires_text}
🔍 今日已查询: {user.queries_today}/{user.daily_limit}
💰 累计消费: ¥{user.total_paid:.1f}
{invite_text}
📊 会员权益:
   • 免费版: 每日3次查询
   • 月卡: 无限查询 + 深度分析
   • 年卡: 全部功能 + 批量查询
   • 专业版: 全部功能 + API接口

💡 发送 /subscribe 升级会员，解锁更多功能！
"""

    return message.strip()


def format_subscribe_message() -> str:
    message = f"""
💎 **会员订阅计划** 💎

{'=' * 40}

🆓 **免费版** - ¥0/天
• 每日3次地址查询
• 基础标签识别

{'=' * 40}

💎 **月卡会员** - ¥{settings.PRICE_MONTHLY}/月
• ✅ 无限次地址查询
• ✅ 深度持仓分析
• ✅ 风险评级报告
• ✅ 优先客服支持

{'=' * 40}

👑 **年卡会员** - ¥{settings.PRICE_YEARLY}/年 (约¥16.6/月)
• ✅ 月卡全部功能
• ✅ 批量查询 (最多10个地址)
• ✅ 专属VIP社群
• ✅ 邀请返利50%

{'=' * 40}

⚡ **专业版** - ¥{settings.PRICE_PRO}/月
• ✅ 年卡全部功能
• ✅ API 接口调用
• ✅ 自定义查询频率
• ✅ 一对一技术支持

{'=' * 40}

🎁 **限时优惠**:
• 前100名用户免费升级月卡7天
• 邀请好友注册，双方各得7天会员
• 年卡用户额外赠送2个月

💳 **支付方式**:
• USDT (TRC20)
• 支付宝
• 微信支付

📱 选择您的套餐：
"""

    return message.strip()


def format_batch_result(results: list) -> str:
    message = "📊 **批量查询结果**\n\n"

    for i, result in enumerate(results, 1):
        if "error" in result:
            message += f"{i}. `{result['address']}` - ❌ 查询失败: {result['error']}\n"
        else:
            risk = result.get("risk_assessment", {})
            label = result.get("label", {})
            risk_emoji = risk.get("risk_emoji", "⚪")
            risk_name = risk.get("risk_name", "未知")
            label_name = getattr(label, "label", "未知") if hasattr(label, "label") else "未知"

            message += f"{i}. `{result['address'][:12]}...`\n"
            message += f"   🏷️ {label_name}\n"
            message += f"   {risk_emoji} {risk_name} ({risk.get('risk_score', 0):.0f}分)\n\n"

    message += "\n💡 点击地址查看详情，或发送 /analyze [地址] 查看深度分析"

    return message.strip()
