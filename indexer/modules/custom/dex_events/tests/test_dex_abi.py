import pytest
from indexer.modules.custom.dex_events.dex_abi import (
    SWAP_EVENT, 
    SWAP_V3_EVENT,
    MINT_EVENT,
    MINT_V3_EVENT,
    BURN_EVENT,
    BURN_V3_EVENT,
    PAIR_CREATED_EVENT
)


class TestDexABI:
    """DEX ABI事件定义测试"""

    def test_swap_event_signature(self):
        """测试Swap事件签名"""
        signature = SWAP_EVENT.get_signature()
        assert signature is not None
        assert signature.startswith("0x")
        assert len(signature) == 66  # 0x + 64 characters

    def test_swap_v3_event_signature(self):
        """测试Swap V3事件签名"""
        signature = SWAP_V3_EVENT.get_signature()
        assert signature is not None
        assert signature.startswith("0x")
        assert len(signature) == 66

    def test_mint_event_signature(self):
        """测试Mint事件签名"""
        signature = MINT_EVENT.get_signature()
        assert signature is not None
        assert signature.startswith("0x")
        assert len(signature) == 66

    def test_mint_v3_event_signature(self):
        """测试Mint V3事件签名"""
        signature = MINT_V3_EVENT.get_signature()
        assert signature is not None
        assert signature.startswith("0x")
        assert len(signature) == 66

    def test_burn_event_signature(self):
        """测试Burn事件签名"""
        signature = BURN_EVENT.get_signature()
        assert signature is not None
        assert signature.startswith("0x")
        assert len(signature) == 66

    def test_burn_v3_event_signature(self):
        """测试Burn V3事件签名"""
        signature = BURN_V3_EVENT.get_signature()
        assert signature is not None
        assert signature.startswith("0x")
        assert len(signature) == 66

    def test_pair_created_event_signature(self):
        """测试PairCreated事件签名"""
        signature = PAIR_CREATED_EVENT.get_signature()
        assert signature is not None
        assert signature.startswith("0x")
        assert len(signature) == 66

    def test_all_signatures_unique(self):
        """测试所有事件签名都是唯一的"""
        signatures = [
            SWAP_EVENT.get_signature(),
            SWAP_V3_EVENT.get_signature(),
            MINT_EVENT.get_signature(),
            MINT_V3_EVENT.get_signature(),
            BURN_EVENT.get_signature(),
            BURN_V3_EVENT.get_signature(),
            PAIR_CREATED_EVENT.get_signature()
        ]
        
        # 所有签名应该是唯一的
        assert len(signatures) == len(set(signatures))

    def test_event_names(self):
        """测试事件名称正确"""
        assert SWAP_EVENT.event_name == "Swap"
        assert SWAP_V3_EVENT.event_name == "Swap"
        assert MINT_EVENT.event_name == "Mint"
        assert MINT_V3_EVENT.event_name == "Mint"
        assert BURN_EVENT.event_name == "Burn"
        assert BURN_V3_EVENT.event_name == "Burn"
        assert PAIR_CREATED_EVENT.event_name == "PairCreated"

    def test_swap_event_inputs(self):
        """测试Swap事件输入参数"""
        inputs = SWAP_EVENT.inputs
        expected_params = {"sender", "amount0In", "amount1In", "amount0Out", "amount1Out", "to"}
        actual_params = {input_param['name'] for input_param in inputs}
        assert expected_params.issubset(actual_params)

    def test_swap_v3_event_inputs(self):
        """测试Swap V3事件输入参数"""
        inputs = SWAP_V3_EVENT.inputs
        expected_params = {"sender", "recipient", "amount0", "amount1", "sqrtPriceX96", "liquidity", "tick"}
        actual_params = {input_param['name'] for input_param in inputs}
        assert expected_params.issubset(actual_params)

    def test_pair_created_event_inputs(self):
        """测试PairCreated事件输入参数"""
        inputs = PAIR_CREATED_EVENT.inputs
        expected_params = {"token0", "token1", "pair"}
        actual_params = {input_param['name'] for input_param in inputs}
        assert expected_params.issubset(actual_params) 