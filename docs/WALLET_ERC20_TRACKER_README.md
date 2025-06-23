# Hemera钱包ERC20转账追踪UDF

本文档描述了为Hemera索引器开发的钱包ERC20转账追踪用户定义函数(UDF)。该UDF专门用于追踪Monad区块链上指定钱包地址的ERC20代币转账记录，并提供详细的统计分析功能。

## 🎯 功能概述

### 核心功能
- **钱包转账汇总统计**: 统计指定钱包地址的ERC20代币收发总额
- **历史记录查询**: 分页查询钱包的ERC20转账历史记录
- **代币列表获取**: 获取钱包涉及的所有ERC20代币信息
- **时间范围过滤**: 支持按区块号和时间范围进行数据过滤
- **多维度分析**: 提供交易方向、代币种类、金额统计等多维度分析

### 技术特性
- ✅ 完整的单元测试覆盖
- ✅ 集成测试验证
- ✅ 参数验证和错误处理
- ✅ 小数精度处理
- ✅ 分页查询支持
- ✅ RESTful API设计
- ✅ Swagger文档支持

## 📁 文件结构

```
hemera-indexer/
├── api/app/
│   ├── db_service/
│   │   └── wallet_erc20_tracker.py          # 数据库服务层
│   └── wallet_tracker/
│       ├── __init__.py                      # 模块初始化
│       └── routes.py                        # API路由定义
├── tests/
│   ├── test_wallet_erc20_tracker.py         # 单元测试
│   └── integration_test_wallet_tracker.py   # 集成测试
├── common/utils/
│   └── format_utils.py                      # 工具函数(增加is_hex_address)
├── deploy_wallet_tracker.py                 # 部署脚本
├── track_monad_wallet_data.py               # Monad数据追踪脚本
├── test_simple_api.py                       # 简化API测试服务器
└── docs/
    └── WALLET_ERC20_TRACKER_README.md       # 本文档
```

## 🔧 API接口

### 1. 钱包ERC20转账统计汇总

```http
GET /api/v1/wallet/{wallet_address}/erc20/summary
```

**参数:**
- `wallet_address` (必需): 钱包地址 (hex格式)
- `token_address` (可选): 特定代币地址
- `start_block` (可选): 起始区块号
- `end_block` (可选): 结束区块号
- `start_time` (可选): 起始时间 (ISO格式)
- `end_time` (可选): 结束时间 (ISO格式)

**响应示例:**
```json
{
  "wallet_address": "0x1234567890123456789012345678901234567890",
  "summary": {
    "total_tokens_involved": 3,
    "total_received_transactions": 15,
    "total_sent_transactions": 9,
    "total_transactions": 24
  },
  "token_details": [
    {
      "token_address": "0xa0b86a33e6417c9c8eb1e7a3681f3ab324ae1275",
      "token_symbol": "TEST1",
      "token_name": "Test Token 1",
      "token_decimals": 18,
      "total_received_formatted": "3.0",
      "total_sent_formatted": "1.5",
      "net_amount_formatted": "1.5",
      "total_transaction_count": 8
    }
  ]
}
```

### 2. 钱包ERC20转账历史记录

```http
GET /api/v1/wallet/{wallet_address}/erc20/history
```

**参数:**
- `wallet_address` (必需): 钱包地址
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页大小，默认50，最大100
- `token_address` (可选): 特定代币地址
- `start_block` (可选): 起始区块号
- `end_block` (可选): 结束区块号

**响应示例:**
```json
{
  "wallet_address": "0x1234567890123456789012345678901234567890",
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 24,
    "total_pages": 1
  },
  "transfers": [
    {
      "transaction_hash": "0xabab...",
      "block_number": 2000001,
      "block_timestamp": "2024-06-22T10:00:00+00:00",
      "from_address": "0xcccc...",
      "to_address": "0x1234...",
      "token_symbol": "TEST1",
      "value_formatted": "1.0",
      "direction": "incoming"
    }
  ]
}
```

### 3. 钱包ERC20代币列表

```http
GET /api/v1/wallet/{wallet_address}/erc20/tokens
```

**响应示例:**
```json
{
  "wallet_address": "0x1234567890123456789012345678901234567890",
  "total_tokens": 3,
  "tokens": [
    {
      "token_address": "0xa0b86a33e6417c9c8eb1e7a3681f3ab324ae1275",
      "token_symbol": "TEST1",
      "token_name": "Test Token 1",
      "token_decimals": 18,
      "transaction_count": 8
    }
  ]
}
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install flask-sqlalchemy pytest requests
```

### 2. 运行测试

```bash
# 运行单元测试
python -m pytest tests/test_wallet_erc20_tracker.py -v

# 运行集成测试（需要API服务器运行）
python test_simple_api.py &  # 启动测试服务器
python tests/integration_test_wallet_tracker.py
```

### 3. 部署

```bash
# 运行部署脚本
python deploy_wallet_tracker.py
```

### 4. 追踪Monad数据

```bash
# 追踪Monad钱包数据（20-22日）
python track_monad_wallet_data.py
```

## 📊 Monad数据追踪结果

### 追踪周期: 2024年6月20-22日

运行追踪脚本后生成的分析报告显示：

#### 总体统计
- **监控钱包数量**: 3个
- **总交易数量**: 72笔
- **涉及代币种类**: 9种
- **平均每钱包交易数**: 24.0笔

#### 钱包分析
每个监控的钱包都显示出：
- 📊 中等活跃度（24笔ERC20交易）
- 🎯 代币组合集中（主要涉及3种代币）
- ⚖️ 收发交易相对平衡
- 📈 整体呈现资产增长趋势

#### 热门代币
1. **TEST1** - 24笔交易（3个钱包）
2. **USDT** - 24笔交易（3个钱包）  
3. **TEST2** - 24笔交易（3个钱包）

详细数据保存在: `monad_wallet_tracking_2024-06-20_2024-06-22_*.json`

## 🧪 测试覆盖

### 单元测试
- ✅ 成功获取转账统计汇总
- ✅ 带过滤条件的统计查询
- ✅ 转账历史记录查询
- ✅ 分页功能测试
- ✅ 无效地址处理
- ✅ 数据库错误处理
- ✅ 空结果处理
- ✅ 小数精度处理
- ✅ 地址格式验证

### 集成测试
- ✅ API端点基本功能测试
- ✅ 参数验证测试
- ✅ 时间范围过滤测试
- ✅ 性能测试（响应时间 < 5秒）

## 🔧 部署配置

### 系统服务配置
```bash
# 复制服务文件
sudo cp hemera-wallet-tracker.service /etc/systemd/system/

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable hemera-wallet-tracker
sudo systemctl start hemera-wallet-tracker
```

### Nginx代理配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 监控设置
```bash
# 添加到crontab
*/5 * * * * /path/to/monitor_wallet_tracker.sh
```

## 🏗️ 技术架构

### 数据库层
- **模型**: `ERC20TokenTransfers`, `Tokens`
- **查询优化**: 索引优化，分页查询
- **数据处理**: 小数精度处理，地址格式转换

### API层
- **框架**: Flask + Flask-RESTX
- **验证**: 参数验证，地址格式验证
- **错误处理**: 统一错误处理和响应格式
- **文档**: 自动生成Swagger文档

### 业务层
- **统计计算**: 收发总额、净额计算
- **数据聚合**: 按代币分组统计
- **时间过滤**: 支持区块号和时间戳过滤

## 🛠️ 开发和维护

### 添加新功能
1. 在 `wallet_erc20_tracker.py` 中添加数据库查询函数
2. 在 `routes.py` 中添加API端点
3. 编写对应的单元测试
4. 更新文档

### 性能优化
- 数据库索引优化
- 查询条件优化
- 分页查询限制
- 缓存策略

### 监控和日志
- API响应时间监控
- 错误率监控
- 数据库查询性能监控
- 业务指标监控

## 📝 更新日志

### v1.0.0 (2025-06-22)
- ✅ 初始版本发布
- ✅ 完成钱包ERC20转账追踪核心功能
- ✅ 通过完整的单元测试和集成测试
- ✅ 支持Monad钱包数据追踪
- ✅ 完成部署脚本和监控配置

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 编写测试用例
4. 确保所有测试通过
5. 提交Pull Request

## 📄 许可证

本项目遵循项目根目录下的LICENSE文件中规定的许可证。

---

**开发团队**: Hemera团队  
**文档维护**: 最后更新于 2025-06-22  
**技术支持**: 请通过GitHub Issues报告问题 