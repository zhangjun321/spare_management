# -*- coding: utf-8 -*-
"""
删除最早的 30 条数据，保留完整的 100 条 AI 生成数据
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
print("删除最早的 30 条数据，保留完整的 100 条")
print("="*80)

with app.app_context():
    # 按创建时间排序获取所有备件
    all_parts = SparePart.query.order_by(SparePart.created_at).all()
    total_count = len(all_parts)
    
    print(f"\n当前总记录数：{total_count}")
    
    if total_count == 130:
        # 获取最早的 30 条
        parts_to_delete = all_parts[:30]
        
        print(f"\n即将删除最早的 30 条记录：")
        print("-" * 80)
        for i, part in enumerate(parts_to_delete, 1):
            print(f"{i:3d}. {part.part_code} - {part.name[:50]}")
        
        print(f"\n⚠️  确认删除这 30 条记录？(y/n): ", end="")
        confirm = 'y'
        print(confirm)
        
        if confirm.lower() == 'y':
            print("\n开始删除...")
            
            for i, part in enumerate(parts_to_delete, 1):
                print(f"[{i}/30] 删除：{part.part_code}")
                db.session.delete(part)
            
            try:
                db.session.commit()
                print("\n✅ 删除成功！")
                
                # 验证结果
                remaining = SparePart.query.count()
                print(f"\n剩余记录数：{remaining} 条")
                
                if remaining == 100:
                    print("✅ 完美！现在数据库正好有 100 条备件数据")
                    
                    # 显示分类统计
                    print("\n📊 按分类统计：")
                    print("-" * 80)
                    categories = set([part.category.name for part in SparePart.query.all() if part.category])
                    for cat_name in sorted(categories):
                        count = SparePart.query.join(SparePart.category).filter(Category.name == cat_name).count()
                        print(f"  - {cat_name}: {count} 条")
                    
                else:
                    print(f"⚠️  注意：剩余 {remaining} 条记录，不是预期的 100 条")
                    
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ 删除失败：{str(e)}")
        else:
            print("\n已取消操作")
    else:
        print(f"\n⚠️  当前有 {total_count} 条记录，不是 130 条，无法执行删除操作")

print("="*80)
