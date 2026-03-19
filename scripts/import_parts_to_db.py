# -*- coding: utf-8 -*-
"""
将备件数据导入 MySQL 数据库
"""

import os
import sys
import json
import glob
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Flask 应用配置
os.environ['FLASK_ENV'] = 'development'

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.supplier import Supplier

# 创建 Flask 应用
app = create_app()


def find_or_create_category(category_name, category_code):
    """查找或创建分类"""
    # 尝试查找
    category = Category.query.filter_by(code=category_code).first()
    
    if not category:
        # 创建新分类
        category = Category(
            name=category_name,
            code=category_code,
            description=f"{category_name} - AI 自动生成"
        )
        db.session.add(category)
        db.session.commit()
        print(f"  ✓ 创建分类：{category_name} ({category_code})")
    else:
        print(f"  - 分类已存在：{category_name}")
    
    return category


def find_or_create_supplier(supplier_name):
    """查找或创建供应商"""
    # 尝试查找
    supplier = Supplier.query.filter_by(name=supplier_name).first()
    
    if not supplier:
        # 创建新供应商
        supplier = Supplier(
            name=supplier_name,
            code=f"SUP-{hash(supplier_name) % 10000:04d}",
            contact_person=f"联系人 - {supplier_name[:4]}",
            phone="138****8888",
            email=f"contact@{supplier_name[:8]}.com",
            address="中国",
            rating=4.5
        )
        db.session.add(supplier)
        db.session.commit()
        print(f"  ✓ 创建供应商：{supplier_name}")
    else:
        print(f"  - 供应商已存在：{supplier_name}")
    
    return supplier


def import_parts_from_json(json_file):
    """从 JSON 文件导入备件数据"""
    print("="*80)
    print("导入备件数据到 MySQL 数据库")
    print("="*80)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据文件：{json_file}")
    print("="*80)
    
    # 读取 JSON 文件
    with open(json_file, 'r', encoding='utf-8') as f:
        parts_data = json.load(f)
    
    print(f"\n✓ 读取到 {len(parts_data)} 条备件数据\n")
    
    # 统计信息
    total = len(parts_data)
    success = 0
    skipped = 0
    updated = 0
    errors = 0
    
    with app.app_context():
        for i, part in enumerate(parts_data, 1):
            try:
                print(f"[{i}/{total}] 处理：{part.get('part_name', 'Unknown')}")
                
                # 检查 part_code 是否已存在
                existing = SparePart.query.filter_by(part_code=part.get('part_code')).first()
                
                if existing:
                    # 如果已存在，生成新的备件代码
                    new_code = generate_unique_code(part.get('part_code'))
                    print(f"  ⚠ 备件代码已存在，生成新代码：{new_code}")
                    part['part_code'] = new_code
                    updated += 1
                
                # 查找或创建分类
                category = find_or_create_category(
                    part.get('category_name', '通用备件'),
                    part.get('category_code', 'A.00.00')
                )
                
                # 查找或创建供应商
                supplier = find_or_create_supplier(part.get('supplier', '默认供应商'))
                
                # 创建备件记录
                remarks = []
                if part.get('material'):
                    remarks.append(f"材质：{part.get('material')}")
                if part.get('brand'):
                    remarks.append(f"品牌：{part.get('brand')}")
                if part.get('stock_status'):
                    remarks.append(f"库存状态：{part.get('stock_status')}")
                remarks.append("AI 自动生成数据")
                
                spare_part = SparePart(
                    part_code=part.get('part_code'),
                    name=part.get('part_name'),
                    specification=part.get('specification'),
                    category_id=category.id,
                    supplier_id=supplier.id,
                    current_stock=0,  # 初始库存为 0
                    unit_price=part.get('unit_price', 0),
                    min_stock=10,  # 默认最低库存
                    max_stock=100,  # 默认最高库存
                    location=f"A-{i:03d}",  # 默认库位
                    unit="个",  # 默认单位
                    remark="; ".join(remarks)
                )
                
                db.session.add(spare_part)
                db.session.commit()
                
                print(f"  ✓ 导入成功")
                success += 1
                
            except Exception as e:
                db.session.rollback()
                print(f"  ✗ 导入失败：{str(e)}")
                errors += 1
    
    # 打印统计信息
    print("\n" + "="*80)
    print("导入完成统计：")
    print("="*80)
    print(f"总记录数：{total}")
    print(f"成功导入：{success}")
    print(f"更新代码：{updated}")
    print(f"跳过重复：{skipped}")
    print(f"导入失败：{errors}")
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return success, skipped, errors


def generate_unique_code(original_code):
    """生成唯一的备件代码"""
    import random
    import string
    
    # 在原代码基础上添加随机后缀
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{original_code}-{suffix}"


def main():
    """主函数"""
    # 查找最新的 JSON 文件
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    json_files = glob.glob(os.path.join(data_dir, 'wenxin_parts_*.json'))
    
    if not json_files:
        print("✗ 未找到备件数据文件")
        print("请先运行 generate_100_parts_wenxin.py 生成数据")
        return
    
    # 使用最新的文件
    latest_file = sorted(json_files)[-1]
    print(f"\n使用最新的数据文件：{latest_file}\n")
    
    # 导入数据
    success, skipped, errors = import_parts_from_json(latest_file)
    
    if success > 0:
        print("\n✓ 数据导入完成！")
    else:
        print("\n✗ 数据导入失败")


if __name__ == "__main__":
    main()
