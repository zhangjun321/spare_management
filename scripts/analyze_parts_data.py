"""
分析系统备件数据和仓库情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.spare_part import SparePart
from app.models.warehouse import Warehouse
from app.models.category import Category
from app.models.supplier import Supplier
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("=" * 80)
    print("备件管理系统数据分析报告")
    print("=" * 80)
    
    # 1. 备件总体统计
    print("\n【1. 备件总体统计】")
    total_parts = SparePart.query.count()
    print(f"  - 备件总数：{total_parts}")
    
    active_parts = SparePart.query.filter_by(is_active=True).count()
    print(f"  - 启用备件：{active_parts}")
    
    # 2. 库存状态分析
    print("\n【2. 库存状态分析】")
    stock_status_stats = db.session.query(
        SparePart.stock_status,
        func.count(SparePart.id)
    ).group_by(SparePart.stock_status).all()
    
    for status, count in stock_status_stats:
        status_map = {
            'normal': '正常',
            'low': '低库存',
            'out': '缺货',
            'overstocked': '超储'
        }
        print(f"  - {status_map.get(status, status)}: {count} 个")
    
    # 3. 分类统计
    print("\n【3. 备件分类统计】")
    category_stats = db.session.query(
        Category.name,
        func.count(SparePart.id)
    ).join(SparePart).group_by(Category.id).all()
    
    for category_name, count in category_stats:
        print(f"  - {category_name}: {count} 个")
    
    # 4. 供应商统计
    print("\n【4. 供应商统计】")
    supplier_count = Supplier.query.count()
    print(f"  - 供应商总数：{supplier_count}")
    
    # 5. 仓库统计
    print("\n【5. 仓库统计】")
    warehouse_count = Warehouse.query.count()
    print(f"  - 仓库总数：{warehouse_count}")
    
    if warehouse_count > 0:
        warehouses = Warehouse.query.all()
        print("\n  现有仓库列表：")
        for wh in warehouses:
            print(f"    * {wh.name} ({wh.code}) - {wh.type} - {wh.address or '无地址'}")
    else:
        print("  ⚠️ 当前系统没有仓库！")
    
    # 6. 备件分布分析
    print("\n【6. 备件仓库分布】")
    warehouse_stats = db.session.query(
        Warehouse.name,
        func.count(SparePart.id)
    ).join(SparePart).group_by(Warehouse.id).all()
    
    if warehouse_stats:
        for wh_name, count in warehouse_stats:
            print(f"  - {wh_name}: {count} 个备件")
    else:
        print("  ⚠️ 所有备件都没有分配仓库！")
    
    # 7. 库存数量分析
    print("\n【7. 库存数量分析】")
    total_stock = db.session.query(func.sum(SparePart.current_stock)).scalar() or 0
    print(f"  - 总库存数量：{total_stock}")
    
    avg_stock = db.session.query(func.avg(SparePart.current_stock)).scalar() or 0
    print(f"  - 平均每个备件库存：{avg_stock:.2f}")
    
    max_stock_part = SparePart.query.order_by(SparePart.current_stock.desc()).first()
    if max_stock_part:
        print(f"  - 库存最多的备件：{max_stock_part.name} ({max_stock_part.part_code}) - {max_stock_part.current_stock}")
    
    # 8. 品牌分布
    print("\n【8. 品牌分布（前 10）】")
    brand_stats = db.session.query(
        SparePart.brand,
        func.count(SparePart.id)
    ).filter(SparePart.brand.isnot(None)).group_by(SparePart.brand).order_by(
        func.count(SparePart.id).desc()
    ).limit(10).all()
    
    for brand, count in brand_stats:
        print(f"  - {brand or '无品牌'}: {count} 个")
    
    # 9. 数据特点总结
    print("\n【9. 数据特点总结】")
    print(f"  ✓ 系统共有 {total_parts} 个备件，{active_parts} 个启用")
    print(f"  ✓ 共有 {supplier_count} 个供应商")
    print(f"  ✓ 当前仓库数量：{warehouse_count} 个")
    
    if warehouse_count == 0:
        print("  ⚠️ 关键问题：系统没有仓库，所有备件无法进行库位管理")
        print("  💡 建议：立即创建仓库，建议按以下维度规划：")
        print("     - 按物理位置：原材料仓、成品仓、备件仓、危险品仓")
        print("     - 按用途：生产仓、维修仓、研发仓")
        print("     - 按温度：常温仓、恒温仓、冷藏仓")
    
    # 10. 智能化建议
    print("\n【10. 智能化仓库规划建议】")
    if total_parts > 0:
        print("  基于 AI 分析的仓库规划方案：")
        print(f"  ① 建议创建 8-12 个仓库，覆盖不同业务场景")
        print(f"  ② 仓库命名采用：区域 + 类型 + 编号 的方式")
        print(f"  ③ 建议仓库类型分布：")
        print(f"     - 主仓库（Main Warehouse）: 2-3 个")
        print(f"     - 分仓库（Branch Warehouse）: 3-4 个")
        print(f"     - 专用仓库（Special Warehouse）: 2-3 个")
        print(f"     - 临时仓库（Temporary Warehouse）: 1-2 个")
    
    print("\n" + "=" * 80)
