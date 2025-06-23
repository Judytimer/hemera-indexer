from dataclasses import dataclass
from typing import Optional

from indexer.domain import FilterData


@dataclass
class DexSwapEvent(FilterData):
    """DEX交易事件"""
    pool_address: str
    sender: str
    to_address: str
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    event_type: str = "swap"  # "swap_v2" or "swap_v3"
    # V2 style amounts
    amount0_in: Optional[int] = None
    amount1_in: Optional[int] = None
    amount0_out: Optional[int] = None
    amount1_out: Optional[int] = None
    # V3 style amounts (can be negative)
    amount0: Optional[int] = None
    amount1: Optional[int] = None
    # V3 specific fields
    sqrt_price_x96: Optional[int] = None
    liquidity: Optional[int] = None
    tick: Optional[int] = None


@dataclass
class DexMintEvent(FilterData):
    """DEX添加流动性事件"""
    pool_address: str
    sender: str
    amount0: int
    amount1: int
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    event_type: str = "mint"  # "mint_v2" or "mint_v3"
    owner: Optional[str] = None  # V3 style
    # V3 specific fields
    tick_lower: Optional[int] = None
    tick_upper: Optional[int] = None
    amount: Optional[int] = None  # V3 liquidity amount


@dataclass
class DexBurnEvent(FilterData):
    """DEX移除流动性事件"""
    pool_address: str
    sender: str
    amount0: int
    amount1: int
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    event_type: str = "burn"  # "burn_v2" or "burn_v3"
    to_address: Optional[str] = None  # V2 style
    owner: Optional[str] = None  # V3 style
    # V3 specific fields
    tick_lower: Optional[int] = None
    tick_upper: Optional[int] = None
    amount: Optional[int] = None  # V3 liquidity amount


@dataclass
class DexPairCreatedEvent(FilterData):
    """DEX交易对创建事件"""
    factory_address: str
    token0: str
    token1: str
    pair_address: str
    pair_index: int
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    event_type: str = "pair_created" 