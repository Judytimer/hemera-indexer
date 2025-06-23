import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from indexer.domain.log import Log
from indexer.modules.custom.dex_events.dex_swap_job import ExportDexSwapEventJob
from indexer.modules.custom.dex_events.dex_liquidity_job import ExportDexLiquidityEventJob
from indexer.modules.custom.dex_events.dex_pair_job import ExportDexPairCreatedEventJob
from indexer.modules.custom.dex_events.dex_abi import SWAP_EVENT, MINT_EVENT, PAIR_CREATED_EVENT
from indexer.modules.custom.dex_events.domain.dex_events import DexSwapEvent, DexMintEvent, DexPairCreatedEvent
from indexer.exporters.console_item_exporter import ConsoleItemExporter


class TestDexJobs:
    """DEX作业测试"""

    def setup_method(self):
        """测试设置"""
        self.mock_web3 = Mock()
        self.mock_exporter = ConsoleItemExporter()

    def create_mock_log(self, address, topic0, topics=None, data=None, block_number=18000000, log_index=1):
        """创建模拟日志"""
        log = Log()
        log.address = address
        log.topic0 = topic0
        log.topics = topics or [topic0]
        log.data = data or "0x"
        log.block_number = block_number
        log.block_timestamp = datetime.now()
        log.transaction_hash = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
        log.log_index = log_index
        return log

    def test_export_dex_swap_job_creation(self):
        """测试ExportDexSwapEventJob创建"""
        job = ExportDexSwapEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter],
            batch_size=100,
            max_workers=5
        )
        
        assert job is not None
        assert DexSwapEvent in job.output_types
        assert Log in job.dependency_types

    def test_export_dex_liquidity_job_creation(self):
        """测试ExportDexLiquidityEventJob创建"""
        job = ExportDexLiquidityEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter],
            batch_size=100,
            max_workers=5
        )
        
        assert job is not None
        assert DexMintEvent in job.output_types
        # DexBurnEvent should also be in output_types

    def test_export_dex_pair_job_creation(self):
        """测试ExportDexPairCreatedEventJob创建"""
        factory_addresses = ["0x1234567890123456789012345678901234567890"]
        job = ExportDexPairCreatedEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter],
            batch_size=100,
            max_workers=5,
            factory_addresses=factory_addresses
        )
        
        assert job is not None
        assert DexPairCreatedEvent in job.output_types
        assert job.factory_addresses == factory_addresses

    def test_swap_job_get_filter(self):
        """测试Swap作业的过滤器"""
        job = ExportDexSwapEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        filter_obj = job.get_filter()
        assert filter_obj is not None

    def test_liquidity_job_get_filter(self):
        """测试流动性作业的过滤器"""
        job = ExportDexLiquidityEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        filter_obj = job.get_filter()
        assert filter_obj is not None

    def test_pair_job_get_filter(self):
        """测试交易对作业的过滤器"""
        job = ExportDexPairCreatedEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        filter_obj = job.get_filter()
        assert filter_obj is not None

    @patch('indexer.modules.custom.dex_events.dex_abi.SWAP_EVENT.decode_log')
    def test_swap_job_process_with_mock_data(self, mock_decode):
        """测试Swap作业处理模拟数据"""
        # 设置模拟解码结果
        mock_decode.return_value = {
            "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "to": "0x9876543210987654321098765432109876543210",
            "amount0In": 1000000,
            "amount1In": 0,
            "amount0Out": 0,
            "amount1Out": 2000000
        }
        
        # 创建作业
        job = ExportDexSwapEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        # 创建模拟日志
        mock_log = self.create_mock_log(
            address="0x1234567890123456789012345678901234567890",
            topic0=SWAP_EVENT.get_signature()
        )
        
        # 设置数据缓冲区
        job._data_buff = {Log.type(): [mock_log]}
        
        # 处理数据
        job._process()
        
        # 验证解码被调用
        mock_decode.assert_called_once_with(mock_log)

    @patch('indexer.modules.custom.dex_events.dex_abi.MINT_EVENT.decode_log')
    def test_liquidity_job_process_with_mock_data(self, mock_decode):
        """测试流动性作业处理模拟数据"""
        # 设置模拟解码结果
        mock_decode.return_value = {
            "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "amount0": 1000000,
            "amount1": 2000000
        }
        
        # 创建作业
        job = ExportDexLiquidityEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        # 创建模拟日志
        mock_log = self.create_mock_log(
            address="0x1234567890123456789012345678901234567890",
            topic0=MINT_EVENT.get_signature()
        )
        
        # 设置数据缓冲区
        job._data_buff = {Log.type(): [mock_log]}
        
        # 处理数据
        job._process()
        
        # 验证解码被调用
        mock_decode.assert_called_once_with(mock_log)

    @patch('indexer.modules.custom.dex_events.dex_abi.PAIR_CREATED_EVENT.decode_log')
    def test_pair_job_process_with_mock_data(self, mock_decode):
        """测试交易对作业处理模拟数据"""
        # 设置模拟解码结果
        mock_decode.return_value = {
            "token0": "0xA0b86a33E6441c8C0527ef632a4C4Cf3e6A5a74A",
            "token1": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "pair": "0x9876543210987654321098765432109876543210",
            "": 1000  # unnamed parameter
        }
        
        # 创建作业
        job = ExportDexPairCreatedEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        # 创建模拟日志
        mock_log = self.create_mock_log(
            address="0x1234567890123456789012345678901234567890",
            topic0=PAIR_CREATED_EVENT.get_signature()
        )
        
        # 设置数据缓冲区
        job._data_buff = {Log.type(): [mock_log]}
        
        # 处理数据
        job._process()
        
        # 验证解码被调用
        mock_decode.assert_called_once_with(mock_log)

    def test_swap_job_with_pool_addresses_filter(self):
        """测试带池地址过滤器的Swap作业"""
        pool_addresses = ["0x1234567890123456789012345678901234567890"]
        job = ExportDexSwapEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter],
            pool_addresses=pool_addresses
        )
        
        assert job.pool_addresses == pool_addresses
        filter_obj = job.get_filter()
        assert filter_obj is not None

    def test_pair_job_with_factory_addresses_filter(self):
        """测试带工厂地址过滤器的交易对作业"""
        factory_addresses = ["0x1234567890123456789012345678901234567890"]
        job = ExportDexPairCreatedEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter],
            factory_addresses=factory_addresses
        )
        
        assert job.factory_addresses == factory_addresses
        filter_obj = job.get_filter()
        assert filter_obj is not None

    def test_jobs_error_handling(self):
        """测试作业错误处理"""
        job = ExportDexSwapEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        # 创建无效的日志（缺少必要数据）
        mock_log = self.create_mock_log(
            address="0x1234567890123456789012345678901234567890",
            topic0="0xinvalid_topic"  # 无效的topic
        )
        
        # 设置数据缓冲区
        job._data_buff = {Log.type(): [mock_log]}
        
        # 处理应该不会抛出异常
        try:
            job._process()
        except Exception as e:
            pytest.fail(f"Job should handle errors gracefully, but got: {e}")

    def test_job_inheritance(self):
        """测试作业继承关系"""
        from indexer.jobs.base_job import FilterTransactionDataJob
        
        swap_job = ExportDexSwapEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        liquidity_job = ExportDexLiquidityEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        pair_job = ExportDexPairCreatedEventJob(
            batch_web3_provider=self.mock_web3,
            item_exporters=[self.mock_exporter]
        )
        
        # 所有作业都应该继承自FilterTransactionDataJob
        assert isinstance(swap_job, FilterTransactionDataJob)
        assert isinstance(liquidity_job, FilterTransactionDataJob)
        assert isinstance(pair_job, FilterTransactionDataJob) 