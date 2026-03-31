#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加数据库备份表
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

def migrate():
    """执行迁移"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating database backup table...")
            
            db.create_all()
            
            print("Database backup table created successfully!")
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
