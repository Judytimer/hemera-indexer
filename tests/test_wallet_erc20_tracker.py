import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.app.db_service.wallet_erc20_tracker import (
    get_wallet_erc20_transfer_summary,
    get_wallet_erc20_transfer_history
)
from common.utils.exception_control import APIError


class TestWalletERC20Tracker:
    
    def test_get_wallet_erc20_transfer_summary_success(self):
        """测试成功获取钱包ERC20转账统计"""
        # Mock数据库查询结果
        mock_received_result = MagicMock()
        mock_received_result.token_address = b'\x12\x34' * 10  # 20 bytes
        mock_received_result.total_received = 1000000000000000000  # 1 ETH
        mock_received_result.received_count = 5
        
        mock_sent_result = MagicMock()
        mock_sent_result.token_address = b'\x12\x34' * 10
        mock_sent_result.total_sent = 500000000000000000  # 0.5 ETH
        mock_sent_result.sent_count = 3
        
        mock_token = MagicMock()
        mock_token.address = b'\x12\x34' * 10
        mock_token.symbol = 'TEST'
        mock_token.name = 'Test Token'
        mock_token.decimals = 18
        
        with patch('api.app.db_service.wallet_erc20_tracker.db.session') as mock_session:
            # Mock查询链
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.group_by.return_value = mock_query
            
            # 第一次调用返回received结果，第二次返回sent结果，第三次返回token结果
            call_count = 0
            def mock_all():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return [mock_received_result]
                elif call_count == 2:
                    return [mock_sent_result]
                elif call_count == 3:
                    return [mock_token]
                return []
            
            mock_query.all = mock_all
            mock_session.query.return_value = mock_query
            
            result = get_wallet_erc20_transfer_summary(
                wallet_address="0x1234567890123456789012345678901234567890"
            )
            
            # 验证结果结构
            assert 'wallet_address' in result
            assert 'summary' in result
            assert 'token_details' in result
            assert result['summary']['total_tokens_involved'] == 1
            assert result['summary']['total_received_transactions'] == 5
            assert result['summary']['total_sent_transactions'] == 3
            assert result['summary']['total_transactions'] == 8
            
            # 验证代币详情
            token_detail = result['token_details'][0]
            assert token_detail['token_symbol'] == 'TEST'
            assert token_detail['token_name'] == 'Test Token'
            assert token_detail['received_transaction_count'] == 5
            assert token_detail['sent_transaction_count'] == 3
            assert token_detail['total_received_formatted'] == '1'
            assert token_detail['total_sent_formatted'] == '0.5'
            assert token_detail['net_amount_formatted'] == '0.5'
    
    def test_get_wallet_erc20_transfer_summary_with_filters(self):
        """测试带过滤条件的转账统计"""
        with patch('api.app.db_service.wallet_erc20_tracker.db.session') as mock_session:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.group_by.return_value = mock_query
            mock_query.all.return_value = []
            mock_session.query.return_value = mock_query
            
            # 测试时间过滤
            start_time = datetime(2024, 1, 1)
            end_time = datetime(2024, 12, 31)
            
            result = get_wallet_erc20_transfer_summary(
                wallet_address="0x1234567890123456789012345678901234567890",
                token_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
                start_block=1000000,
                end_block=2000000,
                start_time=start_time,
                end_time=end_time
            )
            
            # 验证查询条件
            assert result['query_conditions']['token_address'] == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef"
            assert result['query_conditions']['start_block'] == 1000000
            assert result['query_conditions']['end_block'] == 2000000
            assert result['query_conditions']['start_time'] == start_time.isoformat()
            assert result['query_conditions']['end_time'] == end_time.isoformat()
    
    def test_get_wallet_erc20_transfer_history_success(self):
        """测试成功获取转账历史"""
        mock_transfer = MagicMock()
        mock_transfer.transaction_hash = b'\xab\xcd' * 16  # 32 bytes
        mock_transfer.block_number = 12345678
        mock_transfer.block_timestamp = datetime(2024, 1, 15, 10, 30, 0)
        mock_transfer.log_index = 5
        mock_transfer.from_address = b'\x12\x34' * 10  # 匹配钱包地址  
        mock_transfer.to_address = b'\x11\x11' * 10  # 20 bytes
        mock_transfer.token_address = b'\x56\x78' * 10
        mock_transfer.value = 1000000000000000000  # 1 ETH in wei
        
        mock_token = MagicMock()
        mock_token.address = b'\x56\x78' * 10
        mock_token.symbol = 'TEST'
        mock_token.name = 'Test Token'
        mock_token.decimals = 18
        
        with patch('api.app.db_service.wallet_erc20_tracker.db.session') as mock_session:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            call_count = 0
            def mock_all():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return [mock_transfer]
                elif call_count == 2:
                    return [mock_token]
                return []
                
            mock_query.all = mock_all
            mock_session.query.return_value = mock_query
            
            result = get_wallet_erc20_transfer_history(
                wallet_address="0x1234567890123456789012345678901234567890",
                page=1,
                page_size=50
            )
            
            # 验证结果结构
            assert 'wallet_address' in result
            assert 'pagination' in result
            assert 'transfers' in result
            assert result['pagination']['total_count'] == 1
            assert len(result['transfers']) == 1
            
            # 验证转账记录
            transfer = result['transfers'][0]
            assert transfer['token_symbol'] == 'TEST'
            assert transfer['direction'] == 'outgoing'  # from_address匹配钱包地址
            assert transfer['value_formatted'] == '1'  # 1 ETH (Decimal转换后去掉尾随0)
            assert transfer['block_number'] == 12345678
    
    def test_get_wallet_erc20_transfer_history_pagination(self):
        """测试分页功能"""
        with patch('api.app.db_service.wallet_erc20_tracker.db.session') as mock_session:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.count.return_value = 100  # 总共100条记录
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []  # 空结果
            mock_session.query.return_value = mock_query
            
            result = get_wallet_erc20_transfer_history(
                wallet_address="0x1234567890123456789012345678901234567890",
                page=2,
                page_size=20
            )
            
            # 验证分页信息
            assert result['pagination']['page'] == 2
            assert result['pagination']['page_size'] == 20
            assert result['pagination']['total_count'] == 100
            assert result['pagination']['total_pages'] == 5  # 100/20 = 5
            
            # 验证offset调用
            mock_query.offset.assert_called_with(20)  # (page-1) * page_size = (2-1) * 20 = 20
            mock_query.limit.assert_called_with(20)
    
    def test_invalid_wallet_address(self):
        """测试无效钱包地址"""
        with pytest.raises(Exception):  # hex_str_to_bytes会抛出异常
            get_wallet_erc20_transfer_summary(wallet_address="invalid_address")
    
    def test_database_error_handling(self):
        """测试数据库错误处理"""
        with patch('api.app.db_service.wallet_erc20_tracker.db.session') as mock_session:
            mock_session.query.side_effect = Exception("Database connection failed")
            
            with pytest.raises(APIError) as exc_info:
                get_wallet_erc20_transfer_summary(
                    wallet_address="0x1234567890123456789012345678901234567890"
                )
            
            assert exc_info.value.code == 500
    
    def test_empty_results(self):
        """测试空结果处理"""
        with patch('api.app.db_service.wallet_erc20_tracker.db.session') as mock_session:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.group_by.return_value = mock_query
            mock_query.all.return_value = []  # 空结果
            mock_session.query.return_value = mock_query
            
            result = get_wallet_erc20_transfer_summary(
                wallet_address="0x1234567890123456789012345678901234567890"
            )
            
            # 验证空结果
            assert result['summary']['total_tokens_involved'] == 0
            assert result['summary']['total_received_transactions'] == 0
            assert result['summary']['total_sent_transactions'] == 0
            assert result['summary']['total_transactions'] == 0
            assert len(result['token_details']) == 0
    
    def test_decimal_precision(self):
        """测试小数精度处理"""
        mock_received_result = MagicMock()
        mock_received_result.token_address = b'\x12\x34' * 10
        mock_received_result.total_received = 1000000  # 1 USDT (6位小数)
        mock_received_result.received_count = 1
        
        mock_token = MagicMock()
        mock_token.address = b'\x12\x34' * 10
        mock_token.symbol = 'USDT'
        mock_token.name = 'Tether USD'
        mock_token.decimals = 6  # USDT有6位小数
        
        with patch('api.app.db_service.wallet_erc20_tracker.db.session') as mock_session:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.group_by.return_value = mock_query
            
            call_count = 0
            def mock_all():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return [mock_received_result]
                elif call_count == 2:
                    return []  # 无发送记录
                elif call_count == 3:
                    return [mock_token]
                return []
            
            mock_query.all = mock_all
            mock_session.query.return_value = mock_query
            
            result = get_wallet_erc20_transfer_summary(
                wallet_address="0x1234567890123456789012345678901234567890"
            )
            
            # 验证USDT的小数处理
            token_detail = result['token_details'][0]
            assert token_detail['token_decimals'] == 6
            assert token_detail['total_received_formatted'] == '1'  # 1000000 / 10^6 = 1.0


def test_address_format_validation():
    """测试地址格式验证的独立函数"""
    from common.utils.format_utils import is_hex_address
    
    # 测试有效地址
    assert is_hex_address("0x1234567890123456789012345678901234567890") == True
    assert is_hex_address("0xabcdefABCDEF1234567890123456789012345678") == True
    
    # 测试无效地址
    assert is_hex_address("invalid_address") == False
    assert is_hex_address("0x123") == False  # 太短
    assert is_hex_address("1234567890123456789012345678901234567890") == False  # 缺少0x前缀


if __name__ == "__main__":
    # 运行特定测试
    pytest.main([__file__, "-v"]) 