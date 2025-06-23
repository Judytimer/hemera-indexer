from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import aliased

from common.models import db
from common.models.erc20_token_transfers import ERC20TokenTransfers
from common.models.tokens import Tokens
from common.utils.format_utils import hex_str_to_bytes, bytes_to_hex_str
from common.utils.exception_control import APIError


def get_wallet_erc20_transfer_summary(
    wallet_address: str,
    token_address: Optional[str] = None,
    start_block: Optional[int] = None,
    end_block: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> Dict:
    """
    追踪钱包地址的ERC20 Token转账记录，统计收发总额
    
    Args:
        wallet_address: 钱包地址 (hex格式)
        token_address: 可选，特定代币地址，如果不指定则统计所有ERC20代币
        start_block: 可选，起始区块号
        end_block: 可选，结束区块号
        start_time: 可选，起始时间
        end_time: 可选，结束时间
    
    Returns:
        Dict: 包含收发总额统计的字典
    """
    try:
        # 转换地址为bytes格式
        wallet_bytes = hex_str_to_bytes(wallet_address.lower())
        token_bytes = hex_str_to_bytes(token_address.lower()) if token_address else None
        
        # 构建基础查询条件
        base_conditions = []
        
        # 钱包地址条件（作为发送方或接收方）
        wallet_condition = or_(
            ERC20TokenTransfers.from_address == wallet_bytes,
            ERC20TokenTransfers.to_address == wallet_bytes
        )
        base_conditions.append(wallet_condition)
        
        # 代币地址条件
        if token_bytes:
            base_conditions.append(ERC20TokenTransfers.token_address == token_bytes)
        
        # 区块范围条件
        if start_block is not None:
            base_conditions.append(ERC20TokenTransfers.block_number >= start_block)
        if end_block is not None:
            base_conditions.append(ERC20TokenTransfers.block_number <= end_block)
        
        # 时间范围条件
        if start_time is not None:
            base_conditions.append(ERC20TokenTransfers.block_timestamp >= start_time)
        if end_time is not None:
            base_conditions.append(ERC20TokenTransfers.block_timestamp <= end_time)
        
        # 排除reorg的记录
        base_conditions.append(ERC20TokenTransfers.reorg == False)
        
        # 查询收入总额（作为接收方）
        received_query = (
            db.session.query(
                ERC20TokenTransfers.token_address,
                func.sum(ERC20TokenTransfers.value).label('total_received'),
                func.count(ERC20TokenTransfers.transaction_hash).label('received_count')
            )
            .filter(
                and_(
                    ERC20TokenTransfers.to_address == wallet_bytes,
                    *[cond for cond in base_conditions if cond != wallet_condition]
                )
            )
            .group_by(ERC20TokenTransfers.token_address)
        )
        
        # 查询支出总额（作为发送方）
        sent_query = (
            db.session.query(
                ERC20TokenTransfers.token_address,
                func.sum(ERC20TokenTransfers.value).label('total_sent'),
                func.count(ERC20TokenTransfers.transaction_hash).label('sent_count')
            )
            .filter(
                and_(
                    ERC20TokenTransfers.from_address == wallet_bytes,
                    *[cond for cond in base_conditions if cond != wallet_condition]
                )
            )
            .group_by(ERC20TokenTransfers.token_address)
        )
        
        # 执行查询
        received_results = received_query.all()
        sent_results = sent_query.all()
        
        # 获取所有涉及的代币地址
        all_token_addresses = set()
        for result in received_results:
            all_token_addresses.add(result.token_address)
        for result in sent_results:
            all_token_addresses.add(result.token_address)
        
        # 查询代币信息
        tokens_info = {}
        if all_token_addresses:
            tokens = (
                db.session.query(Tokens)
                .filter(Tokens.address.in_(list(all_token_addresses)))
                .all()
            )
            for token in tokens:
                tokens_info[token.address] = {
                    'symbol': token.symbol or 'UNKNOWN',
                    'name': token.name or 'Unknown Token',
                    'decimals': int(token.decimals) if token.decimals else 18,
                    'address': bytes_to_hex_str(token.address)
                }
        
        # 整理结果
        token_summaries = {}
        
        # 处理收入数据
        for result in received_results:
            token_addr = result.token_address
            if token_addr not in token_summaries:
                token_summaries[token_addr] = {
                    'total_received': Decimal('0'),
                    'total_sent': Decimal('0'),
                    'received_count': 0,
                    'sent_count': 0,
                    'net_amount': Decimal('0')
                }
            
            token_summaries[token_addr]['total_received'] = Decimal(str(result.total_received or 0))
            token_summaries[token_addr]['received_count'] = result.received_count or 0
        
        # 处理支出数据
        for result in sent_results:
            token_addr = result.token_address
            if token_addr not in token_summaries:
                token_summaries[token_addr] = {
                    'total_received': Decimal('0'),
                    'total_sent': Decimal('0'),
                    'received_count': 0,
                    'sent_count': 0,
                    'net_amount': Decimal('0')
                }
            
            token_summaries[token_addr]['total_sent'] = Decimal(str(result.total_sent or 0))
            token_summaries[token_addr]['sent_count'] = result.sent_count or 0
        
        # 计算净额并格式化结果
        formatted_results = []
        total_tokens_count = 0
        
        for token_addr, summary in token_summaries.items():
            # 计算净额
            net_amount = summary['total_received'] - summary['total_sent']
            summary['net_amount'] = net_amount
            
            # 获取代币信息
            token_info = tokens_info.get(token_addr, {
                'symbol': 'UNKNOWN',
                'name': 'Unknown Token',
                'decimals': 18,
                'address': bytes_to_hex_str(token_addr)
            })
            
            # 格式化金额（考虑小数位）
            decimals = token_info['decimals']
            divisor = Decimal(10) ** decimals
            
            formatted_result = {
                'token_address': token_info['address'],
                'token_symbol': token_info['symbol'],
                'token_name': token_info['name'],
                'token_decimals': decimals,
                'total_received_raw': str(summary['total_received']),
                'total_sent_raw': str(summary['total_sent']),
                'net_amount_raw': str(net_amount),
                'total_received_formatted': str(summary['total_received'] / divisor),
                'total_sent_formatted': str(summary['total_sent'] / divisor),
                'net_amount_formatted': str(net_amount / divisor),
                'received_transaction_count': summary['received_count'],
                'sent_transaction_count': summary['sent_count'],
                'total_transaction_count': summary['received_count'] + summary['sent_count']
            }
            
            formatted_results.append(formatted_result)
            total_tokens_count += 1
        
        # 按交易总数排序
        formatted_results.sort(key=lambda x: x['total_transaction_count'], reverse=True)
        
        # 计算总体统计
        total_received_count = sum(r['received_transaction_count'] for r in formatted_results)
        total_sent_count = sum(r['sent_transaction_count'] for r in formatted_results)
        
        return {
            'wallet_address': wallet_address.lower(),
            'query_conditions': {
                'token_address': token_address,
                'start_block': start_block,
                'end_block': end_block,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None
            },
            'summary': {
                'total_tokens_involved': total_tokens_count,
                'total_received_transactions': total_received_count,
                'total_sent_transactions': total_sent_count,
                'total_transactions': total_received_count + total_sent_count
            },
            'token_details': formatted_results
        }
        
    except Exception as e:
        raise APIError(f"查询钱包ERC20转账记录失败: {str(e)}", code=500)


def get_wallet_erc20_transfer_history(
    wallet_address: str,
    token_address: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    start_block: Optional[int] = None,
    end_block: Optional[int] = None
) -> Dict:
    """
    获取钱包地址的ERC20转账历史记录
    
    Args:
        wallet_address: 钱包地址
        token_address: 可选，特定代币地址
        page: 页码，从1开始
        page_size: 每页大小
        start_block: 可选，起始区块号
        end_block: 可选，结束区块号
    
    Returns:
        Dict: 包含转账历史记录的字典
    """
    try:
        wallet_bytes = hex_str_to_bytes(wallet_address.lower())
        token_bytes = hex_str_to_bytes(token_address.lower()) if token_address else None
        
        # 构建查询条件
        conditions = [
            or_(
                ERC20TokenTransfers.from_address == wallet_bytes,
                ERC20TokenTransfers.to_address == wallet_bytes
            ),
            ERC20TokenTransfers.reorg == False
        ]
        
        if token_bytes:
            conditions.append(ERC20TokenTransfers.token_address == token_bytes)
        
        if start_block is not None:
            conditions.append(ERC20TokenTransfers.block_number >= start_block)
        if end_block is not None:
            conditions.append(ERC20TokenTransfers.block_number <= end_block)
        
        # 查询转账记录
        query = (
            db.session.query(ERC20TokenTransfers)
            .filter(and_(*conditions))
            .order_by(
                ERC20TokenTransfers.block_number.desc(),
                ERC20TokenTransfers.log_index.desc()
            )
        )
        
        # 分页
        total_count = query.count()
        transfers = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 获取代币信息
        token_addresses = list(set([t.token_address for t in transfers]))
        tokens_info = {}
        if token_addresses:
            tokens = (
                db.session.query(Tokens)
                .filter(Tokens.address.in_(token_addresses))
                .all()
            )
            for token in tokens:
                tokens_info[token.address] = {
                    'symbol': token.symbol or 'UNKNOWN',
                    'name': token.name or 'Unknown Token',
                    'decimals': int(token.decimals) if token.decimals else 18
                }
        
        # 格式化结果
        formatted_transfers = []
        for transfer in transfers:
            token_info = tokens_info.get(transfer.token_address, {
                'symbol': 'UNKNOWN',
                'name': 'Unknown Token',
                'decimals': 18
            })
            
            # 判断转账方向
            is_incoming = transfer.to_address == wallet_bytes
            direction = 'incoming' if is_incoming else 'outgoing'
            
            # 格式化金额
            decimals = token_info['decimals']
            divisor = Decimal(10) ** decimals
            formatted_value = str(Decimal(str(transfer.value)) / divisor)
            
            formatted_transfer = {
                'transaction_hash': bytes_to_hex_str(transfer.transaction_hash),
                'block_number': transfer.block_number,
                'block_timestamp': transfer.block_timestamp.isoformat() if transfer.block_timestamp else None,
                'log_index': transfer.log_index,
                'from_address': bytes_to_hex_str(transfer.from_address),
                'to_address': bytes_to_hex_str(transfer.to_address),
                'token_address': bytes_to_hex_str(transfer.token_address),
                'token_symbol': token_info['symbol'],
                'token_name': token_info['name'],
                'token_decimals': decimals,
                'value_raw': str(transfer.value),
                'value_formatted': formatted_value,
                'direction': direction
            }
            
            formatted_transfers.append(formatted_transfer)
        
        return {
            'wallet_address': wallet_address.lower(),
            'token_address': token_address,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            },
            'transfers': formatted_transfers
        }
        
    except Exception as e:
        raise APIError(f"查询钱包ERC20转账历史失败: {str(e)}", code=500) 