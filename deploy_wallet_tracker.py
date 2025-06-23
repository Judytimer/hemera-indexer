#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
from datetime import datetime

def run_command(command, description):
    """运行命令并返回结果"""
    print(f"\n🔧 {description}")
    print(f"命令: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ {description} 成功")
        if result.stdout.strip():
            print(f"输出: {result.stdout.strip()}")
    else:
        print(f"✗ {description} 失败")
        print(f"错误: {result.stderr.strip()}")
        return False
    
    return True

def check_prerequisites():
    """检查部署前置条件"""
    print("📋 检查部署前置条件...")
    
    # 检查Python环境
    if not run_command("python --version", "检查Python版本"):
        return False
    
    # 检查虚拟环境
    if not run_command(".venv/bin/python -c 'import flask'", "检查Flask依赖"):
        return False
    
    # 检查数据库连接（如果配置了的话）
    print("✓ 前置条件检查完成")
    return True

def run_tests():
    """运行所有测试"""
    print("\n🧪 运行测试套件...")
    
    # 运行单元测试
    if not run_command(".venv/bin/python -m pytest tests/test_wallet_erc20_tracker.py -v", 
                      "运行单元测试"):
        return False
    
    print("✓ 所有测试通过")
    return True

def deploy_api():
    """部署API服务"""
    print("\n🚀 部署钱包追踪API...")
    
    # 检查API文件完整性
    api_files = [
        "api/app/db_service/wallet_erc20_tracker.py",
        "api/app/wallet_tracker/routes.py",
        "api/app/wallet_tracker/__init__.py"
    ]
    
    for file_path in api_files:
        if not os.path.exists(file_path):
            print(f"✗ 关键文件缺失: {file_path}")
            return False
    
    print("✓ API文件检查完成")
    
    # 验证API注册
    if not run_command(".venv/bin/python -c 'from api.app.wallet_tracker.routes import wallet_tracker_namespace; print(\"Wallet tracker namespace:\", wallet_tracker_namespace.name)'",
                      "验证API注册"):
        return False
    
    print("✓ API部署检查完成")
    return True

def create_systemd_service():
    """创建systemd服务文件（可选）"""
    print("\n⚙️ 创建系统服务配置...")
    
    service_content = f"""[Unit]
Description=Hemera钱包追踪API服务
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'hemera')}
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/.venv/bin
ExecStart={os.getcwd()}/.venv/bin/python start_api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "hemera-wallet-tracker.service"
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✓ 服务配置文件已创建: {service_file}")
    print(f"  要安装系统服务，请运行:")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print(f"  sudo systemctl daemon-reload")
    print(f"  sudo systemctl enable hemera-wallet-tracker")
    print(f"  sudo systemctl start hemera-wallet-tracker")
    
    return True

def create_nginx_config():
    """创建Nginx配置示例"""
    print("\n🌐 创建Nginx配置示例...")
    
    nginx_content = """server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
    
    nginx_file = "nginx-wallet-tracker.conf"
    with open(nginx_file, 'w') as f:
        f.write(nginx_content)
    
    print(f"✓ Nginx配置文件已创建: {nginx_file}")
    print(f"  要使用此配置，请将文件复制到 /etc/nginx/sites-available/ 并启用")
    
    return True

def create_monitoring_script():
    """创建监控脚本"""
    print("\n📊 创建监控脚本...")
    
    monitoring_content = """#!/bin/bash
# Hemera钱包追踪API监控脚本

API_URL="http://localhost:5000"
LOG_FILE="/var/log/hemera-wallet-tracker-monitor.log"

# 健康检查
check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
    if [ "$response" = "200" ]; then
        echo "$(date): API健康检查 - OK" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): API健康检查 - FAILED (HTTP $response)" >> "$LOG_FILE"
        return 1
    fi
}

# 测试API端点
test_api() {
    test_wallet="0x1234567890123456789012345678901234567890"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/wallet/$test_wallet/erc20/summary")
    if [ "$response" = "200" ]; then
        echo "$(date): API功能测试 - OK" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): API功能测试 - FAILED (HTTP $response)" >> "$LOG_FILE"
        return 1
    fi
}

# 主监控循环
main() {
    if check_health && test_api; then
        echo "$(date): 监控检查通过" >> "$LOG_FILE"
        exit 0
    else
        echo "$(date): 监控检查失败，需要人工介入" >> "$LOG_FILE"
        # 可以在这里添加重启服务的逻辑
        exit 1
    fi
}

main
"""
    
    monitoring_file = "monitor_wallet_tracker.sh"
    with open(monitoring_file, 'w') as f:
        f.write(monitoring_content)
    
    os.chmod(monitoring_file, 0o755)
    
    print(f"✓ 监控脚本已创建: {monitoring_file}")
    print(f"  可以将此脚本添加到crontab中定期运行:")
    print(f"  */5 * * * * {os.getcwd()}/{monitoring_file}")
    
    return True

def main():
    """主部署流程"""
    print("=" * 60)
    print("🚀 Hemera钱包ERC20追踪功能部署脚本")
    print("=" * 60)
    print(f"部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"部署目录: {os.getcwd()}")
    
    # 检查前置条件
    if not check_prerequisites():
        print("\n❌ 前置条件检查失败，部署中止")
        return 1
    
    # 运行测试
    if not run_tests():
        print("\n❌ 测试失败，部署中止")
        return 1
    
    # 部署API
    if not deploy_api():
        print("\n❌ API部署失败")
        return 1
    
    # 创建配置文件
    create_systemd_service()
    create_nginx_config()
    create_monitoring_script()
    
    print("\n" + "=" * 60)
    print("✅ 部署完成！")
    print("=" * 60)
    
    print("\n📋 部署摘要:")
    print("1. ✓ 单元测试通过")
    print("2. ✓ API文件部署完成")
    print("3. ✓ 系统服务配置已创建")
    print("4. ✓ Nginx配置示例已创建")
    print("5. ✓ 监控脚本已创建")
    
    print("\n🔗 API端点:")
    print("- 钱包转账汇总: POST /api/v1/wallet/{address}/erc20/summary")
    print("- 转账历史记录: GET /api/v1/wallet/{address}/erc20/history")
    print("- 代币列表: GET /api/v1/wallet/{address}/erc20/tokens")
    print("- 健康检查: GET /health")
    print("- API文档: GET /api")
    
    print("\n📚 后续步骤:")
    print("1. 配置数据库连接（修改 api_config.yaml）")
    print("2. 根据需要安装系统服务")
    print("3. 配置Nginx代理")
    print("4. 设置监控和日志")
    print("5. 进行生产环境测试")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 