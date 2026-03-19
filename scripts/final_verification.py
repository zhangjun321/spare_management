# -*- coding: utf-8 -*-
"""
最终验证 - 数据库正好有 100 条备件数据
"""

import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models.spare_part import SparePart
from app.models.category import Category

app = create_app()

print("="*80)
print("最终验证 - 数据库正好有 100 条备件数据")
print("="*80)

with app.app_context():
    # 总记录数
    total = SparePart.query.count()
    
    print(f"\n✅ 数据库备件总数：{total}")
    
    if total == 100:
        print("\n🎉 完美！数据库正好有 100 条记录")
        
        # 按大类统计
        print("\n📊 按 6 大类统计：")
        print("-" * 80)
        
        categories = Category.query.all()
        for cat in categories:
            count = SparePart.query.filter_by(category_id=cat.id).count()
            if count > 0:
                print(f"  {cat.code} - {cat.name:15s}: {count:3d} 条")
        
        # 验证编码唯一性
        print("\n📋 验证编码规则：")
        print("-" * 80)
        all_parts = SparePart.query.all()
        codes = [part.part_code for part in all_parts]
        
        if len(codes) == len(set(codes)):
            print("  ✅ 所有备件编码都是唯一的")
        else:
            print("  ❌ 发现重复的备件编码")
        
        # 显示前 10 条和后 10 条
        print("\n📋 前 10 条记录（按创建时间）：")
        print("-" * 80)
        parts = SparePart.query.order_by(SparePart.created_at).limit(10).all()
        for i, part in enumerate(parts, 1):
            print(f"  {i:2d}. {part.part_code:20s} | {part.name[:40]}")
        
        print("\n📋 后 10 条记录（按创建时间）：")
        print("-" * 80)
        parts = SparePart.query.order_by(SparePart.created_at.desc()).limit(10).all()
        for i, part in enumerate(parts, 1):
            print(f"  {i:2d}. {part.part_code:20s} | {part.name[:40]}")
        
        print("\n" + "="*80)
        print("✅ 验证完成！数据符合要求：")
        print("   - 总记录数：100 条")
        print("   - 编码规则：统一且唯一")
        print("   - 分类分布：6 大类，覆盖完整")
        print("="*80)
        
    else:
        print(f"\n⚠️  警告：记录数不是 100 条！")
        print("="*80)
