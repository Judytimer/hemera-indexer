#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
代币相关的API路由
Token-related API routes
"""

import logging
from flask import request
from flask_restx import Namespace, Resource, reqparse
from sqlalchemy.sql import and_, func

from api.app.cache import cache
from api.app.db_service.tokens import (
    get_token_by_address,
    get_tokens_by_condition,
    get_tokens_cnt_by_condition,
    get_token_holders,
    get_token_holders_cnt,
    get_raw_token_transfers,
    get_token_transfers_with_token_by_hash,
    parse_token_transfers
)
from api.app.utils.format_utils import format_to_dict

# 创建tokens命名空间
tokens_ns = Namespace('tokens', description='代币相关API')

# 参数解析器
list_parser = reqparse.RequestParser()
list_parser.add_argument('page', type=int, default=1, help='页码')
list_parser.add_argument('size', type=int, default=20, help='每页数量')
list_parser.add_argument('token_type', type=str, help='代币类型 (ERC20, ERC721, ERC1155)')
list_parser.add_argument('search', type=str, help='搜索关键词')
list_parser.add_argument('order_by', type=str, default='block_number', help='排序字段')
list_parser.add_argument('order', type=str, default='desc', help='排序方向')

transfer_parser = reqparse.RequestParser()
transfer_parser.add_argument('page', type=int, default=1, help='页码')
transfer_parser.add_argument('size', type=int, default=20, help='每页数量')
transfer_parser.add_argument('from_address', type=str, help='发送地址')
transfer_parser.add_argument('to_address', type=str, help='接收地址')
transfer_parser.add_argument('token_address', type=str, help='代币合约地址')

@tokens_ns.route('/<string:token_address>')
class TokenDetail(Resource):
    """获取代币详情"""
    
    @cache.cached(timeout=300)
    def get(self, token_address):
        """
        根据代币合约地址获取代币详情
        :param token_address: 代币合约地址
        """
        try:
            # 验证地址格式
            if not token_address.startswith('0x') or len(token_address) != 42:
                return {'code': 400, 'message': 'Invalid token address format'}
            
            token = get_token_by_address(token_address)
            if not token:
                return {'code': 404, 'message': 'Token not found'}
            
            # 获取代币持有者数量
            holders_count = get_token_holders_cnt(token_address)
            
            result = format_to_dict(token)
            result['holders_count'] = holders_count
            
            return {
                'code': 200,
                'data': result,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取代币详情错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@tokens_ns.route('/list')
class TokenList(Resource):
    """获取代币列表"""
    
    @tokens_ns.expect(list_parser)
    @cache.cached(timeout=120)
    def get(self):
        """获取代币列表"""
        try:
            args = list_parser.parse_args()
            page = max(1, args.get('page', 1))
            size = min(100, max(1, args.get('size', 20)))
            token_type = args.get('token_type')
            search = args.get('search')
            order_by = args.get('order_by', 'block_number')
            order = args.get('order', 'desc')
            
            # 构建查询条件
            conditions = {}
            if token_type:
                conditions['token_type'] = token_type
            if search:
                conditions['search'] = search
            
            # 获取代币数据
            tokens, total = get_tokens_by_condition(
                page=page,
                size=size,
                conditions=conditions,
                order_by=order_by,
                order=order
            )
            
            return {
                'code': 200,
                'data': {
                    'items': [format_to_dict(token) for token in tokens],
                    'total': total,
                    'page': page,
                    'size': size
                },
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取代币列表错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@tokens_ns.route('/<string:token_address>/holders')
class TokenHolders(Resource):
    """获取代币持有者列表"""
    
    @cache.cached(timeout=300)
    def get(self, token_address):
        """
        获取代币持有者列表
        :param token_address: 代币合约地址
        """
        try:
            # 验证地址格式
            if not token_address.startswith('0x') or len(token_address) != 42:
                return {'code': 400, 'message': 'Invalid token address format'}
            
            page = int(request.args.get('page', 1))
            size = min(100, max(1, int(request.args.get('size', 20))))
            
            holders, total = get_token_holders(
                token_address=token_address,
                page=page,
                size=size
            )
            
            return {
                'code': 200,
                'data': {
                    'items': [format_to_dict(holder) for holder in holders],
                    'total': total,
                    'page': page,
                    'size': size
                },
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取代币持有者错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@tokens_ns.route('/transfers')
class TokenTransfers(Resource):
    """获取代币转账记录"""
    
    @tokens_ns.expect(transfer_parser)
    @cache.cached(timeout=60)
    def get(self):
        """获取代币转账记录"""
        try:
            args = transfer_parser.parse_args()
            page = max(1, args.get('page', 1))
            size = min(100, max(1, args.get('size', 20)))
            from_address = args.get('from_address')
            to_address = args.get('to_address')
            token_address = args.get('token_address')
            
            # 构建查询条件
            conditions = {}
            if from_address:
                conditions['from_address'] = from_address
            if to_address:
                conditions['to_address'] = to_address
            if token_address:
                conditions['token_address'] = token_address
            
            # 获取转账记录
            transfers, total = get_raw_token_transfers(
                page=page,
                size=size,
                conditions=conditions
            )
            
            # 解析转账记录
            parsed_transfers = parse_token_transfers(transfers)
            
            return {
                'code': 200,
                'data': {
                    'items': [format_to_dict(transfer) for transfer in parsed_transfers],
                    'total': total,
                    'page': page,
                    'size': size
                },
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取代币转账记录错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@tokens_ns.route('/transfers/<string:tx_hash>')
class TransactionTokenTransfers(Resource):
    """获取指定交易的代币转账记录"""
    
    @cache.cached(timeout=300)
    def get(self, tx_hash):
        """
        获取指定交易哈希的代币转账记录
        :param tx_hash: 交易哈希
        """
        try:
            # 验证交易哈希格式
            if not tx_hash.startswith('0x') or len(tx_hash) != 66:
                return {'code': 400, 'message': 'Invalid transaction hash'}
            
            transfers = get_token_transfers_with_token_by_hash(tx_hash)
            
            return {
                'code': 200,
                'data': [format_to_dict(transfer) for transfer in transfers],
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取交易代币转账记录错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}