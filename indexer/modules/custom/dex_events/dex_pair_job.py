import logging
from typing import List

from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.dex_events.dex_abi import PAIR_CREATED_EVENT
from indexer.modules.custom.dex_events.domain.dex_events import DexPairCreatedEvent
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportDexPairCreatedEventJob(FilterTransactionDataJob):
    """抓取DEX交易对创建事件的作业"""
    dependency_types = [Log]
    output_types = [DexPairCreatedEvent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.factory_addresses = kwargs.get('factory_addresses', [])  # 可选的工厂地址过滤器

    def get_filter(self):
        """获取事件过滤器"""
        topics = [PAIR_CREATED_EVENT.get_signature()]
        filters = [TopicSpecification(topics=topics)]
        
        # 如果指定了工厂地址，添加地址过滤器
        if self.factory_addresses:
            from indexer.specification.specification import AddressSpecification
            filters.append(AddressSpecification(addresses=self.factory_addresses))
        
        return TransactionFilterByLogs(filters)

    def _process(self, **kwargs):
        """处理日志数据"""
        logs = self._data_buff[Log.type()]
        
        for log in logs:
            try:
                if log.topic0 == PAIR_CREATED_EVENT.get_signature():
                    decoded_dict = PAIR_CREATED_EVENT.decode_log(log)
                    
                    pair_created_event = DexPairCreatedEvent(
                        factory_address=log.address,
                        token0=decoded_dict["token0"],
                        token1=decoded_dict["token1"],
                        pair_address=decoded_dict["pair"],
                        pair_index=decoded_dict.get("", 0),  # 有些实现可能没有命名这个参数
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        log_index=log.log_index,
                        event_type="pair_created"
                    )
                    
                    self._collect_domain(pair_created_event)
                    logger.debug(f"Processed pair created event: {decoded_dict['token0']}/{decoded_dict['token1']} -> {decoded_dict['pair']}")
                    
            except Exception as e:
                logger.error(f"Error processing pair created event in log {log.transaction_hash}:{log.log_index}: {e}")
                continue 