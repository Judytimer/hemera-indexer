import logging
from typing import List

from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.dex_events.dex_abi import (
    MINT_EVENT, 
    MINT_V3_EVENT,
    BURN_EVENT,
    BURN_V3_EVENT
)
from indexer.modules.custom.dex_events.domain.dex_events import DexMintEvent, DexBurnEvent
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportDexLiquidityEventJob(FilterTransactionDataJob):
    """抓取DEX流动性事件（Mint/Burn）的作业"""
    dependency_types = [Log]
    output_types = [DexMintEvent, DexBurnEvent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pool_addresses = kwargs.get('pool_addresses', [])  # 可选的池地址过滤器

    def get_filter(self):
        """获取事件过滤器"""
        topics = [
            MINT_EVENT.get_signature(),
            MINT_V3_EVENT.get_signature(),
            BURN_EVENT.get_signature(),
            BURN_V3_EVENT.get_signature(),
        ]
        
        filters = [TopicSpecification(topics=topics)]
        
        # 如果指定了池地址，添加地址过滤器
        if self.pool_addresses:
            from indexer.specification.specification import AddressSpecification
            filters.append(AddressSpecification(addresses=self.pool_addresses))
        
        return TransactionFilterByLogs(filters)

    def _process(self, **kwargs):
        """处理日志数据"""
        logs = self._data_buff[Log.type()]
        
        for log in logs:
            event = None
            
            try:
                if log.topic0 == MINT_EVENT.get_signature():
                    # Uniswap V2 style Mint event
                    decoded_dict = MINT_EVENT.decode_log(log)
                    event = DexMintEvent(
                        pool_address=log.address,
                        sender=decoded_dict["sender"],
                        amount0=decoded_dict["amount0"],
                        amount1=decoded_dict["amount1"],
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                        event_type="mint_v2"
                    )
                    
                elif log.topic0 == MINT_V3_EVENT.get_signature():
                    # Uniswap V3 style Mint event
                    decoded_dict = MINT_V3_EVENT.decode_log(log)
                    event = DexMintEvent(
                        pool_address=log.address,
                        sender=decoded_dict["sender"],
                        owner=decoded_dict["owner"],
                        amount0=decoded_dict["amount0"],
                        amount1=decoded_dict["amount1"],
                        tick_lower=decoded_dict["tickLower"],
                        tick_upper=decoded_dict["tickUpper"],
                        amount=decoded_dict["amount"],
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                        event_type="mint_v3"
                    )
                    
                elif log.topic0 == BURN_EVENT.get_signature():
                    # Uniswap V2 style Burn event
                    decoded_dict = BURN_EVENT.decode_log(log)
                    event = DexBurnEvent(
                        pool_address=log.address,
                        sender=decoded_dict["sender"],
                        to_address=decoded_dict["to"],
                        amount0=decoded_dict["amount0"],
                        amount1=decoded_dict["amount1"],
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                        event_type="burn_v2"
                    )
                    
                elif log.topic0 == BURN_V3_EVENT.get_signature():
                    # Uniswap V3 style Burn event
                    decoded_dict = BURN_V3_EVENT.decode_log(log)
                    event = DexBurnEvent(
                        pool_address=log.address,
                        sender=log.address,  # In V3, sender is usually the pool itself
                        owner=decoded_dict["owner"],
                        amount0=decoded_dict["amount0"],
                        amount1=decoded_dict["amount1"],
                        tick_lower=decoded_dict["tickLower"],
                        tick_upper=decoded_dict["tickUpper"],
                        amount=decoded_dict["amount"],
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                        event_type="burn_v3"
                    )

                if event:
                    self._collect_domain(event)
                    logger.debug(f"Processed {event.event_type} event at {log.address}")
                    
            except Exception as e:
                logger.error(f"Error processing liquidity event in log {log.transaction_hash}:{log.log_index}: {e}")
                continue 