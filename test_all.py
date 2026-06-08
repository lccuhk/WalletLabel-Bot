#!/usr/bin/env python3
"""
WalletLabel Bot 全面测试脚本
测试所有核心功能模块
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 使用测试数据库
os.environ["DATABASE_URL"] = "sqlite:///./data/test_wallet_bot.db"

import unittest
from datetime import datetime, timedelta
from loguru import logger

# 禁用日志输出
logger.remove()


class TestConfig(unittest.TestCase):
    """测试配置模块"""

    def test_settings_loaded(self):
        """测试配置加载"""
        from config import settings
        self.assertIsNotNone(settings)
        self.assertEqual(settings.FREE_DAILY_LIMIT, 3)
        self.assertEqual(settings.PRICE_MONTHLY, 19.9)
        self.assertEqual(settings.PRICE_YEARLY, 199)
        self.assertEqual(settings.PRICE_PRO, 99)

    def test_supported_chains(self):
        """测试支持的公链"""
        from config import settings
        chains = settings.supported_chains
        self.assertIn("ethereum", chains)
        self.assertIn("bsc", chains)
        self.assertIn("polygon", chains)

    def test_address_patterns(self):
        """测试地址格式正则"""
        from config import settings
        import re

        patterns = settings.address_patterns

        # 测试ETH地址
        self.assertTrue(re.match(patterns["ethereum"], "0x28C6c06298d514Db089934071355E5743bf21d60"))
        self.assertFalse(re.match(patterns["ethereum"], "invalid_address"))

        # 测试BTC地址
        self.assertTrue(re.match(patterns["bitcoin"], "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"))
        self.assertTrue(re.match(patterns["bitcoin"], "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"))

        # 测试TRON地址
        self.assertTrue(re.match(patterns["tron"], "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE"))

        # 测试SOLANA地址
        self.assertTrue(re.match(patterns["solana"], "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"))


class TestDatabase(unittest.TestCase):
    """测试数据库模块"""

    @classmethod
    def setUpClass(cls):
        """初始化测试数据库"""
        from models import init_db, engine, Base
        # 删除旧的测试数据库
        test_db = project_root / "data" / "test_wallet_bot.db"
        if test_db.exists():
            test_db.unlink()
        init_db()

    def test_database_connection(self):
        """测试数据库连接"""
        from models import get_db_context
        with get_db_context() as db:
            self.assertIsNotNone(db)

    def test_user_creation(self):
        """测试用户创建"""
        from models import get_db_context, User, UserTier, generate_invite_code

        with get_db_context() as db:
            # 使用不同的用户ID避免与其他测试冲突
            test_telegram_id = 999999999

            # 先删除已存在的用户（避免测试顺序问题）
            existing = db.query(User).filter(User.telegram_id == test_telegram_id).first()
            if existing:
                db.delete(existing)
                db.commit()

            user = User(
                telegram_id=test_telegram_id,
                username="testuser_new",
                first_name="TestNew",
                last_name="UserNew",
                invite_code=generate_invite_code(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            self.assertIsNotNone(user.id)
            self.assertEqual(user.telegram_id, test_telegram_id)
            self.assertEqual(user.tier, UserTier.FREE)
            self.assertTrue(user.can_query)
            self.assertFalse(user.can_analyze)
            self.assertFalse(user.can_batch_query)
            self.assertEqual(user.daily_limit, 3)

    def test_user_subscription(self):
        """测试用户订阅"""
        from models import get_db_context, User, UserTier

        with get_db_context() as db:
            user = db.query(User).filter(User.telegram_id == 123456789).first()
            self.assertIsNotNone(user)

            # 升级到月卡
            user.tier = UserTier.MONTHLY
            user.extend_subscription(30)
            db.commit()
            db.refresh(user)

            self.assertTrue(user.can_analyze)
            self.assertFalse(user.can_batch_query)
            self.assertTrue(user.is_subscription_active)

            # 升级到年卡
            user.tier = UserTier.YEARLY
            user.extend_subscription(365)
            db.commit()
            db.refresh(user)

            self.assertTrue(user.can_analyze)
            self.assertTrue(user.can_batch_query)

    def test_query_history(self):
        """测试查询历史"""
        from models import get_db_context, QueryHistory, User, generate_invite_code

        with get_db_context() as db:
            # 确保用户存在
            user = db.query(User).filter(User.telegram_id == 123456789).first()
            if not user:
                user = User(
                    telegram_id=123456789,
                    username="testuser",
                    first_name="Test",
                    last_name="User",
                    invite_code=generate_invite_code(),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            self.assertIsNotNone(user)

            history = QueryHistory(
                user_id=user.id,
                address="0x28C6c06298d514Db089934071355E5743bf21d60",
                query_type="check",
                result_summary="Binance - 低风险",
            )
            db.add(history)
            db.commit()
            db.refresh(history)

            self.assertIsNotNone(history.id)
            self.assertEqual(history.user_id, user.id)


class TestBlockchainAPI(unittest.TestCase):
    """测试区块链API"""

    def test_detect_chain(self):
        """测试公链检测"""
        from core import blockchain_api

        # ETH地址
        chain = blockchain_api.detect_chain("0x28C6c06298d514Db089934071355E5743bf21d60")
        self.assertEqual(chain, "ethereum")

        # BTC地址
        chain = blockchain_api.detect_chain("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.assertEqual(chain, "bitcoin")

        # TRON地址
        chain = blockchain_api.detect_chain("TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE")
        self.assertEqual(chain, "tron")

        # 无效地址
        chain = blockchain_api.detect_chain("invalid_address")
        self.assertIsNone(chain)

    def test_get_address_info(self):
        """测试获取地址信息"""
        from core import blockchain_api

        # 测试已知交易所地址
        info = blockchain_api.get_address_info(
            "0x28C6c06298d514Db089934071355E5743bf21d60",
            "ethereum"
        )
        self.assertIsNotNone(info)
        self.assertIn("chain", info)
        self.assertIn("native_balance", info)
        self.assertIn("transaction_count", info)

        # 测试随机地址
        info = blockchain_api.get_address_info(
            "0x1234567890123456789012345678901234567890",
            "ethereum"
        )
        self.assertIsNotNone(info)


class TestLabelEngine(unittest.TestCase):
    """测试标签引擎"""

    def test_get_exchange_label(self):
        """测试获取交易所标签"""
        from core import label_engine
        from models import AddressType, RiskLevel

        label = label_engine.get_label(
            "0x28C6c06298d514Db089934071355E5743bf21d60",
            "ethereum"
        )

        self.assertIsNotNone(label)
        self.assertEqual(label.address.lower(), "0x28C6c06298d514Db089934071355E5743bf21d60".lower())
        self.assertEqual(label.address_type, AddressType.EXCHANGE)
        self.assertEqual(label.label, "Binance")
        self.assertTrue(label.is_verified)
        self.assertEqual(label.risk_level, RiskLevel.LOW)

    def test_get_unknown_label(self):
        """测试获取未知地址标签"""
        from core import label_engine
        from models import AddressType, RiskLevel

        label = label_engine.get_label(
            "0x1234567890123456789012345678901234567890",
            "ethereum"
        )

        self.assertIsNotNone(label)
        self.assertEqual(label.address_type, AddressType.UNKNOWN)
        self.assertEqual(label.label, "未知地址")
        self.assertFalse(label.is_verified)
        self.assertEqual(label.risk_level, RiskLevel.MEDIUM)

    def test_local_labels_loaded(self):
        """测试本地标签加载"""
        from core import label_engine

        self.assertGreater(len(label_engine._exchange_labels), 0)
        self.assertIn("ethereum", label_engine._exchange_labels)
        self.assertIn("bsc", label_engine._exchange_labels)


class TestAnalysisEngine(unittest.TestCase):
    """测试分析引擎"""

    def test_analyze_exchange_address(self):
        """测试分析交易所地址"""
        from core import analysis_engine

        analysis = analysis_engine.analyze_address(
            "0x28C6c06298d514Db089934071355E5743bf21d60",
            "ethereum"
        )

        self.assertIsNotNone(analysis)
        self.assertIn("address", analysis)
        self.assertIn("chain", analysis)
        self.assertIn("holdings_analysis", analysis)
        self.assertIn("transaction_analysis", analysis)
        self.assertIn("behavior_analysis", analysis)

        holdings = analysis["holdings_analysis"]
        self.assertIn("native_balance", holdings)
        self.assertIn("token_count", holdings)

        transactions = analysis["transaction_analysis"]
        self.assertIn("total_transactions", transactions)
        self.assertIn("activity_level", transactions)

        behavior = analysis["behavior_analysis"]
        self.assertIn("behavior_type", behavior)
        self.assertIn("trust_score", behavior)

    def test_analyze_unknown_address(self):
        """测试分析未知地址"""
        from core import analysis_engine

        analysis = analysis_engine.analyze_address(
            "0x1234567890123456789012345678901234567890",
            "ethereum"
        )

        self.assertIsNotNone(analysis)
        self.assertIn("behavior_analysis", analysis)


class TestRiskEngine(unittest.TestCase):
    """测试风险引擎"""

    def test_assess_exchange_risk(self):
        """测试评估交易所风险"""
        from core import risk_engine, label_engine, blockchain_api, analysis_engine
        from models import RiskLevel

        address = "0x28C6c06298d514Db089934071355E5743bf21d60"
        chain = "ethereum"

        label = label_engine.get_label(address, chain)
        blockchain_info = blockchain_api.get_address_info(address, chain)
        analysis = analysis_engine.analyze_address(address, chain)

        risk = risk_engine.assess_risk(address, chain, label, blockchain_info, analysis)

        self.assertIsNotNone(risk)
        self.assertIn("risk_level", risk)
        self.assertIn("risk_score", risk)
        self.assertIn("recommendations", risk)
        self.assertIn("summary", risk)

        # 交易所应该是低风险
        self.assertGreater(risk["risk_score"], 70)

    def test_assess_unknown_risk(self):
        """测试评估未知地址风险"""
        from core import risk_engine, label_engine, blockchain_api, analysis_engine

        address = "0x1234567890123456789012345678901234567890"
        chain = "ethereum"

        label = label_engine.get_label(address, chain)
        blockchain_info = blockchain_api.get_address_info(address, chain)
        analysis = analysis_engine.analyze_address(address, chain)

        risk = risk_engine.assess_risk(address, chain, label, blockchain_info, analysis)

        self.assertIsNotNone(risk)
        self.assertIn("risk_level", risk)
        self.assertIn("risk_score", risk)

    def test_risk_factors(self):
        """测试风险因素"""
        from core import risk_engine

        self.assertIn("hacker_address", risk_engine.risk_factors)
        self.assertIn("scam_address", risk_engine.risk_factors)
        self.assertIn("verified_exchange", risk_engine.risk_factors)
        self.assertIn("new_address", risk_engine.risk_factors)


class TestBotUtils(unittest.TestCase):
    """测试Bot工具函数"""

    def test_format_label_message(self):
        """测试格式化标签消息"""
        from bot import format_label_message
        from core import label_engine

        label = label_engine.get_label(
            "0x28C6c06298d514Db089934071355E5743bf21d60",
            "ethereum"
        )

        message = format_label_message(label)
        self.assertIsInstance(message, str)
        self.assertIn("Binance", message)
        self.assertIn("交易所", message)
        self.assertIn("风险等级", message)

    def test_format_analysis_message(self):
        """测试格式化分析消息"""
        from bot import format_analysis_message
        from core import analysis_engine, label_engine

        analysis = analysis_engine.analyze_address(
            "0x28C6c06298d514Db089934071355E5743bf21d60",
            "ethereum"
        )
        label = label_engine.get_label(
            "0x28C6c06298d514Db089934071355E5743bf21d60",
            "ethereum"
        )

        message = format_analysis_message(analysis, label)
        self.assertIsInstance(message, str)
        self.assertIn("深度分析报告", message)
        self.assertIn("持仓分析", message)
        self.assertIn("交易分析", message)

    def test_format_risk_message(self):
        """测试格式化风险消息"""
        from bot import format_risk_message
        from core import risk_engine, label_engine, blockchain_api, analysis_engine

        address = "0x28C6c06298d514Db089934071355E5743bf21d60"
        chain = "ethereum"

        label = label_engine.get_label(address, chain)
        blockchain_info = blockchain_api.get_address_info(address, chain)
        analysis = analysis_engine.analyze_address(address, chain)
        risk = risk_engine.assess_risk(address, chain, label, blockchain_info, analysis)

        message = format_risk_message(risk, label)
        self.assertIsInstance(message, str)
        self.assertIn("风险评级报告", message)
        self.assertIn("综合评分", message)
        self.assertIn("评估建议", message)

    def test_format_profile_message(self):
        """测试格式化个人资料消息"""
        from bot import format_profile_message
        from models import get_db_context, User, UserTier

        with get_db_context() as db:
            user = db.query(User).filter(User.telegram_id == 123456789).first()
            self.assertIsNotNone(user)

            message = format_profile_message(user)
            self.assertIsInstance(message, str)
            self.assertIn("个人中心", message)
            self.assertIn("会员等级", message)
            self.assertIn("年卡会员", message)

    def test_format_subscribe_message(self):
        """测试格式化订阅消息"""
        from bot import format_subscribe_message

        message = format_subscribe_message()
        self.assertIsInstance(message, str)
        self.assertIn("会员订阅计划", message)
        self.assertIn("免费版", message)
        self.assertIn("月卡会员", message)
        self.assertIn("年卡会员", message)
        self.assertIn("专业版", message)

    def test_format_batch_result(self):
        """测试格式化批量查询结果"""
        from bot import format_batch_result

        results = [
            {
                "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
                "label": type('obj', (object,), {'label': 'Binance'})(),
                "risk_assessment": {
                    "risk_emoji": "🟢",
                    "risk_name": "低风险",
                    "risk_score": 85.5,
                },
            },
            {
                "address": "0x1234567890123456789012345678901234567890",
                "error": "查询失败",
            },
        ]

        message = format_batch_result(results)
        self.assertIsInstance(message, str)
        self.assertIn("批量查询结果", message)
        self.assertIn("Binance", message)
        self.assertIn("查询失败", message)


class TestBotCommands(unittest.TestCase):
    """测试Bot命令处理"""

    def test_validate_address(self):
        """测试地址验证"""
        from bot import validate_address

        # 有效地址
        is_valid, chain = validate_address("0x28C6c06298d514Db089934071355E5743bf21d60")
        self.assertTrue(is_valid)
        self.assertEqual(chain, "ethereum")

        is_valid, chain = validate_address("TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE")
        self.assertTrue(is_valid)
        self.assertEqual(chain, "tron")

        # 无效地址
        is_valid, chain = validate_address("invalid_address")
        self.assertFalse(is_valid)
        self.assertIsNone(chain)

        # 空地址
        is_valid, chain = validate_address("")
        self.assertFalse(is_valid)
        self.assertIsNone(chain)


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("WalletLabel Bot 全面测试")
    print("=" * 70)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestBlockchainAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestLabelEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestBotUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestBotCommands))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试结果摘要
    print("\n" + "=" * 70)
    print("测试结果摘要")
    print("=" * 70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 70)

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  ❌ {test}")
            print(f"     {traceback.splitlines()[-1]}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  ❌ {test}")
            print(f"     {traceback.splitlines()[-1]}")

    print("=" * 70)

    # 返回是否全部通过
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
