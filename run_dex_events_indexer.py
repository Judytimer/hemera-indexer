#!/usr/bin/env python3
"""
DEX Events Indexer 启动脚本
抓取Swap、Mint/Burn和PairCreated事件
"""

import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy
from indexer.modules.custom.dex_events.domain.dex_events import DexSwapEvent, DexMintEvent, DexBurnEvent, DexPairCreatedEvent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dex_events_indexer.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info("🚀 启动 DEX Events Indexer")
        
        # 区块链配置 - 使用测试网以便快速验证
        provider_uri = "https://sepolia.base.org"  # Base Sepolia testnet
        
        # 创建Web3提供者
        batch_web3_provider = ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True))
        batch_web3_debug_provider = ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True))
        
        # 创建导出器
        exporter = ConsoleItemExporter()
        
        # 定义要输出的数据类型
        required_output_types = [
            DexSwapEvent,
            DexMintEvent, 
            DexBurnEvent,
            DexPairCreatedEvent
        ]
        
        # 创建调度器
        logger.info("⚙️ 创建作业调度器")
        scheduler = JobScheduler(
            batch_web3_provider=batch_web3_provider,
            batch_web3_debug_provider=batch_web3_debug_provider,
            item_exporters=[exporter],
            batch_size=10,  # 使用较小的批次进行测试
            max_workers=2,
            required_output_types=required_output_types,
            config={}
        )
        
        # 启动索引器
        logger.info("🎯 启动 DEX 事件索引器...")
        logger.info("监控的事件类型:")
        logger.info("  - Swap (交易事件)")
        logger.info("  - Mint/Burn (流动性事件)")
        logger.info("  - PairCreated (交易对创建事件)")
        
        # 运行最近的几个区块进行测试
        logger.info("📋 开始处理区块（测试模式）...")
        start_block = 18000000  # Base Sepolia的一个相对较新的区块
        end_block = start_block + 5  # 只处理5个区块进行测试
        
        scheduler.run_jobs(start_block=start_block, end_block=end_block)
        
        # 显示处理结果
        data_buff = scheduler.get_data_buff()
        logger.info("📊 处理结果统计:")
        for output_type in required_output_types:
            count = len(data_buff.get(output_type.type(), []))
            logger.info(f"  - {output_type.type()}: {count} 条记录")
        
    except KeyboardInterrupt:
        logger.info("👋 收到中断信号，正在停止索引器...")
    except Exception as e:
        logger.error(f"❌ 索引器运行出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        logger.info("🛑 DEX Events Indexer 已停止")


if __name__ == "__main__":
    main() 