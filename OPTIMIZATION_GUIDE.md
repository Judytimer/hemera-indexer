# Hemera 项目优化指南
# Hemera Project Optimization Guide

本文档包含了对Hemera区块链索引器项目的全面优化改进建议和实施计划。

## 🚨 紧急修复已完成

### ✅ 1. API路由模块化重构
- **问题**: 原`routes.py`文件2375行，严重违反单一职责原则
- **解决方案**: 拆分为5个模块
  ```
  api/app/explorer/routes/
  ├── __init__.py      # 路由注册
  ├── blocks.py        # 区块相关API
  ├── transactions.py  # 交易相关API  
  ├── tokens.py        # 代币相关API
  ├── contracts.py     # 合约相关API
  └── stats.py         # 统计相关API
  ```

### ✅ 2. 安全漏洞修复
已升级以下有安全漏洞的依赖包：
- `Flask-CORS`: 3.0.9 → 6.0.1 (修复CVE-2024-6221)
- `pandas`: 1.5.3 → 2.3.0 (修复CVE-2024-42992相关问题)
- `web3`: 6.20.3 → 7.12.0 (大版本升级，性能和安全改进)
- `numpy`: 1.24.4 → 2.3.1 (最新稳定版)

## 🚀 性能优化已实施

### ✅ 3. 数据库连接池优化
**原配置 → 优化后配置:**
- 最小连接数: 2 → 10
- 最大连接数: 10 → 50
- 连接池大小: 10 → 50
- 最大溢出: 10 → 30
- 连接超时: 30s → 60s
- 连接回收: 1800s → 3600s

### ✅ 4. RPC批量处理优化
创建了`optimized_multicall.py`，包含以下优化：
- **批量大小**: 默认值 → 500+
- **并发线程**: 5 → 20
- **请求去重**: 新增缓存机制
- **连接池复用**: 新增HTTP连接池
- **智能重试**: 指数退避 + 错误类型区分

### ✅ 5. 数据库批量导出优化
创建了`optimized_postgres_exporter.py`，包含：
- **批量提交大小**: 1000 → 10000
- **UPSERT支持**: 处理重复键
- **内存管理**: 智能缓冲区管理
- **并行插入**: 多线程批量处理

## 📋 代码质量流程已建立

### ✅ 6. 自动化代码检查
建立了完整的代码质量检查流程：

#### CI/CD Pipeline (`.github/workflows/code-quality.yml`)
- **安全检查**: Safety + pip-audit
- **类型检查**: MyPy
- **代码风格**: Ruff + Black + isort
- **测试覆盖率**: pytest + coverage (最低60%)

#### Pre-commit Hooks (`.pre-commit-config.yaml`)
- **代码格式化**: Black, Ruff, isort
- **类型检查**: MyPy
- **安全扫描**: Bandit, detect-secrets
- **基础检查**: 尾随空格、文件大小、YAML格式等

#### 配置文件
- `mypy.ini`: 类型检查配置
- `ruff.toml`: 现代Python linting
- `pytest.ini`: 测试和覆盖率配置

## 📈 性能对比预期

### 数据库性能提升
- **连接池容量**: 5倍提升 (10 → 50)
- **批量插入**: 10倍提升 (1000 → 10000条/批)
- **预期吞吐量**: 3-5倍提升

### RPC调用性能提升  
- **并发能力**: 4倍提升 (5 → 20线程)
- **批量大小**: 5-10倍提升
- **缓存命中**: 预期30-50%缓存命中率
- **预期响应时间**: 50-70%减少

### 内存使用优化
- **智能缓冲**: 防止内存溢出
- **垃圾回收**: 定期强制GC
- **预期内存使用**: 30-40%减少

## 🔧 使用新优化功能

### 1. 使用优化的API路由
```python
# 在主应用中注册新的模块化路由
from api.app.explorer.routes import register_routes

def create_app():
    app = Flask(__name__)
    register_routes(app)  # 注册新的模块化路由
    return app
```

### 2. 使用优化的数据库导出
```python
from indexer.exporters.optimized_postgres_exporter import OptimizedPostgresItemExporter

# 使用优化的导出器
exporter = OptimizedPostgresItemExporter(
    postgres_url="postgresql://user:pass@host:5432/db",
    optimized_batch_size=10000,  # 大批量
    enable_upsert=True,          # 启用UPSERT
    parallel_insert=True         # 并行插入
)

# 使用批处理器
with BatchProcessor(exporter, batch_size=10000) as processor:
    for item in data_items:
        processor.add_item(item)
# 自动刷新所有缓冲区
```

### 3. 使用优化的RPC调用
```python
from indexer.utils.optimized_multicall import OptimizedMultiCallHelper

# 使用优化的多重调用
helper = OptimizedMultiCallHelper(
    web3,
    kwargs={
        "batch_size": 500,      # 大批量
        "max_workers": 20,      # 高并发
        "timeout": 30,
        "retry_attempts": 3
    }
)

# 执行优化的批量调用
optimized_calls = helper.execute_calls_optimized(calls)

# 获取性能统计
stats = helper.get_performance_stats()
print(f"缓存命中率: {stats['cached_requests']/stats['total_requests']*100:.1f}%")
```

### 4. 使用性能配置
```python
# 加载优化配置
import yaml

with open('config/performance-optimized.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 应用数据库配置
db_config = config['database']
service = PostgreSQLService(
    jdbc_url="postgresql://...",
    pool_size=db_config['pool_size'],
    max_overflow=db_config['max_overflow'],
    pool_timeout=db_config['pool_timeout']
)
```

## 🛠 开发工作流程

### 本地开发设置
```bash
# 1. 安装pre-commit hooks
pip install pre-commit
pre-commit install

# 2. 运行代码质量检查
ruff check indexer/ common/ api/ cli/
black --check indexer/ common/ api/ cli/
mypy indexer/ common/ api/ cli/

# 3. 运行测试
pytest --cov=indexer --cov=common --cov=api --cov=cli

# 4. 安全检查  
safety check
pip-audit --desc
```

### 提交代码流程
1. **自动格式化**: pre-commit hooks自动运行
2. **类型检查**: MyPy验证类型注解
3. **安全扫描**: Bandit检查安全问题
4. **测试运行**: pytest确保功能正常
5. **CI/CD**: GitHub Actions运行完整检查

## 📊 监控和度量

### 性能监控
```python
# 使用内置的性能统计
from indexer.utils.optimized_multicall import OptimizedMultiCallHelper

helper = OptimizedMultiCallHelper(web3)
# ... 执行调用 ...

# 获取性能报告
stats = helper.get_performance_stats()
print(f"总请求: {stats['total_requests']}")
print(f"缓存命中率: {stats['cached_requests']/stats['total_requests']*100:.1f}%")
print(f"平均执行时间: {stats['total_time']/stats['total_requests']:.3f}s")
```

### 数据库性能监控
```python
from indexer.exporters.optimized_postgres_exporter import OptimizedPostgresItemExporter

exporter = OptimizedPostgresItemExporter("postgresql://...")
# ... 执行导出 ...

# 获取性能统计
stats = exporter.get_performance_stats() 
print(f"吞吐量: {stats['total_exported']/stats['total_time']:.1f} 条/秒")
print(f"内存刷新次数: {stats['memory_flushes']}")
```

## 🎯 下一步优化计划

### 近期目标 (1-2周)
1. **类型注解完善**: 为核心模块添加完整类型注解
2. **测试覆盖率提升**: 目标达到80%以上
3. **配置管理重构**: 使用Pydantic替代手动配置解析

### 中期目标 (1-2个月)  
1. **异步处理**: 引入asyncio提升I/O密集型操作
2. **缓存策略**: 实现Redis分布式缓存
3. **监控告警**: 添加Prometheus指标和Grafana面板

### 长期目标 (3-6个月)
1. **技术栈升级**: 评估迁移到FastAPI
2. **微服务架构**: 拆分为独立的服务组件
3. **容器化优化**: 优化Docker配置和K8s部署

## 📚 参考资源

- [Python类型提示指南](https://docs.python.org/3/library/typing.html)
- [SQLAlchemy性能优化](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [Flask最佳实践](https://flask.palletsprojects.com/en/2.0.x/patterns/)
- [Web3.py文档](https://web3py.readthedocs.io/)

## 🤝 贡献指南

1. **提交PR前**: 确保通过所有pre-commit检查
2. **代码审查**: 关注性能影响和安全问题
3. **测试要求**: 新功能必须有80%以上的测试覆盖率
4. **文档更新**: 重要变更需要更新相关文档

---

**记住**: 优秀的软件不是一次写成的，而是不断重构和优化出来的。这些改进只是开始，持续的优化和监控才是保持项目健康的关键。