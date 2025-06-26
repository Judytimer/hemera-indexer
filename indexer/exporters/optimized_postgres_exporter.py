#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
优化的PostgreSQL批量导出器
Optimized PostgreSQL batch exporter
"""

import gc
import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from indexer.exporters.postgres_item_exporter import PostgresItemExporter
from common.services.postgresql_service import PostgreSQLService


class OptimizedPostgresItemExporter(PostgresItemExporter):
    """优化的PostgreSQL批量导出器"""
    
    def __init__(self, postgres_url: str, **kwargs):
        super().__init__(postgres_url, **kwargs)
        
        # 优化配置
        self.optimized_batch_size = kwargs.get('optimized_batch_size', 10000)  # 增大批量大小
        self.memory_threshold = kwargs.get('memory_threshold', 100000)  # 内存阈值
        self.enable_upsert = kwargs.get('enable_upsert', True)  # 启用UPSERT
        self.parallel_insert = kwargs.get('parallel_insert', True)  # 并行插入
        
        # 内存管理
        self._buffer = defaultdict(list)
        self._buffer_size = defaultdict(int)
        self._total_items = 0
        
        # 性能监控
        self._performance_stats = {
            'total_exported': 0,
            'batch_count': 0,
            'total_time': 0,
            'memory_flushes': 0
        }
        
        self.logger = logging.getLogger(__name__)
        
    def export_items_optimized(self, items: List[Any], **kwargs) -> None:
        """优化的批量导出方法"""
        start_time = time.time()
        
        try:
            # 按类型分组
            items_grouped = self._group_items_by_type(items)
            
            # 分批处理每个类型
            for item_type, item_list in items_grouped.items():
                if not item_list:
                    continue
                    
                self._process_item_type_optimized(item_type, item_list)
            
            # 更新性能统计
            execution_time = time.time() - start_time
            self._update_performance_stats(len(items), execution_time)
            
        except Exception as e:
            self.logger.error(f"优化导出失败: {e}")
            raise
    
    def _group_items_by_type(self, items: List[Any]) -> Dict[str, List[Any]]:
        """按类型分组项目"""
        grouped = defaultdict(list)
        for item in items:
            item_type = type(item).__name__
            grouped[item_type].append(item)
        return grouped
    
    def _process_item_type_optimized(self, item_type: str, items: List[Any]) -> None:
        """优化处理特定类型的项目"""
        # 添加到缓冲区
        self._buffer[item_type].extend(items)
        self._buffer_size[item_type] += len(items)
        self._total_items += len(items)
        
        # 检查是否需要刷新缓冲区
        if (self._buffer_size[item_type] >= self.optimized_batch_size or 
            self._total_items >= self.memory_threshold):
            self._flush_buffer(item_type)
    
    def _flush_buffer(self, item_type: Optional[str] = None) -> None:
        """刷新缓冲区"""
        if item_type:
            # 刷新特定类型
            self._flush_single_type(item_type)
        else:
            # 刷新所有类型
            for itype in list(self._buffer.keys()):
                self._flush_single_type(itype)
    
    def _flush_single_type(self, item_type: str) -> None:
        """刷新单个类型的缓冲区"""
        if not self._buffer[item_type]:
            return
            
        items = self._buffer[item_type]
        
        try:
            # 获取表配置
            pg_config = self._get_table_config(item_type)
            if not pg_config:
                self.logger.warning(f"未找到类型 {item_type} 的表配置")
                return
            
            # 批量插入
            self._bulk_insert_optimized(pg_config, items)
            
            # 清理缓冲区
            self._buffer[item_type].clear()
            self._buffer_size[item_type] = 0
            self._total_items -= len(items)
            self._performance_stats['memory_flushes'] += 1
            
            # 强制垃圾回收
            if self._performance_stats['memory_flushes'] % 10 == 0:
                gc.collect()
                
        except Exception as e:
            self.logger.error(f"刷新类型 {item_type} 的缓冲区失败: {e}")
            raise
    
    def _bulk_insert_optimized(self, pg_config: Dict, items: List[Any]) -> None:
        """优化的批量插入"""
        table = pg_config["table"]
        converter = pg_config["converter"]
        
        # 准备批量数据
        bulk_data = []
        for item in items:
            try:
                converted_item = converter(table, item, False)
                if converted_item:
                    bulk_data.append(converted_item)
            except Exception as e:
                self.logger.warning(f"转换项目失败: {e}")
                continue
        
        if not bulk_data:
            return
        
        # 执行批量插入
        service = PostgreSQLService(self.postgres_url)
        
        try:
            with service.session_scope() as session:
                if self.enable_upsert:
                    self._upsert_bulk_data(session, table, bulk_data)
                else:
                    self._insert_bulk_data(session, table, bulk_data)
                    
                session.commit()
                
        except Exception as e:
            self.logger.error(f"批量插入失败: {e}")
            raise
    
    def _upsert_bulk_data(self, session, table, bulk_data: List[Dict]) -> None:
        """使用UPSERT批量插入数据"""
        try:
            # 使用PostgreSQL的ON CONFLICT DO UPDATE
            stmt = insert(table).values(bulk_data)
            
            # 构建冲突解决策略
            primary_keys = [key.name for key in table.primary_key.columns]
            if primary_keys:
                # 更新除主键外的所有列
                update_dict = {
                    col.name: stmt.excluded[col.name] 
                    for col in table.columns 
                    if col.name not in primary_keys
                }
                
                if update_dict:
                    stmt = stmt.on_conflict_do_update(
                        index_elements=primary_keys,
                        set_=update_dict
                    )
                else:
                    stmt = stmt.on_conflict_do_nothing()
            else:
                stmt = stmt.on_conflict_do_nothing()
            
            session.execute(stmt)
            
        except Exception as e:
            self.logger.error(f"UPSERT操作失败: {e}")
            # 回退到普通插入
            self._insert_bulk_data(session, table, bulk_data)
    
    def _insert_bulk_data(self, session, table, bulk_data: List[Dict]) -> None:
        """传统的批量插入"""
        try:
            session.bulk_insert_mappings(table, bulk_data)
        except IntegrityError as e:
            # 处理重复键错误
            self.logger.warning(f"批量插入遇到重复键，切换到逐条插入: {e}")
            self._insert_data_one_by_one(session, table, bulk_data)
    
    def _insert_data_one_by_one(self, session, table, bulk_data: List[Dict]) -> None:
        """逐条插入数据（处理重复键）"""
        for data in bulk_data:
            try:
                stmt = insert(table).values(data)
                session.execute(stmt)
            except IntegrityError:
                # 忽略重复键错误
                session.rollback()
                continue
    
    def _get_table_config(self, item_type: str) -> Optional[Dict]:
        """获取表配置"""
        # 这里需要根据实际的domain_model_mapping实现
        # 暂时返回None，需要根据实际项目调整
        from indexer.exporters.postgres_item_exporter import domain_model_mapping
        return domain_model_mapping.get(item_type)
    
    def _update_performance_stats(self, item_count: int, execution_time: float) -> None:
        """更新性能统计"""
        self._performance_stats['total_exported'] += item_count
        self._performance_stats['batch_count'] += 1
        self._performance_stats['total_time'] += execution_time
        
        # 定期输出性能报告
        if self._performance_stats['batch_count'] % 100 == 0:
            self._log_performance_report()
    
    def _log_performance_report(self) -> None:
        """输出性能报告"""
        stats = self._performance_stats
        avg_time = stats['total_time'] / max(stats['batch_count'], 1)
        throughput = stats['total_exported'] / max(stats['total_time'], 1)
        
        self.logger.info(
            f"数据库导出性能报告 - "
            f"总导出: {stats['total_exported']}条, "
            f"批次数: {stats['batch_count']}, "
            f"平均批次时间: {avg_time:.3f}s, "
            f"吞吐量: {throughput:.1f}条/秒, "
            f"内存刷新: {stats['memory_flushes']}次"
        )
    
    def flush_all_buffers(self) -> None:
        """刷新所有缓冲区"""
        self._flush_buffer()
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return self._performance_stats.copy()
    
    def __del__(self):
        """析构函数：确保刷新所有缓冲区"""
        try:
            self.flush_all_buffers()
        except Exception as e:
            self.logger.error(f"析构时刷新缓冲区失败: {e}")


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, exporter: OptimizedPostgresItemExporter, batch_size: int = 10000):
        self.exporter = exporter
        self.batch_size = batch_size
        self.buffer = []
        
    def add_item(self, item: Any) -> None:
        """添加项目到批处理器"""
        self.buffer.append(item)
        
        if len(self.buffer) >= self.batch_size:
            self.flush()
    
    def flush(self) -> None:
        """刷新批处理器"""
        if self.buffer:
            self.exporter.export_items_optimized(self.buffer)
            self.buffer.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()