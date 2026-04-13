"""
仓库管理 V3 模块 - 数据模型层
基于百度千帆 AI 的智能化仓库管理系统
"""

from .warehouse import WarehouseV3
from .location import WarehouseLocationV3
from .inventory import InventoryV3
from .inbound import InboundOrderV3, InboundOrderItemV3
from .outbound import OutboundOrderV3, OutboundOrderItemV3
from .inventory_check import InventoryCheck, InventoryCheckItem
from .warning import WarningRule, WarningLog
from .quality_check import QualityCheck, QualityCheckItem, QualityCheckStandard

__all__ = [
    'WarehouseV3',
    'WarehouseLocationV3',
    'InventoryV3',
    'InboundOrderV3',
    'InboundOrderItemV3',
    'OutboundOrderV3',
    'OutboundOrderItemV3',
    'InventoryCheck',
    'InventoryCheckItem',
    'WarningRule',
    'WarningLog',
    'QualityCheck',
    'QualityCheckItem',
    'QualityCheckStandard'
]
