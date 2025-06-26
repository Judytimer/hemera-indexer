#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
区块相关的API路由
Block-related API routes
"""

import logging
from datetime import datetime, timedelta
from flask import request
from flask_restx import Namespace, Resource, reqparse
from sqlalchemy.sql import and_, func

from api.app.cache import cache
from api.app.db_service.blocks import (
    get_block_by_hash, 
    get_block_by_number, 
    get_blocks_by_condition, 
    get_last_block
)
from api.app.utils.format_utils import format_to_dict

# 创建blocks命名空间
blocks_ns = Namespace('blocks', description='区块相关API')

# 参数解析器
list_parser = reqparse.RequestParser()
list_parser.add_argument('page', type=int, default=1, help='页码')
list_parser.add_argument('size', type=int, default=20, help='每页数量')
list_parser.add_argument('order_by', type=str, default='number', help='排序字段')
list_parser.add_argument('order', type=str, default='desc', help='排序方向')

@blocks_ns.route('/latest')
class LatestBlock(Resource):
    """获取最新区块"""
    
    @cache.cached(timeout=10)
    def get(self):
        """获取最新区块信息"""
        try:
            block = get_last_block()
            if block:
                return {
                    'code': 200,
                    'data': format_to_dict(block),
                    'message': 'success'
                }
            return {'code': 404, 'message': 'Block not found'}
        except Exception as e:
            logging.error(f"获取最新区块错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@blocks_ns.route('/<string:identifier>')
class BlockDetail(Resource):
    """获取指定区块详情"""
    
    @cache.cached(timeout=300)
    def get(self, identifier):
        """
        根据区块号或区块哈希获取区块详情
        :param identifier: 区块号或区块哈希
        """
        try:
            # 判断是区块号还是区块哈希
            if identifier.startswith('0x') and len(identifier) == 66:
                # 区块哈希
                block = get_block_by_hash(identifier)
            else:
                # 区块号
                try:
                    block_number = int(identifier)
                    block = get_block_by_number(block_number)
                except ValueError:
                    return {'code': 400, 'message': 'Invalid block identifier'}
            
            if block:
                return {
                    'code': 200,
                    'data': format_to_dict(block),
                    'message': 'success'
                }
            return {'code': 404, 'message': 'Block not found'}
            
        except Exception as e:
            logging.error(f"获取区块详情错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@blocks_ns.route('/list')
class BlockList(Resource):
    """获取区块列表"""
    
    @blocks_ns.expect(list_parser)
    @cache.cached(timeout=60)
    def get(self):
        """获取区块列表"""
        try:
            args = list_parser.parse_args()
            page = max(1, args.get('page', 1))
            size = min(100, max(1, args.get('size', 20)))  # 限制最大100条
            order_by = args.get('order_by', 'number')
            order = args.get('order', 'desc')
            
            # 获取区块数据
            blocks, total = get_blocks_by_condition(
                page=page,
                size=size,
                order_by=order_by,
                order=order
            )
            
            return {
                'code': 200,
                'data': {
                    'items': [format_to_dict(block) for block in blocks],
                    'total': total,
                    'page': page,
                    'size': size
                },
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取区块列表错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@blocks_ns.route('/stats')
class BlockStats(Resource):
    """区块统计信息"""
    
    @cache.cached(timeout=300)
    def get(self):
        """获取区块统计信息"""
        try:
            latest_block = get_last_block()
            
            if not latest_block:
                return {'code': 404, 'message': 'No blocks found'}
            
            # 计算24小时内的区块数量（假设15秒一个区块）
            blocks_24h = 24 * 60 * 60 // 15
            
            stats = {
                'latest_block_number': latest_block.number,
                'latest_block_timestamp': latest_block.timestamp.isoformat() if latest_block.timestamp else None,
                'estimated_blocks_24h': blocks_24h,
                'block_time': 15  # 平均出块时间（秒）
            }
            
            return {
                'code': 200,
                'data': stats,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取区块统计错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}