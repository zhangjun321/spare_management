# -*- coding: utf-8 -*-
"""
创建缺失的数据库表
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import *

def create_missing_tables():
    """创建缺失的表"""
    app = create_app()
    
    with app.app_context():
        print("正在创建缺失的数据库表...")
        db.create_all()
        print("✅ 数据库表创建完成！")
        
        # 检查表是否存在
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n当前数据库表列表:")
        for table in sorted(tables):
            print(f"  - {table}")

if __name__ == '__main__':
    create_missing_tables()
