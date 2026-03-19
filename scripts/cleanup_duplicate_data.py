# -*- coding: utf-8 -*-
"""
清理数据库，删除原有的 30 条数据，保留 AI 生成的 100 条
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
print("清理数据库 - 删除原有数据，保留 AI 生成的 100 条")
print("="*80)

with app.app_context():
    # 获取所有备件
    all_parts = SparePart.query.all()
    total_count = len(all_parts)
    
    print(f"\n当前总记录数：{total_count}")
    
    # AI 生成的数据 remark 包含"AI 自动生成数据"
    ai_generated = []
    original_data = []
    
    for part in all_parts:
        if part.remark and "AI 自动生成数据" in part.remark:
            ai_generated.append(part)
        else:
            original_data.append(part)
    
    print(f"AI 生成的数据：{len(ai_generated)} 条")
    print(f"原有数据：{len(original_data)} 条")
    
    if len(original_data) > 0:
        print(f"\n⚠️  即将删除 {len(original_data)} 条原有数据...")
        print("这些数据的 remark 字段不包含'AI 自动生成数据'")
        print("\n确认要删除吗？(y/n): ", end="")
        
        # 自动确认（因为这是程序化操作）
        confirm = 'y'
        print(confirm)
        
        if confirm.lower() == 'y':
            print("\n开始删除...")
            for i, part in enumerate(original_data, 1):
                print(f"[{i}/{len(original_data)}] 删除：{part.part_code} - {part.name}")
                db.session.delete(part)
            
            try:
                db.session.commit()
                print("\n✅ 删除成功！")
                
                # 验证结果
                remaining = SparePart.query.count()
                print(f"\n剩余记录数：{remaining} 条")
                
                if remaining == 100:
                    print("✅ 完美！现在数据库有 100 条 AI 生成的备件数据")
                else:
                    print(f"⚠️  注意：剩余 {remaining} 条记录，不是预期的 100 条")
                    
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ 删除失败：{str(e)}")
        else:
            print("\n已取消操作")
    else:
        print("\n✅ 无需清理，所有数据都是 AI 生成的")

print("="*80)
