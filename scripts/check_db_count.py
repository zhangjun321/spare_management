# -*- coding: utf-8 -*-
"""
检查数据库备件数量
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.supplier import Supplier

app = create_app()

with app.app_context():
    # 统计备件数量
    part_count = SparePart.query.count()
    
    # 统计分类数量
    category_count = Category.query.count()
    
    # 统计供应商数量
    supplier_count = Supplier.query.count()
    
    print("="*80)
    print("数据库统计信息")
    print("="*80)
    print(f"✅ 备件总数：{part_count}")
    print(f"✅ 分类总数：{category_count}")
    print(f"✅ 供应商总数：{supplier_count}")
    print("="*80)
    
    # 按分类统计
    print("\n按分类统计：")
    categories = Category.query.all()
    for cat in categories:
        count = SparePart.query.filter_by(category_id=cat.id).count()
        if count > 0:
            print(f"  - {cat.name} ({cat.code}): {count} 条")
    
    print("="*80)
