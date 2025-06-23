# DEX Events 模块

这个模块用于抓取去中心化交易所（DEX）的核心事件，包括：

## 支持的事件类型

### 1. Swap 事件 (交易事件)
- **Uniswap V2 风格**: `Swap(address indexed sender, uint amount0In, uint amount1In, uint amount0Out, uint amount1Out, address indexed to)`
- **Uniswap V3 风格**: `Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)`

### 2. Mint 事件 (添加流动性)
- **Uniswap V2 风格**: `Mint(address indexed sender, uint amount0, uint amount1)`
- **Uniswap V3 风格**: `Mint(address sender, address indexed owner, int24 indexed tickLower, int24 indexed tickUpper, uint128 amount, uint256 amount0, uint256 amount1)`

### 3. Burn 事件 (移除流动性)
- **Uniswap V2 风格**: `Burn(address indexed sender, uint amount0, uint amount1, address indexed to)`
- **Uniswap V3 风格**: `Burn(address indexed owner, int24 indexed tickLower, int24 indexed tickUpper, uint128 amount, uint256 amount0, uint256 amount1)`

### 4. PairCreated 事件 (交易对创建)
- **标准格式**: `PairCreated(address indexed token0, address indexed token1, address pair, uint)`

## 数据库表结构

### af_dex_swap_events
存储所有交易事件数据，包含V2和V3格式的字段。

### af_dex_mint_events
存储添加流动性事件数据。

### af_dex_burn_events
存储移除流动性事件数据。

### af_dex_pair_created_events
存储交易对创建事件数据。

## 使用方法

### 1. 配置数据库
确保PostgreSQL数据库已启动并且连接信息正确：
```bash
# 测试数据库连接
PGPASSWORD=hemera123 psql -h localhost -U devuser -d hemera_indexer
```

### 2. 运行索引器
```bash
cd hemera-indexer
python run_dex_events_indexer.py
```

### 3. 使用配置文件
```bash
python -m indexer.cli.api --config config/indexer-config-dex-events.yaml
```

## 配置选项

在 `config/indexer-config-dex-events.yaml` 中可以配置：

- `chain_id`: 区块链ID
- `pool_addresses`: 要监控的特定池地址（可选）
- `factory_addresses`: 要监控的工厂地址（用于PairCreated事件）
- `provider_uri`: 区块链RPC端点
- `batch_size`: 批处理大小
- `max_workers`: 最大工作线程数

## 查询示例

### 查询最近的交易事件
```sql
SELECT 
    pool_address,
    event_type,
    amount0_in, amount1_in, amount0_out, amount1_out,
    block_number,
    block_timestamp
FROM af_dex_swap_events 
ORDER BY block_timestamp DESC 
LIMIT 10;
```

### 查询流动性添加事件
```sql
SELECT 
    pool_address,
    sender,
    amount0, amount1,
    block_timestamp
FROM af_dex_mint_events 
WHERE event_type = 'mint_v2'
ORDER BY block_timestamp DESC 
LIMIT 10;
```

### 查询新创建的交易对
```sql
SELECT 
    factory_address,
    token0, token1,
    pair_address,
    block_timestamp
FROM af_dex_pair_created_events 
ORDER BY block_timestamp DESC 
LIMIT 10;
```

## 扩展支持

要添加对新DEX的支持：

1. 在 `dex_abi.py` 中添加新的事件ABI定义
2. 在相应的作业文件中添加对新事件签名的处理
3. 更新配置文件中的工厂地址列表

## 监控和日志

- 日志文件：`dex_events_indexer.log`
- 支持的日志级别：DEBUG, INFO, WARNING, ERROR
- 实时监控：查看控制台输出了解索引进度

## 性能优化

- 调整 `batch_size` 来优化性能
- 使用 `pool_addresses` 过滤器来减少处理的数据量
- 监控数据库性能并适当添加索引

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否运行
   - 验证数据库连接信息

2. **RPC连接问题**
   - 检查 `provider_uri` 是否正确
   - 验证网络连接

3. **事件解析错误**
   - 检查ABI定义是否与合约匹配
   - 查看日志文件了解具体错误

### 调试模式
```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
python run_dex_events_indexer.py
``` 