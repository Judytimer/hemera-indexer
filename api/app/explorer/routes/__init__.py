#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Modular API routes for Hemera Explorer
重构后的模块化API路由结构
"""

from flask import Blueprint
from flask_restx import Api

# 创建主要的 API Blueprint
explorer_bp = Blueprint('explorer', __name__, url_prefix='/api/v1')
api = Api(explorer_bp, doc='/docs/', title='Hemera Explorer API', version='1.0')

# 导入各个模块的路由
from .blocks import blocks_ns
from .transactions import transactions_ns
from .tokens import tokens_ns
from .contracts import contracts_ns
from .stats import stats_ns

# 注册命名空间
api.add_namespace(blocks_ns, path='/blocks')
api.add_namespace(transactions_ns, path='/transactions')  
api.add_namespace(tokens_ns, path='/tokens')
api.add_namespace(contracts_ns, path='/contracts')
api.add_namespace(stats_ns, path='/stats')

# 为了保持向后兼容性，保留原有的路由注册方式
def register_routes(app):
    """注册所有路由到Flask应用"""
    app.register_blueprint(explorer_bp)