#!/usr/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields

from api.app.db_service.wallet_erc20_tracker import (
    get_wallet_erc20_transfer_summary,
    get_wallet_erc20_transfer_history
)
from common.utils.exception_control import APIError
from common.utils.format_utils import is_hex_address

wallet_tracker_namespace = Namespace("wallet_tracker", path="/api/v1/wallet", description="钱包ERC20转账追踪API")

# 定义响应模型
summary_model = wallet_tracker_namespace.model('WalletERC20Summary', {
    'wallet_address': fields.String(description='钱包地址'),
    'summary': fields.Raw(description='统计汇总'),
    'token_details': fields.List(fields.Raw(), description='代币详情列表')
})

history_model = wallet_tracker_namespace.model('WalletERC20History', {
    'wallet_address': fields.String(description='钱包地址'),
    'pagination': fields.Raw(description='分页信息'),
    'transfers': fields.List(fields.Raw(), description='转账记录列表')
})

tokens_model = wallet_tracker_namespace.model('WalletERC20Tokens', {
    'wallet_address': fields.String(description='钱包地址'),
    'total_tokens': fields.Integer(description='代币总数'),
    'tokens': fields.List(fields.Raw(), description='代币列表')
})


@wallet_tracker_namespace.route('/<string:wallet_address>/erc20/summary')
class WalletERC20Summary(Resource):
    @wallet_tracker_namespace.doc('get_wallet_erc20_summary')
    @wallet_tracker_namespace.marshal_with(summary_model)
    @wallet_tracker_namespace.param('wallet_address', '钱包地址', required=True)
    @wallet_tracker_namespace.param('token_address', '代币地址 (可选)', required=False)
    @wallet_tracker_namespace.param('start_block', '起始区块号 (可选)', type=int, required=False)
    @wallet_tracker_namespace.param('end_block', '结束区块号 (可选)', type=int, required=False)
    @wallet_tracker_namespace.param('start_time', '起始时间 ISO格式 (可选)', required=False)
    @wallet_tracker_namespace.param('end_time', '结束时间 ISO格式 (可选)', required=False)
    def get(self, wallet_address):
        """获取钱包地址的ERC20转账统计汇总"""
        try:
            # 验证钱包地址格式
            if not is_hex_address(wallet_address):
                wallet_tracker_namespace.abort(400, "无效的钱包地址格式")
            
            # 获取查询参数
            token_address = request.args.get('token_address')
            start_block = request.args.get('start_block', type=int)
            end_block = request.args.get('end_block', type=int)
            start_time_str = request.args.get('start_time')
            end_time_str = request.args.get('end_time')
            
            # 验证代币地址格式
            if token_address and not is_hex_address(token_address):
                wallet_tracker_namespace.abort(400, "无效的代币地址格式")
            
            # 解析时间参数
            start_time = None
            end_time = None
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                except ValueError:
                    wallet_tracker_namespace.abort(400, "无效的开始时间格式，请使用ISO格式")
            
            if end_time_str:
                try:
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                except ValueError:
                    wallet_tracker_namespace.abort(400, "无效的结束时间格式，请使用ISO格式")
            
            # 验证区块范围
            if start_block is not None and start_block < 0:
                wallet_tracker_namespace.abort(400, "起始区块号不能为负数")
            
            if end_block is not None and end_block < 0:
                wallet_tracker_namespace.abort(400, "结束区块号不能为负数")
            
            if start_block is not None and end_block is not None and start_block > end_block:
                wallet_tracker_namespace.abort(400, "起始区块号不能大于结束区块号")
            
            # 验证时间范围
            if start_time and end_time and start_time > end_time:
                wallet_tracker_namespace.abort(400, "开始时间不能晚于结束时间")
            
            # 调用数据库服务
            result = get_wallet_erc20_transfer_summary(
                wallet_address=wallet_address,
                token_address=token_address,
                start_block=start_block,
                end_block=end_block,
                start_time=start_time,
                end_time=end_time
            )
            
            return result
            
        except APIError as e:
            wallet_tracker_namespace.abort(e.code, str(e))
        except Exception as e:
            wallet_tracker_namespace.abort(500, f"内部服务器错误: {str(e)}")


@wallet_tracker_namespace.route('/<string:wallet_address>/erc20/history')
class WalletERC20History(Resource):
    @wallet_tracker_namespace.doc('get_wallet_erc20_history')
    @wallet_tracker_namespace.marshal_with(history_model)
    @wallet_tracker_namespace.param('wallet_address', '钱包地址', required=True)
    @wallet_tracker_namespace.param('token_address', '代币地址 (可选)', required=False)
    @wallet_tracker_namespace.param('page', '页码，默认为1', type=int, required=False, default=1)
    @wallet_tracker_namespace.param('page_size', '每页大小，默认为50，最大100', type=int, required=False, default=50)
    @wallet_tracker_namespace.param('start_block', '起始区块号 (可选)', type=int, required=False)
    @wallet_tracker_namespace.param('end_block', '结束区块号 (可选)', type=int, required=False)
    def get(self, wallet_address):
        """获取钱包地址的ERC20转账历史记录"""
        try:
            # 验证钱包地址格式
            if not is_hex_address(wallet_address):
                wallet_tracker_namespace.abort(400, "无效的钱包地址格式")
            
            # 获取查询参数
            token_address = request.args.get('token_address')
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 50, type=int)
            start_block = request.args.get('start_block', type=int)
            end_block = request.args.get('end_block', type=int)
            
            # 验证分页参数
            if page < 1:
                wallet_tracker_namespace.abort(400, "页码必须大于0")
            
            if page_size < 1 or page_size > 100:
                wallet_tracker_namespace.abort(400, "每页大小必须在1-100之间")
            
            # 验证代币地址格式
            if token_address and not is_hex_address(token_address):
                wallet_tracker_namespace.abort(400, "无效的代币地址格式")
            
            # 验证区块范围
            if start_block is not None and start_block < 0:
                wallet_tracker_namespace.abort(400, "起始区块号不能为负数")
            
            if end_block is not None and end_block < 0:
                wallet_tracker_namespace.abort(400, "结束区块号不能为负数")
            
            if start_block is not None and end_block is not None and start_block > end_block:
                wallet_tracker_namespace.abort(400, "起始区块号不能大于结束区块号")
            
            # 调用数据库服务
            result = get_wallet_erc20_transfer_history(
                wallet_address=wallet_address,
                token_address=token_address,
                page=page,
                page_size=page_size,
                start_block=start_block,
                end_block=end_block
            )
            
            return result
            
        except APIError as e:
            wallet_tracker_namespace.abort(e.code, str(e))
        except Exception as e:
            wallet_tracker_namespace.abort(500, f"内部服务器错误: {str(e)}")


@wallet_tracker_namespace.route('/<string:wallet_address>/erc20/tokens')
class WalletERC20Tokens(Resource):
    @wallet_tracker_namespace.doc('get_wallet_erc20_tokens')
    @wallet_tracker_namespace.marshal_with(tokens_model)
    @wallet_tracker_namespace.param('wallet_address', '钱包地址', required=True)
    def get(self, wallet_address):
        """获取钱包地址涉及的所有ERC20代币列表"""
        try:
            # 验证钱包地址格式
            if not is_hex_address(wallet_address):
                wallet_tracker_namespace.abort(400, "无效的钱包地址格式")
            
            # 调用汇总接口获取代币列表
            result = get_wallet_erc20_transfer_summary(wallet_address=wallet_address)
            
            # 提取代币信息
            tokens = []
            for token_detail in result['token_details']:
                tokens.append({
                    'token_address': token_detail['token_address'],
                    'token_symbol': token_detail['token_symbol'],
                    'token_name': token_detail['token_name'],
                    'token_decimals': token_detail['token_decimals'],
                    'transaction_count': token_detail['total_transaction_count']
                })
            
            return {
                "wallet_address": wallet_address.lower(),
                "total_tokens": len(tokens),
                "tokens": tokens
            }
            
        except APIError as e:
            wallet_tracker_namespace.abort(e.code, str(e))
        except Exception as e:
            wallet_tracker_namespace.abort(500, f"内部服务器错误: {str(e)}") 