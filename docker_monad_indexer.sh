#!/bin/bash

echo "🐳 使用 Docker 运行 Hemera Indexer 连接 Monad 测试网"
echo "=================================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker 安装完成，请重新登录后再次运行此脚本"
    exit 1
fi

# 修改 docker-compose 配置
cat > docker-compose/hemera-indexer.env << EOF
# Monad 测试网配置
PROVIDER_URI=https://testnet-rpc.monad.xyz
DEBUG_PROVIDER_URI=https://testnet-rpc.monad.xyz
START_BLOCK=1
END_BLOCK=100
POSTGRES_URL=postgresql://user:password@postgresql:5432/postgres
OUTPUT=postgres

# PostgreSQL 数据库配置
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=postgres
EOF

echo "📝 配置文件已更新"

# 启动服务
echo "🚀 启动 Docker 服务..."
cd docker-compose
docker-compose up -d postgresql

echo "⏳ 等待 PostgreSQL 启动..."
sleep 10

echo "🔄 运行 Hemera Indexer..."
docker-compose up hemera-indexer

echo "✅ 完成！检查 docker-compose logs 查看详细日志" 