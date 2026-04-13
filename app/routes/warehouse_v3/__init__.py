"""
仓库管理 V3 模块 - 路由层
基于百度千帆 AI 的智能化仓库管理系统
"""

from flask import Blueprint

warehouse_v3_bp = Blueprint('warehouse_v3', __name__, url_prefix='/api/v1/warehouse')

# 导入路由
from . import warehouse_routes
from . import location_routes
from . import inventory_routes
from . import inbound_routes
from . import outbound_routes
from . import ai_routes
