"""
仓库管理 V3 模块 - 路由层
基于百度千帆 AI 的智能化仓库管理系统
"""

from flask import Blueprint

warehouse_v3_bp = Blueprint('warehouse_v3', __name__, url_prefix='/api/v1/warehouse')

# 导入路由（已废弃的路由文件移至 app/_deprecated/）
from . import warehouse_routes
from . import inventory_routes
