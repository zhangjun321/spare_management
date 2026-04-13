"""
数据库迁移执行脚本
"""

from app import create_app, db
from app.models.warehouse_v3 import *

app = create_app()

with app.app_context():
    try:
        # 创建所有表
        db.create_all()
        print("[OK] 数据库表创建完成！")
        
        # 验证表是否存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n当前数据库中的表:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # 特别检查新增的表
        new_tables = ['quality_check_standard', 'picking_wave', 'wave_strategy', 
                     'inventory_check_plan', 'inventory_check_analysis', 'warning_notification']
        
        print(f"\n新增表检查:")
        for table in new_tables:
            if table in tables:
                print(f"  [OK] {table}")
            else:
                print(f"  [FAIL] {table} (未创建)")
        
        print("\n数据库初始化完成！")
        
    except Exception as e:
        print(f"[ERROR] 错误：{e}")
        import traceback
        traceback.print_exc()
