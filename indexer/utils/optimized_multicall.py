#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
优化的RPC批量调用处理器
Optimized RPC batch call processor
"""

import asyncio
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Dict, List, Optional, Set, Tuple
from functools import lru_cache
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from indexer.utils.multicall_hemera.call import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper


class OptimizedMultiCallHelper(MultiCallHelper):
    """优化的多重调用帮助器"""
    
    def __init__(self, web3, kwargs=None, logger=None):
        super().__init__(web3, kwargs, logger)
        self.kwargs = kwargs or {}
        
        # 优化的配置参数
        self.batch_size = min(self.kwargs.get("batch_size", 500), 1000)  # 增大批量大小
        self.max_workers = min(self.kwargs.get("max_workers", 20), 50)   # 增加工作线程数
        self.timeout = self.kwargs.get("timeout", 30)
        self.retry_attempts = self.kwargs.get("retry_attempts", 3)
        
        # 请求去重缓存
        self._request_cache: Dict[str, any] = {}
        self._cache_lock = Lock()
        
        # 连接池优化
        self._setup_connection_pool()
        
        # 性能监控
        self._performance_stats = {
            'total_requests': 0,
            'cached_requests': 0,
            'failed_requests': 0,
            'total_time': 0
        }
        
    def _setup_connection_pool(self):
        """设置优化的HTTP连接池"""
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        # 配置连接池适配器
        adapter = HTTPAdapter(
            pool_connections=20,
            pool_maxsize=50,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _generate_cache_key(self, call: Call) -> str:
        """生成请求缓存键"""
        return f"{call.target}:{call.data}:{call.block_number}"
    
    def _deduplicate_calls(self, calls: List[Call]) -> Tuple[List[Call], Dict[str, Call]]:
        """
        去除重复的RPC调用
        返回: (去重后的调用列表, 重复调用映射)
        """
        seen: Set[str] = set()
        deduplicated: List[Call] = []
        duplicate_map: Dict[str, Call] = {}
        
        for call in calls:
            cache_key = self._generate_cache_key(call)
            
            if cache_key not in seen:
                seen.add(cache_key)
                deduplicated.append(call)
            else:
                # 记录重复的调用，稍后复用结果
                duplicate_map[cache_key] = call
                
        return deduplicated, duplicate_map
    
    @lru_cache(maxsize=10000)
    def _get_cached_result(self, cache_key: str):
        """获取缓存的结果"""
        return self._request_cache.get(cache_key)
    
    def _cache_result(self, cache_key: str, result):
        """缓存结果"""
        with self._cache_lock:
            # 限制缓存大小
            if len(self._request_cache) > 50000:
                # 清理最旧的一半缓存
                keys_to_remove = list(self._request_cache.keys())[:25000]
                for key in keys_to_remove:
                    del self._request_cache[key]
            
            self._request_cache[cache_key] = result
    
    def execute_calls_optimized(self, calls: List[Call]) -> List[Call]:
        """
        优化的批量执行调用
        """
        start_time = time.time()
        
        try:
            # 去重复请求
            deduplicated_calls, duplicate_map = self._deduplicate_calls(calls)
            
            self.logger.info(f"原始请求数: {len(calls)}, 去重后: {len(deduplicated_calls)}")
            
            # 动态调整批量大小
            optimal_batch_size = self._calculate_optimal_batch_size(len(deduplicated_calls))
            
            # 并行处理批次
            self._process_batches_parallel(deduplicated_calls, optimal_batch_size)
            
            # 恢复重复请求的结果
            self._restore_duplicate_results(calls, duplicate_map)
            
            # 更新性能统计
            self._update_performance_stats(len(calls), len(deduplicated_calls), time.time() - start_time)
            
            return calls
            
        except Exception as e:
            self.logger.error(f"批量执行调用失败: {e}")
            self._performance_stats['failed_requests'] += len(calls)
            raise
    
    def _calculate_optimal_batch_size(self, total_calls: int) -> int:
        """根据调用数量动态计算最优批量大小"""
        if total_calls <= 100:
            return min(50, total_calls)
        elif total_calls <= 1000:
            return min(200, total_calls)
        else:
            return min(self.batch_size, total_calls)
    
    def _process_batches_parallel(self, calls: List[Call], batch_size: int):
        """并行处理批次"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i in range(0, len(calls), batch_size):
                batch = calls[i:i + batch_size]
                future = executor.submit(self._process_batch_with_retry, batch)
                futures.append(future)
            
            # 等待所有批次完成
            for future in as_completed(futures, timeout=self.timeout * 2):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"批次处理失败: {e}")
    
    def _process_batch_with_retry(self, batch: List[Call]) -> bool:
        """带重试的批次处理"""
        for attempt in range(self.retry_attempts):
            try:
                # 检查缓存
                cached_results = self._check_batch_cache(batch)
                if cached_results:
                    self._apply_cached_results(batch, cached_results)
                    return True
                
                # 执行批次调用
                results = self._execute_batch_call(batch)
                
                # 缓存结果
                self._cache_batch_results(batch, results)
                
                return True
                
            except Exception as e:
                self.logger.warning(f"批次处理尝试 {attempt + 1} 失败: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数退避
        
        return False
    
    def _check_batch_cache(self, batch: List[Call]) -> Optional[List]:
        """检查批次缓存"""
        cached_results = []
        for call in batch:
            cache_key = self._generate_cache_key(call)
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                cached_results.append(cached_result)
            else:
                return None  # 如果有任何调用未缓存，返回None
        return cached_results
    
    def _apply_cached_results(self, batch: List[Call], cached_results: List):
        """应用缓存的结果"""
        for call, result in zip(batch, cached_results):
            call.result = result
        self._performance_stats['cached_requests'] += len(batch)
    
    def _execute_batch_call(self, batch: List[Call]) -> List:
        """执行批次调用"""
        # 这里调用原有的批量执行逻辑
        # 具体实现取决于原有的MultiCallHelper的实现
        return super().execute_calls(batch)
    
    def _cache_batch_results(self, batch: List[Call], results: List):
        """缓存批次结果"""
        for call, result in zip(batch, results):
            cache_key = self._generate_cache_key(call)
            self._cache_result(cache_key, result)
    
    def _restore_duplicate_results(self, original_calls: List[Call], duplicate_map: Dict[str, Call]):
        """恢复重复请求的结果"""
        for call in original_calls:
            cache_key = self._generate_cache_key(call)
            if cache_key in duplicate_map and not hasattr(call, 'result'):
                # 找到已处理的相同请求的结果
                for processed_call in original_calls:
                    if (self._generate_cache_key(processed_call) == cache_key and 
                        hasattr(processed_call, 'result')):
                        call.result = processed_call.result
                        break
    
    def _update_performance_stats(self, total_calls: int, processed_calls: int, execution_time: float):
        """更新性能统计"""
        self._performance_stats['total_requests'] += total_calls
        self._performance_stats['total_time'] += execution_time
        
        # 定期输出性能报告
        if self._performance_stats['total_requests'] % 10000 == 0:
            self._log_performance_report()
    
    def _log_performance_report(self):
        """输出性能报告"""
        stats = self._performance_stats
        avg_time = stats['total_time'] / max(stats['total_requests'], 1)
        cache_hit_rate = stats['cached_requests'] / max(stats['total_requests'], 1) * 100
        
        self.logger.info(
            f"RPC性能报告 - "
            f"总请求: {stats['total_requests']}, "
            f"缓存命中率: {cache_hit_rate:.1f}%, "
            f"平均执行时间: {avg_time:.3f}s, "
            f"失败请求: {stats['failed_requests']}"
        )
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return self._performance_stats.copy()
    
    def clear_cache(self):
        """清理缓存"""
        with self._cache_lock:
            self._request_cache.clear()
        self._get_cached_result.cache_clear()
        self.logger.info("RPC缓存已清理")


# 异步版本的多重调用帮助器
class AsyncOptimizedMultiCallHelper:
    """异步优化的多重调用帮助器"""
    
    def __init__(self, web3, kwargs=None, logger=None):
        self.web3 = web3
        self.kwargs = kwargs or {}
        self.logger = logger or logging.getLogger(__name__)
        
        self.batch_size = self.kwargs.get("batch_size", 500)
        self.max_concurrent = self.kwargs.get("max_concurrent", 20)
        self.timeout = self.kwargs.get("timeout", 30)
        
    async def execute_calls_async(self, calls: List[Call]) -> List[Call]:
        """异步执行调用"""
        # 创建异步任务
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_batch(batch):
            async with semaphore:
                return await self._process_batch_async(batch)
        
        # 分批处理
        tasks = []
        for i in range(0, len(calls), self.batch_size):
            batch = calls[i:i + self.batch_size]
            task = asyncio.create_task(process_batch(batch))
            tasks.append(task)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        return calls
    
    async def _process_batch_async(self, batch: List[Call]):
        """异步处理批次"""
        loop = asyncio.get_event_loop()
        
        # 在线程池中执行同步的RPC调用
        await loop.run_in_executor(
            None, 
            self._execute_sync_batch, 
            batch
        )
    
    def _execute_sync_batch(self, batch: List[Call]):
        """在线程池中执行同步批次"""
        # 这里可以复用OptimizedMultiCallHelper的逻辑
        helper = OptimizedMultiCallHelper(self.web3, self.kwargs, self.logger)
        return helper._execute_batch_call(batch)