#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加系统监控表
运行方式：python scripts/migrate_add_monitor_table.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.system_monitor import SystemMonitor

def migrate():
    """执行迁移"""
    app = create_app()
    
    with app.app_context():
        try:
            print("开始创建系统监控表...")
            
            # 创建表
            db.create_all()
            
            print("System monitor table created successfully!")
            print("\nTable structure:")
            print("-" * 60)
            
            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if inspector.has_table('system_monitor'):
                print("Table: system_monitor")
                print("Columns:")
                for column in inspector.get_columns('system_monitor'):
                    print(f"  - {column['name']}: {column['type']} (nullable={column['nullable']})")
            else:
                print("Table creation failed!")
            
            print("-" * 60)
            print("\nMigration completed!")
            
        except Exception as e:
            print(f"\nMigration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
