#!/usr/bin/env python
"""
修复 email_config 表结构
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("开始修复 email_config 表结构...")
    
    # 执行 SQL 删除可能存在的 config_name 列
    try:
        # 先检查列是否存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('email_config')]
        
        print(f"当前 email_config 表的列：{columns}")
        
        if 'config_name' in columns:
            # 删除 config_name 列
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE email_config DROP COLUMN config_name"))
                conn.commit()
            print("✓ 已删除 config_name 列")
        else:
            print("✓ config_name 列不存在，无需删除")
        
        # 检查是否有 created_at 和 updated_at
        if 'created_at' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE email_config ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'"))
                conn.commit()
            print("✓ 已添加 created_at 列")
        
        if 'updated_at' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE email_config ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'"))
                conn.commit()
            print("✓ 已添加 updated_at 列")
        
        print("\n表结构修复完成！")
        
    except Exception as e:
        print(f"✗ 修复失败：{str(e)}")
        import traceback
        traceback.print_exc()
