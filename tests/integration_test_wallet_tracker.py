#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
import os
import time
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class WalletTrackerIntegrationTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_wallet = "0x1234567890123456789012345678901234567890"  # 测试钱包地址
        self.test_token = "0xA0b86a33E6417c9C8eb1E7A3681F3aB324AE1275"  # 测试代币地址
        
    def test_api_endpoints(self):
        """测试所有API端点的基本功能"""
        print("开始集成测试...")
        
        # 测试1: 钱包ERC20转账统计汇总
        print("\n1. 测试钱包ERC20转账统计汇总 API")
        summary_url = f"{self.base_url}/api/v1/wallet/{self.test_wallet}/erc20/summary"
        
        try:
            response = requests.get(summary_url, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✓ 汇总API测试成功")
                print(f"  - 钱包地址: {data.get('wallet_address', 'N/A')}")
                summary = data.get('summary', {})
                print(f"  - 涉及代币数量: {summary.get('total_tokens_involved', 0)}")
                print(f"  - 总交易数量: {summary.get('total_transactions', 0)}")
                print(f"  - 收入交易: {summary.get('total_received_transactions', 0)}")
                print(f"  - 支出交易: {summary.get('total_sent_transactions', 0)}")
                
                token_details = data.get('token_details', [])
                if token_details:
                    print(f"  - 代币详情数量: {len(token_details)}")
                    for token in token_details[:3]:  # 显示前3个代币
                        print(f"    * {token.get('token_symbol', 'UNKNOWN')}: {token.get('total_transaction_count', 0)} 笔交易")
            else:
                print(f"✗ 汇总API测试失败: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 汇总API连接失败: {e}")
        
        # 测试2: 钱包ERC20转账历史记录
        print("\n2. 测试钱包ERC20转账历史记录 API")
        history_url = f"{self.base_url}/api/v1/wallet/{self.test_wallet}/erc20/history"
        
        try:
            params = {"page": 1, "page_size": 10}
            response = requests.get(history_url, params=params, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✓ 历史记录API测试成功")
                pagination = data.get('pagination', {})
                print(f"  - 当前页: {pagination.get('page', 'N/A')}")
                print(f"  - 每页大小: {pagination.get('page_size', 'N/A')}")
                print(f"  - 总记录数: {pagination.get('total_count', 0)}")
                print(f"  - 总页数: {pagination.get('total_pages', 0)}")
                
                transfers = data.get('transfers', [])
                print(f"  - 当前页记录数: {len(transfers)}")
                
                if transfers:
                    for i, transfer in enumerate(transfers[:3]):  # 显示前3笔交易
                        print(f"    {i+1}. {transfer.get('token_symbol', 'UNKNOWN')} - {transfer.get('direction', 'N/A')} - {transfer.get('value_formatted', 'N/A')}")
            else:
                print(f"✗ 历史记录API测试失败: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 历史记录API连接失败: {e}")
        
        # 测试3: 钱包ERC20代币列表
        print("\n3. 测试钱包ERC20代币列表 API")
        tokens_url = f"{self.base_url}/api/v1/wallet/{self.test_wallet}/erc20/tokens"
        
        try:
            response = requests.get(tokens_url, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✓ 代币列表API测试成功")
                print(f"  - 代币总数: {data.get('total_tokens', 0)}")
                
                tokens = data.get('tokens', [])
                if tokens:
                    for i, token in enumerate(tokens[:5]):  # 显示前5个代币
                        print(f"    {i+1}. {token.get('token_symbol', 'UNKNOWN')} ({token.get('token_name', 'Unknown')}) - {token.get('transaction_count', 0)} 笔交易")
            else:
                print(f"✗ 代币列表API测试失败: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 代币列表API连接失败: {e}")
    
    def test_parameter_validation(self):
        """测试参数验证功能"""
        print("\n4. 测试参数验证")
        
        # 测试无效钱包地址
        invalid_wallet = "invalid_address"
        summary_url = f"{self.base_url}/api/v1/wallet/{invalid_wallet}/erc20/summary"
        
        try:
            response = requests.get(summary_url, timeout=10)
            if response.status_code == 400:
                print("✓ 无效钱包地址验证通过")
            else:
                print(f"✗ 无效钱包地址验证失败，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"✗ 参数验证测试连接失败: {e}")
        
        # 测试分页参数
        history_url = f"{self.base_url}/api/v1/wallet/{self.test_wallet}/erc20/history"
        
        try:
            # 测试无效页码
            params = {"page": 0, "page_size": 50}
            response = requests.get(history_url, params=params, timeout=10)
            if response.status_code == 400:
                print("✓ 无效页码验证通过")
            else:
                print(f"✗ 无效页码验证失败，状态码: {response.status_code}")
                
            # 测试过大页面大小
            params = {"page": 1, "page_size": 200}
            response = requests.get(history_url, params=params, timeout=10)
            if response.status_code == 400:
                print("✓ 过大页面大小验证通过")
            else:
                print(f"✗ 过大页面大小验证失败，状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 分页参数验证测试连接失败: {e}")
    
    def test_time_range_filtering(self):
        """测试时间范围过滤功能"""
        print("\n5. 测试时间范围过滤")
        
        # 计算最近3天的时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=3)
        
        summary_url = f"{self.base_url}/api/v1/wallet/{self.test_wallet}/erc20/summary"
        
        try:
            params = {
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z"
            }
            
            response = requests.get(summary_url, params=params, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✓ 时间范围过滤测试成功")
                
                query_conditions = data.get('query_conditions', {})
                print(f"  - 查询开始时间: {query_conditions.get('start_time', 'N/A')}")
                print(f"  - 查询结束时间: {query_conditions.get('end_time', 'N/A')}")
                
                summary = data.get('summary', {})
                print(f"  - 时间范围内交易数: {summary.get('total_transactions', 0)}")
            else:
                print(f"✗ 时间范围过滤测试失败: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 时间范围过滤测试连接失败: {e}")
    
    def test_performance(self):
        """测试API性能"""
        print("\n6. 测试API性能")
        
        summary_url = f"{self.base_url}/api/v1/wallet/{self.test_wallet}/erc20/summary"
        
        try:
            start_time = time.time()
            response = requests.get(summary_url, timeout=60)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            print(f"响应时间: {response_time:.2f} ms")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('summary', {})
                total_transactions = summary.get('total_transactions', 0)
                
                if response_time < 5000:  # 5秒内
                    print("✓ 性能测试通过（响应时间 < 5秒）")
                else:
                    print("⚠ 性能警告（响应时间 >= 5秒）")
                
                print(f"  - 处理交易数量: {total_transactions}")
                print(f"  - 平均处理速度: {total_transactions / (response_time / 1000):.2f} 笔/秒")
            else:
                print(f"✗ 性能测试失败: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 性能测试连接失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("钱包ERC20追踪API集成测试")
        print("=" * 60)
        print(f"API服务器: {self.base_url}")
        print(f"测试钱包: {self.test_wallet}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.test_api_endpoints()
        self.test_parameter_validation()
        self.test_time_range_filtering()
        self.test_performance()
        
        print("\n" + "=" * 60)
        print("集成测试完成")
        print("=" * 60)


def main():
    """主函数"""
    # 检查API服务器是否在运行
    test_runner = WalletTrackerIntegrationTest()
    
    print("检查API服务器连接...")
    try:
        response = requests.get(f"{test_runner.base_url}/api", timeout=5)
        if response.status_code in [200, 404]:  # 404也表示服务器正在运行
            print("✓ API服务器连接正常")
        else:
            print(f"⚠ API服务器响应异常，状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ 无法连接到API服务器: {e}")
        print("请确保API服务器正在运行在 http://localhost:5000")
        return 1
    
    # 运行所有测试
    test_runner.run_all_tests()
    return 0


if __name__ == "__main__":
    sys.exit(main()) 