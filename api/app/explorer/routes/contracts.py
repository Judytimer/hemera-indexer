#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
合约相关的API路由
Contract-related API routes
"""

import logging
from flask import request
from flask_restx import Namespace, Resource, reqparse

from api.app.cache import cache
from api.app.db_service.contracts import get_contract_by_address
from api.app.contract.contract_verify import get_abis_for_method, get_sha256_hash, get_similar_addresses
from api.app.utils.format_utils import format_to_dict

# 创建contracts命名空间
contracts_ns = Namespace('contracts', description='合约相关API')

@contracts_ns.route('/<string:contract_address>')
class ContractDetail(Resource):
    """获取合约详情"""
    
    @cache.cached(timeout=300)
    def get(self, contract_address):
        """
        根据合约地址获取合约详情
        :param contract_address: 合约地址
        """
        try:
            # 验证地址格式
            if not contract_address.startswith('0x') or len(contract_address) != 42:
                return {'code': 400, 'message': 'Invalid contract address format'}
            
            contract = get_contract_by_address(contract_address)
            if not contract:
                return {'code': 404, 'message': 'Contract not found'}
            
            result = format_to_dict(contract)
            
            return {
                'code': 200,
                'data': result,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取合约详情错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@contracts_ns.route('/<string:contract_address>/verify')
class ContractVerify(Resource):
    """合约验证相关功能"""
    
    def get(self, contract_address):
        """获取合约验证信息"""
        try:
            # 验证地址格式
            if not contract_address.startswith('0x') or len(contract_address) != 42:
                return {'code': 400, 'message': 'Invalid contract address format'}
            
            contract = get_contract_by_address(contract_address)
            if not contract:
                return {'code': 404, 'message': 'Contract not found'}
            
            # 获取合约的ABI信息
            abis = get_abis_for_method(contract_address)
            
            # 获取合约的哈希信息
            contract_hash = get_sha256_hash(contract.bytecode) if contract.bytecode else None
            
            # 获取相似的合约地址
            similar_addresses = get_similar_addresses(contract_hash) if contract_hash else []
            
            result = {
                'contract': format_to_dict(contract),
                'abis': abis,
                'hash': contract_hash,
                'similar_contracts': similar_addresses,
                'is_verified': bool(contract.is_verified) if hasattr(contract, 'is_verified') else False
            }
            
            return {
                'code': 200,
                'data': result,
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取合约验证信息错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@contracts_ns.route('/<string:contract_address>/abi')
class ContractABI(Resource):
    """获取合约ABI"""
    
    @cache.cached(timeout=3600)  # ABI信息缓存1小时
    def get(self, contract_address):
        """
        获取合约的ABI信息
        :param contract_address: 合约地址
        """
        try:
            # 验证地址格式
            if not contract_address.startswith('0x') or len(contract_address) != 42:
                return {'code': 400, 'message': 'Invalid contract address format'}
            
            # 获取合约ABI
            abis = get_abis_for_method(contract_address)
            
            if not abis:
                return {'code': 404, 'message': 'Contract ABI not found'}
            
            return {
                'code': 200,
                'data': {'abi': abis},
                'message': 'success'
            }
            
        except Exception as e:
            logging.error(f"获取合约ABI错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}

@contracts_ns.route('/search')
class ContractSearch(Resource):
    """合约搜索"""
    
    def get(self):
        """搜索合约"""
        try:
            # 获取搜索参数
            query = request.args.get('q', '').strip()
            page = int(request.args.get('page', 1))
            size = min(100, max(1, int(request.args.get('size', 20))))
            
            if not query:
                return {'code': 400, 'message': 'Search query is required'}
            
            # 如果查询是地址格式，直接查找
            if query.startswith('0x') and len(query) == 42:
                contract = get_contract_by_address(query)
                if contract:
                    return {
                        'code': 200,
                        'data': {
                            'items': [format_to_dict(contract)],
                            'total': 1,
                            'page': 1,
                            'size': size
                        },
                        'message': 'success'
                    }
                else:
                    return {
                        'code': 200,
                        'data': {
                            'items': [],
                            'total': 0,
                            'page': page,
                            'size': size
                        },
                        'message': 'success'
                    }
            
            # TODO: 实现更复杂的合约搜索逻辑
            # 这里可以根据合约名称、标签等进行搜索
            
            return {
                'code': 200,
                'data': {
                    'items': [],
                    'total': 0,
                    'page': page,
                    'size': size
                },
                'message': 'Contract search by name not implemented yet'
            }
            
        except Exception as e:
            logging.error(f"合约搜索错误: {e}")
            return {'code': 500, 'message': 'Internal server error'}