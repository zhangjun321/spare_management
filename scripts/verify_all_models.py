"""
验证所有模型字段是否与数据库匹配
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import *
from sqlalchemy import inspect

app = create_app()

def check_model_table(model_class):
    """检查模型类对应的表字段"""
    model_name = model_class.__name__
    table_name = model_class.__tablename__
    
    # 获取模型字段
    model_columns = set()
    for attr in dir(model_class):
        if isinstance(getattr(model_class, attr), db.Column):
            model_columns.add(attr)
    
    # 获取数据库表字段
    with app.app_context():
        inspector = inspect(db.engine)
        db_columns = set([col['name'] for col in inspector.get_columns(table_name)])
    
    # 比较
    missing_in_db = model_columns - db_columns
    extra_in_db = db_columns - model_columns
    
    if missing_in_db or extra_in_db:
        print(f"\n⚠ {model_name} ({table_name}):")
        if missing_in_db:
            print(f"   缺失字段：{', '.join(missing_in_db)}")
        if extra_in_db:
            print(f"   多余字段：{', '.join(extra_in_db)}")
        return False
    else:
        print(f"✓ {model_name} ({table_name}) - 字段匹配")
        return True

def main():
    print("=" * 60)
    print("验证所有模型字段")
    print("=" * 60)
    
    # 获取所有模型类
    models = [
        SparePart, Category, Supplier, Equipment,
        Warehouse, Batch, Transaction, TransactionDetail,
        WarehouseLocation, SerialNumber,
        MaintenanceOrder, MaintenanceTask, MaintenanceRecord, MaintenanceCost,
        PurchasePlan, PurchaseRequest, PurchaseOrder, PurchaseOrderItem, PurchaseQuote,
        User, Role, Department,
        SupplierEvaluation,
        Tag, Alert, AlertRule, Notification, EmailConfig,
        SystemLog, DeletionLog
    ]
    
    all_ok = True
    for model in models:
        if not check_model_table(model):
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ 所有模型字段与数据库完全匹配！")
    else:
        print("⚠ 发现字段不匹配，请检查上述输出")
    print("=" * 60)

if __name__ == '__main__':
    main()
