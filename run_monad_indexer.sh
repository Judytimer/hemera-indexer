#!/bin/bash

# 激活虚拟环境
source .venv/bin/activate

# Monad 测试网配置
MONAD_RPC="https://testnet-rpc.monad.xyz"
POSTGRES_URL="postgresql://devuser:devpassword@localhost:5432/hemera_indexer"

# 创建输出目录
mkdir -p output/monad_testnet/{json,csv}

echo "开始连接 Monad 测试网并运行 Hemera Indexer..."
echo "RPC 端点: $MONAD_RPC"
echo "数据库: $POSTGRES_URL"

# 运行 Hemera Indexer
python hemera.py stream \
    --provider-uri $MONAD_RPC \
    --debug-provider-uri $MONAD_RPC \
    --postgres-url $POSTGRES_URL \
    --output jsonfile://output/monad_testnet/json,csvfile://output/monad_testnet/csv,postgresql://devuser:devpassword@localhost:5432/hemera_indexer \
    --start-block 1 \
    --end-block 100 \
    --entity-types EXPLORER_BASE \
    --block-batch-size 10 \
    --batch-size 10 \
    --max-workers 4

echo "Indexer 运行完成！" 