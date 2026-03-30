#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查备件数据
"""

from app.extensions import db
from app.models.spare_part import SparePart
from app.models.category import Category

# 初始化应用上下文
from app import create_app
app = create_app()

with app.app_context():
    print("=" * 70)
    print("备件数据检查")
    print("=" * 70)
    
    # 获取备件数量
    total_parts = SparePart.query.count()
    print(f"当前备件数量: {total_parts}")
    
    # 获取类别数量
    total_categories = Category.query.count()
    print(f"当前类别数量: {total_categories}")
    
    # 显示前10个备件
    print("\n前10个备件:")
    print("-" * 100)
    print(f"{'ID':<5} {'编码':<20} {'名称':<30} {'类别':<20} {'库存':<10}")
    print("-" * 100)
    
    parts = SparePart.query.limit(10).all()
    for part in parts:
        category_name = part.category.name if part.category else '未分类'
        print(f"{part.id:<5} {part.part_code:<20} {part.name:<30} {category_name:<20} {part.current_stock:<10}")
    
    print("-" * 100)
    
    # 显示所有类别
    print("\n所有类别:")
    print("-" * 50)
    categories = Category.query.all()
    for category in categories:
        print(f"ID: {category.id}, 名称: {category.name}, 描述: {category.description or '无'}")
    print("-" * 50)
