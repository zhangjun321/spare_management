"""
仓库管理 V3 模块 - 服务层
基于百度千帆 AI 的智能化仓库管理系统
"""

from .warehouse_service import WarehouseV3Service
from .location_service import LocationV3Service
from .inventory_service import InventoryV3Service
from .inbound_service import InboundV3Service
from .outbound_service import OutboundV3Service
from .check_service import InventoryCheckService
from .ai_analysis_service import AIAnalysisV3Service

__all__ = [
    'WarehouseV3Service',
    'LocationV3Service',
    'InventoryV3Service',
    'InboundV3Service',
    'OutboundV3Service',
    'InventoryCheckService',
    'AIAnalysisV3Service'
]
