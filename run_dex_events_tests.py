#!/usr/bin/env python3
"""
DEX Events Module 测试运行器

运行所有DEX Events相关的单元测试
"""

import os
import sys
import pytest
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """运行测试"""
    try:
        logger.info("🧪 开始运行 DEX Events 模块测试")
        
        # 测试文件路径
        test_paths = [
            "indexer/modules/custom/dex_events/tests/test_dex_abi.py",
            "indexer/modules/custom/dex_events/tests/test_dex_domain.py", 
            "indexer/modules/custom/dex_events/tests/test_dex_jobs.py"
        ]
        
        # 验证测试文件存在
        missing_files = []
        for test_path in test_paths:
            full_path = os.path.join(project_root, test_path)
            if not os.path.exists(full_path):
                missing_files.append(test_path)
        
        if missing_files:
            logger.error(f"❌ 找不到测试文件: {missing_files}")
            return 1
        
        # 运行pytest
        logger.info("📋 执行测试...")
        
        # pytest参数配置
        pytest_args = [
            "-v",  # 详细输出
            "-s",  # 显示print输出
            "--tb=short",  # 简短的traceback
            "--color=yes",  # 彩色输出
        ]
        
        # 添加测试路径
        pytest_args.extend(test_paths)
        
        # 执行测试
        exit_code = pytest.main(pytest_args)
        
        if exit_code == 0:
            logger.info("✅ 所有测试通过!")
        else:
            logger.error(f"❌ 测试失败，退出码: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"❌ 测试运行出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 