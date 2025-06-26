#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
交易相关的API路由
Transaction-related API routes
"""

import logging
from flask import request
from flask_restx import Namespace, Resource, reqparse
from sqlalchemy.sql import and_, func

from api.app.cache import cache
from api.app.db_service.transactions import (
    get_transaction_by_hash,
    get_transactions_by_condition,
    get_address_transaction_cnt,
    get_total_txn_count,
    get_tps_latest_10min
)
from api.app.db_service.traces import get_traces_by_transaction_hash
from api.app.db_service.logs import get_logs_with_input_by_hash
from api.app.utils.format_utils import format_to_dict

# 创建transactions命名空间
transactions_ns = Namespace('transactions', description='交易相关API')

# 参数解析器
list_parser = reqparse.RequestParser()
list_parser.add_argument('page', type=int, default=1, help='页码')
list_parser.add_argument('size', type=int, default=20, help='每页数量')
list_parser.add_argument('address', type=str, help='地址过滤')
list_parser.add_argument('block_number', type=int, help='区块号过滤')
list_parser.add_argument('order_by', type=str, default='block_number', help='排序字段')
list_parser.add_argument('order', type=str, default='desc', help='排序方向')

@transactions_ns.route('/<string:tx_hash>')
class TransactionDetail(Resource):
    """获取交易详情"""
    
    @cache.cached(timeout=300)
    def get(self, tx_hash):
        """
        根据交易哈希获取交易详情
        :param tx_hash: 交易哈希
        """
        try:
            # 验证交易哈希格式
            if not tx_hash.startswith('0x') or len(tx_hash) != 66:
                return {'code': 400, 'message': 'Invalid transaction hash'}
            
            # 获取交易基本信息
            transaction = get_transaction_by_hash(tx_hash)
            if not transaction:
                return {'code': 404, 'message': 'Transaction not found'}
            
            # 获取交易的traces信息
            traces = get_traces_by_transaction_hash(tx_hash)
            
            # 获取交易的logs信息
            logs = get_logs_with_input_by_hash(tx_hash)
            
            result = {
                'transaction': format_to_dict(transaction),
                'traces': [format_to_dict(trace) for trace in traces],
                'logs': [format_to_dict(log) for log in logs]
            }
            
            return {
                'code': 200,
                'data': result,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取交易详情错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@transactions_ns.route('/list')
class TransactionList(Resource):
    """获取交易列表"""
    
    @transactions_ns.expect(list_parser)
    @cache.cached(timeout=30)
    def get(self):
        """获取交易列表"""
        try:
            args = list_parser.parse_args()
            page = max(1, args.get('page', 1))
            size = min(100, max(1, args.get('size', 20)))
            address = args.get('address')
            block_number = args.get('block_number')
            order_by = args.get('order_by', 'block_number')
            order = args.get('order', 'desc')
            
            # 构建查询条件
            conditions = {}
            if address:
                conditions['address'] = address
            if block_number:
                conditions['block_number'] = block_number
            
            # 获取交易数据
            transactions, total = get_transactions_by_condition(
                page=page,
                size=size,
                conditions=conditions,
                order_by=order_by,
                order=order
            )
            
            return {
                'code': 200,
                'data': {
                    'items': [format_to_dict(tx) for tx in transactions],
                    'total': total,
                    'page': page,
                    'size': size
                },
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取交易列表错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@transactions_ns.route('/stats')
class TransactionStats(Resource):
    """交易统计信息"""
    
    @cache.cached(timeout=60)
    def get(self):
        """获取交易统计信息"""
        try:
            # 获取总交易数
            total_txn_count = get_total_txn_count()
            
            # 获取最近10分钟的TPS
            recent_tps = get_tps_latest_10min()
            
            stats = {
                'total_transactions': total_txn_count,
                'tps_10min': recent_tps,
                'average_tps': recent_tps  # 可以根据需要计算更复杂的平均值
            }
            
            return {
                'code': 200,
                'data': stats,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取交易统计错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@transactions_ns.route('/address/<string:address>/count')
class AddressTransactionCount(Resource):
    """获取地址交易数量"""
    
    @cache.cached(timeout=300)
    def get(self, address):
        """
        获取指定地址的交易数量
        :param address: 地址
        """
        try:
            # 验证地址格式
            if not address.startswith('0x') or len(address) != 42:
                return {'code': 400, 'message': 'Invalid address format'}
            
            count = get_address_transaction_cnt(address)
            
            return {
                'code': 200,
                'data': {'count': count},
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取地址交易数量错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}