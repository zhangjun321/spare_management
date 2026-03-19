# -*- coding: utf-8 -*-
"""
检查备件数据的编码规则和唯一性
"""

import sys
import os
import re
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 加载环境变量
load_dotenv()

os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models.spare_part import SparePart
from collections import Counter

app = create_app()

print("="*80)
print("检查备件数据编码规则和唯一性")
print("="*80)

with app.app_context():
    # 获取所有备件
    all_parts = SparePart.query.all()
    total_count = len(all_parts)
    
    print(f"\n📊 数据库总记录数：{total_count}")
    print("="*80)
    
    # 检查编码规则
    print("\n1️⃣ 检查备件代码编码规则")
    print("-" * 80)
    
    # 标准编码规则：品牌代码 (4 位)-分类代码 (6 位)-规格代码 (3 位)-流水号 (3 位)
    # 例如：SKFX-A0101-001-001
    standard_pattern = r'^[A-Z]{3,4}-[A-Z0-9\.]{6,8}-[A-Z0-9]{3}-[0-9]{3}(-[A-Z0-9]{3})?$'
    
    valid_codes = []
    invalid_codes = []
    codes_with_suffix = []  # 带随机后缀的代码
    
    for part in all_parts:
        code = part.part_code
        # 检查是否符合标准格式
        if re.match(standard_pattern, code):
            if len(code) > 20:  # 带后缀的
                codes_with_suffix.append(part)
                valid_codes.append(part)
            else:
                valid_codes.append(part)
        else:
            invalid_codes.append(part)
    
    print(f"✅ 符合编码规则：{len(valid_codes)} 条")
    print(f"❌ 不符合编码规则：{len(invalid_codes)} 条")
    print(f"⚠️  带随机后缀（重复生成）：{len(codes_with_suffix)} 条")
    
    if codes_with_suffix:
        print("\n带随机后缀的备件代码示例（前 10 条）：")
        for part in codes_with_suffix[:10]:
            print(f"  - {part.part_code}: {part.name}")
    
    # 检查唯一性
    print("\n2️⃣ 检查备件代码唯一性")
    print("-" * 80)
    
    code_list = [part.part_code for part in all_parts]
    code_counts = Counter(code_list)
    
    duplicates = {code: count for code, count in code_counts.items() if count > 1}
    
    if duplicates:
        print(f"❌ 发现 {len(duplicates)} 个重复的备件代码：")
        for code, count in list(duplicates.items())[:10]:
            print(f"  - {code}: 重复 {count} 次")
    else:
        print("✅ 所有备件代码都是唯一的")
    
    # 按分类统计
    print("\n3️⃣ 按分类统计")
    print("-" * 80)
    
    category_distribution = Counter([part.category.name if part.category else '未分类' for part in all_parts])
    for category, count in sorted(category_distribution.items()):
        print(f"  - {category}: {count} 条")
    
    # 建议
    print("\n4️⃣ 处理建议")
    print("="*80)
    
    if total_count > 100:
        print(f"⚠️  当前有 {total_count} 条记录，超出目标 100 条")
        print(f"💡 建议：删除 {total_count - 100} 条记录")
        
        # 找出带后缀的重复记录
        if codes_with_suffix:
            print(f"\n📝 方案：删除 {len(codes_with_suffix)} 条带随机后缀的记录")
            print("   这些是因为重复而自动生成的新代码")
    
    elif total_count < 100:
        print(f"⚠️  当前有 {total_count} 条记录，少于目标 100 条")
        print(f"💡 建议：补充 {100 - total_count} 条记录")
    
    else:
        print("✅ 记录数正好为 100 条")
    
    print("="*80)
