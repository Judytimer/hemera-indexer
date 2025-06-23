import logging
from typing import List

from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.dex_events.dex_abi import (
    SWAP_EVENT, 
    SWAP_V3_EVENT
)
from indexer.modules.custom.dex_events.domain.dex_events import DexSwapEvent
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportDexSwapEventJob(FilterTransactionDataJob):
    """抓取DEX交易事件的作业"""
    dependency_types = [Log]
    output_types = [DexSwapEvent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pool_addresses = kwargs.get('pool_addresses', [])  # 可选的池地址过滤器

    def get_filter(self):
        """获取事件过滤器"""
        topics = [
            SWAP_EVENT.get_signature(),
            SWAP_V3_EVENT.get_signature(),
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
            swap_event = None
            
            try:
                if log.topic0 == SWAP_EVENT.get_signature():
                    # Uniswap V2 style Swap event
                    decoded_dict = SWAP_EVENT.decode_log(log)
                    swap_event = DexSwapEvent(
                        pool_address=log.address,
                        sender=decoded_dict["sender"],
                        to_address=decoded_dict["to"],
                        amount0_in=decoded_dict["amount0In"],
                        amount1_in=decoded_dict["amount1In"],
                        amount0_out=decoded_dict["amount0Out"],
                        amount1_out=decoded_dict["amount1Out"],
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                        event_type="swap_v2"
                    )
                    
                elif log.topic0 == SWAP_V3_EVENT.get_signature():
                    # Uniswap V3 style Swap event
                    decoded_dict = SWAP_V3_EVENT.decode_log(log)
                    swap_event = DexSwapEvent(
                        pool_address=log.address,
                        sender=decoded_dict["sender"],
                        to_address=decoded_dict["recipient"],
                        amount0=decoded_dict["amount0"],
                        amount1=decoded_dict["amount1"],
                        sqrt_price_x96=decoded_dict["sqrtPriceX96"],
                        liquidity=decoded_dict["liquidity"],
                        tick=decoded_dict["tick"],
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                        event_type="swap_v3"
                    )

                if swap_event:
                    self._collect_domain(swap_event)
                    logger.debug(f"Processed {swap_event.event_type} event at {log.address}")
                    
            except Exception as e:
                logger.error(f"Error processing swap event in log {log.transaction_hash}:{log.log_index}: {e}")
                continue 