# -*- coding: utf-8 -*-
"""
检查数据库中的 130 条数据，按创建时间排序
"""

import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models.spare_part import SparePart

app = create_app()

print("="*80)
print("检查备件数据（按创建时间排序）")
print("="*80)

with app.app_context():
    # 按创建时间排序获取所有备件
    all_parts = SparePart.query.order_by(SparePart.created_at).all()
    total_count = len(all_parts)
    
    print(f"\n当前总记录数：{total_count}")
    print("="*80)
    
    # 显示前 30 条（最早的）
    print("\n📋 最早的 30 条记录（可能是原有数据）：")
    print("-" * 80)
    for i, part in enumerate(all_parts[:30], 1):
        print(f"{i:3d}. {part.part_code} | {part.name[:40]:40s} | {part.created_at}")
    
    print("\n" + "="*80)
    
    # 显示最新的 10 条
    print("\n📋 最新的 10 条记录：")
    print("-" * 80)
    for i, part in enumerate(all_parts[-10:], total_count-9):
        print(f"{i:3d}. {part.part_code} | {part.name[:40]:40s} | {part.created_at}")
    
    print("\n" + "="*80)
    
    # 分析创建时间分布
    print("\n📊 创建时间分析：")
    print("-" * 80)
    
    if total_count >= 30:
        first_30_time = all_parts[29].created_at
        print(f"第 30 条记录时间：{first_30_time}")
        print(f"最后一条记录时间：{all_parts[-1].created_at}")
        
        # 统计不同时间段的数量
        early_count = 0
        late_count = 0
        
        for part in all_parts:
            if part.created_at <= first_30_time:
                early_count += 1
            else:
                late_count += 1
        
        print(f"\n早期数据：{early_count} 条")
        print(f"后期数据：{late_count} 条")

print("="*80)
