#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
统计相关的API路由
Statistics-related API routes
"""

import logging
from datetime import datetime, timedelta
from flask import request
from flask_restx import Namespace, Resource, reqparse

from api.app.cache import cache
from api.app.db_service.blocks import get_last_block
from api.app.db_service.transactions import get_total_txn_count, get_tps_latest_10min
from api.app.db_service.daily_transactions_aggregates import get_daily_transactions_cnt
from api.app.utils.format_utils import format_to_dict

# 创建stats命名空间
stats_ns = Namespace('stats', description='统计相关API')

@stats_ns.route('/overview')
class StatsOverview(Resource):
    """总体统计概览"""
    
    @cache.cached(timeout=60)
    def get(self):
        """获取总体统计信息"""
        try:
            # 获取最新区块信息
            latest_block = get_last_block()
            
            # 获取总交易数
            total_transactions = get_total_txn_count()
            
            # 获取最近10分钟的TPS
            recent_tps = get_tps_latest_10min()
            
            # 计算网络基本信息
            stats = {
                'latest_block': {
                    'number': latest_block.number if latest_block else 0,
                    'timestamp': latest_block.timestamp.isoformat() if latest_block and latest_block.timestamp else None,
                    'hash': latest_block.hash if latest_block else None
                },
                'total_transactions': total_transactions,
                'current_tps': recent_tps,
                'network_info': {
                    'average_block_time': 15,  # 平均出块时间（秒）
                    'network_utilization': 'Medium'  # 可以根据实际情况计算
                }
            }
            
            return {
                'code': 200,
                'data': stats,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取统计概览错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@stats_ns.route('/daily-transactions')
class DailyTransactionStats(Resource):
    """每日交易统计"""
    
    @cache.cached(timeout=3600)  # 缓存1小时
    def get(self):
        """获取每日交易统计数据"""
        try:
            # 获取查询参数
            days = int(request.args.get('days', 30))  # 默认最近30天
            days = min(365, max(1, days))  # 限制在1-365天之间
            
            # 获取每日交易数据
            daily_data = get_daily_transactions_cnt(days)
            
            # 格式化数据
            formatted_data = []
            for item in daily_data:
                formatted_data.append({
                    'date': item.date.isoformat() if hasattr(item, 'date') else str(item[0]),
                    'transaction_count': item.transaction_count if hasattr(item, 'transaction_count') else item[1],
                    'unique_addresses': getattr(item, 'unique_addresses', 0)
                })
            
            return {
                'code': 200,
                'data': {
                    'items': formatted_data,
                    'period_days': days,
                    'total_items': len(formatted_data)
                },
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取每日交易统计错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@stats_ns.route('/network')
class NetworkStats(Resource):
    """网络统计信息"""
    
    @cache.cached(timeout=300)  # 缓存5分钟
    def get(self):
        """获取网络统计信息"""
        try:
            # 获取最新区块
            latest_block = get_last_block()
            
            if not latest_block:
                return {'code': 404, 'message': 'No blocks found'}
            
            # 计算网络统计
            current_time = datetime.utcnow()
            block_time = latest_block.timestamp if latest_block.timestamp else current_time
            
            # 估算网络参数
            estimated_hashrate = "Unknown"  # 这需要更复杂的计算
            difficulty = getattr(latest_block, 'difficulty', 0)
            gas_limit = getattr(latest_block, 'gas_limit', 0)
            gas_used = getattr(latest_block, 'gas_used', 0)
            
            # 计算网络利用率
            utilization = (gas_used / gas_limit * 100) if gas_limit > 0 else 0
            
            stats = {
                'block_number': latest_block.number,
                'block_time': 15,  # 平均出块时间
                'difficulty': difficulty,
                'hashrate': estimated_hashrate,
                'gas_limit': gas_limit,
                'gas_used': gas_used,
                'network_utilization': f"{utilization:.2f}%",
                'pending_transactions': 0,  # 需要从mempool获取
                'network_status': 'Active'
            }
            
            return {
                'code': 200,
                'data': stats,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取网络统计错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@stats_ns.route('/performance')
class PerformanceStats(Resource):
    """性能统计信息"""
    
    @cache.cached(timeout=120)  # 缓存2分钟
    def get(self):
        """获取性能统计信息"""
        try:
            # 获取TPS信息
            current_tps = get_tps_latest_10min()
            
            # 获取最新区块信息
            latest_block = get_last_block()
            
            # 计算性能指标
            stats = {
                'current_tps': current_tps,
                'peak_tps_24h': current_tps * 1.5,  # 示例值，需要实际计算
                'average_tps_24h': current_tps * 0.8,  # 示例值
                'block_production_rate': 15,  # 秒
                'confirmation_time': {
                    'fast': '15s',
                    'standard': '30s',
                    'safe': '60s'
                },
                'network_congestion': 'Low'  # 可以根据实际情况计算
            }
            
            return {
                'code': 200,
                'data': stats,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取性能统计错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}