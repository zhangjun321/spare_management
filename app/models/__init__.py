"""
数据模型
导入所有模型以便 SQLAlchemy 识别
"""

from app.extensions import db

# 按依赖顺序导入所有模型
from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation
from app.models.spare_part import SparePart
from app.models.batch import Batch
from app.models.serial_number import SerialNumber
from app.models.transaction import Transaction, TransactionDetail
from app.models.equipment import Equipment
from app.models.maintenance import MaintenanceOrder, MaintenanceTask, MaintenanceRecord, MaintenanceCost
from app.models.purchase import PurchasePlan, PurchaseRequest, PurchaseOrder, PurchaseOrderItem, PurchaseQuote
from app.models.supplier_evaluation import SupplierEvaluation
from app.models.system import Tag, Alert, AlertRule, Notification, EmailConfig
from app.models.deletion_log import DeletionLog
from app.models.system_log import SystemLog
from app.models.system_monitor import SystemMonitor

__all__ = [
    'db',
    'Role',
    'Department',
    'User',
    'Category',
    'Supplier',
    'Warehouse',
    'WarehouseLocation',
    'SparePart',
    'Batch',
    'SerialNumber',
    'Transaction',
    'TransactionDetail',
    'Equipment',
    'MaintenanceOrder',
    'MaintenanceTask',
    'MaintenanceRecord',
    'MaintenanceCost',
    'PurchasePlan',
    'PurchaseRequest',
    'PurchaseOrder',
    'PurchaseOrderItem',
    'PurchaseQuote',
    'SupplierEvaluation',
    'Tag',
    'Alert',
    'AlertRule',
    'Notification',
    'EmailConfig',
    'DeletionLog',
    'SystemLog',
    'SystemMonitor'
]
