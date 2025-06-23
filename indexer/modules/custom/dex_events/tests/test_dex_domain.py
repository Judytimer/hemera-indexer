import pytest
from datetime import datetime
from indexer.modules.custom.dex_events.domain.dex_events import (
    DexSwapEvent,
    DexMintEvent, 
    DexBurnEvent,
    DexPairCreatedEvent
)


class TestDexDomainModels:
    """DEX domain模型测试"""

    def test_dex_swap_event_creation(self):
        """测试DexSwapEvent创建"""
        event = DexSwapEvent(
            pool_address="0x1234567890123456789012345678901234567890",
            sender="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            to_address="0x9876543210987654321098765432109876543210",
            amount0_in=1000000,
            amount1_in=0,
            amount0_out=0,
            amount1_out=2000000,
            block_number=18000000,
            block_timestamp=datetime.now(),
            transaction_hash="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            log_index=1,
            event_type="swap_v2"
        )
        
        assert event.pool_address == "0x1234567890123456789012345678901234567890"
        assert event.sender == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        assert event.amount0_in == 1000000
        assert event.amount1_out == 2000000
        assert event.event_type == "swap_v2"
        assert event.block_number == 18000000

    def test_dex_swap_event_v3_creation(self):
        """测试DexSwapEvent V3格式创建"""
        event = DexSwapEvent(
            pool_address="0x1234567890123456789012345678901234567890",
            sender="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            to_address="0x9876543210987654321098765432109876543210",
            amount0=-1000000,  # V3可以是负数
            amount1=2000000,
            sqrt_price_x96=79228162514264337593543950336,
            liquidity=1000000000000000000,
            tick=-276324,
            block_number=18000000,
            block_timestamp=datetime.now(),
            transaction_hash="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            log_index=2,
            event_type="swap_v3"
        )
        
        assert event.amount0 == -1000000
        assert event.amount1 == 2000000
        assert event.sqrt_price_x96 == 79228162514264337593543950336
        assert event.liquidity == 1000000000000000000
        assert event.tick == -276324
        assert event.event_type == "swap_v3"

    def test_dex_mint_event_creation(self):
        """测试DexMintEvent创建"""
        event = DexMintEvent(
            pool_address="0x1234567890123456789012345678901234567890",
            sender="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            amount0=1000000,
            amount1=2000000,
            block_number=18000000,
            block_timestamp=datetime.now(),
            transaction_hash="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            log_index=3,
            event_type="mint_v2"
        )
        
        assert event.pool_address == "0x1234567890123456789012345678901234567890"
        assert event.sender == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        assert event.amount0 == 1000000
        assert event.amount1 == 2000000
        assert event.event_type == "mint_v2"

    def test_dex_mint_event_v3_creation(self):
        """测试DexMintEvent V3格式创建"""
        event = DexMintEvent(
            pool_address="0x1234567890123456789012345678901234567890",
            sender="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            owner="0x9876543210987654321098765432109876543210",
            amount0=1000000,
            amount1=2000000,
            tick_lower=-276400,
            tick_upper=-276300,
            amount=500000000000000000,
            block_number=18000000,
            block_timestamp=datetime.now(),
            transaction_hash="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            log_index=4,
            event_type="mint_v3"
        )
        
        assert event.owner == "0x9876543210987654321098765432109876543210"
        assert event.tick_lower == -276400
        assert event.tick_upper == -276300
        assert event.amount == 500000000000000000
        assert event.event_type == "mint_v3"

    def test_dex_burn_event_creation(self):
        """测试DexBurnEvent创建"""
        event = DexBurnEvent(
            pool_address="0x1234567890123456789012345678901234567890",
            sender="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            to_address="0x9876543210987654321098765432109876543210",
            amount0=800000,
            amount1=1600000,
            block_number=18000000,
            block_timestamp=datetime.now(),
            transaction_hash="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            log_index=5,
            event_type="burn_v2"
        )
        
        assert event.pool_address == "0x1234567890123456789012345678901234567890"
        assert event.to_address == "0x9876543210987654321098765432109876543210"
        assert event.amount0 == 800000
        assert event.amount1 == 1600000
        assert event.event_type == "burn_v2"

    def test_dex_pair_created_event_creation(self):
        """测试DexPairCreatedEvent创建"""
        event = DexPairCreatedEvent(
            factory_address="0x1234567890123456789012345678901234567890",
            token0="0xA0b86a33E6441c8C0527ef632a4C4Cf3e6A5a74A",
            token1="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            pair_address="0x9876543210987654321098765432109876543210",
            pair_index=1000,
            block_number=18000000,
            block_timestamp=datetime.now(),
            transaction_hash="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            log_index=6,
            event_type="pair_created"
        )
        
        assert event.factory_address == "0x1234567890123456789012345678901234567890"
        assert event.token0 == "0xA0b86a33E6441c8C0527ef632a4C4Cf3e6A5a74A"
        assert event.token1 == "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        assert event.pair_address == "0x9876543210987654321098765432109876543210"
        assert event.pair_index == 1000
        assert event.event_type == "pair_created"

    def test_domain_models_type_method(self):
        """测试domain模型的type()方法"""
        # 创建测试事件
        swap_event = DexSwapEvent(
            pool_address="0x1234567890123456789012345678901234567890",
            sender="0xabcd",
            to_address="0x9876",
            amount0_in=1000,
            amount1_in=0,
            amount0_out=0,
            amount1_out=2000,
            block_number=18000000,
            block_timestamp=datetime.now(),
            transaction_hash="0xdeadbeef",
            log_index=1,
            event_type="swap_v2"
        )
        
        # 测试type方法
        assert swap_event.type() == "DexSwapEvent"
        assert DexSwapEvent.type() == "DexSwapEvent"
        assert DexMintEvent.type() == "DexMintEvent"
        assert DexBurnEvent.type() == "DexBurnEvent"
        assert DexPairCreatedEvent.type() == "DexPairCreatedEvent" 