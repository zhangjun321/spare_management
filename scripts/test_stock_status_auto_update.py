"""
测试库存状态自动检测功能
验证在创建和编辑备件时，库存状态能够正确更新
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.spare_part import SparePart

app = create_app()

with app.app_context():
    print("=" * 80)
    print("测试库存状态自动检测功能")
    print("=" * 80)
    
    # 测试用例
    test_cases = [
        # (current_stock, min_stock, max_stock, expected_status, description)
        (0, 10, 100, 'out', '缺货：库存为 0'),
        (5, 10, 100, 'low', '低库存：0 < 库存 <= 最低'),
        (10, 10, 100, 'low', '低库存：库存 = 最低'),
        (50, 10, 100, 'normal', '正常：最低 < 库存 < 最高'),
        (99, 10, 100, 'normal', '正常：库存 = 最高 -1'),
        (100, 10, 100, 'overstocked', '超储：库存 = 最高'),
        (150, 10, 100, 'overstocked', '超储：库存 > 最高'),
    ]
    
    print("\n测试用例：")
    print("-" * 80)
    for i, (current, min_s, max_s, expected, desc) in enumerate(test_cases, 1):
        print(f"{i}. {desc}")
        print(f"   当前库存={current}, 最低={min_s}, 最高={max_s} → 期望状态={expected}")
    
    print("\n" + "=" * 80)
    print("执行测试")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, (current, min_s, max_s, expected, desc) in enumerate(test_cases, 1):
        # 创建测试备件
        spare_part = SparePart(
            part_code=f'TEST-{i:03d}',
            name=f'测试备件 {i}',
            current_stock=current,
            min_stock=min_s,
            max_stock=max_s,
            unit='个',
            unit_price=100.00,
            is_active=True
        )
        
        # 调用库存状态更新方法
        spare_part.update_stock_status()
        
        # 验证结果
        if spare_part.stock_status == expected:
            print(f"✅ 测试{i}通过：{desc}")
            print(f"   实际状态={spare_part.stock_status}")
            passed += 1
        else:
            print(f"❌ 测试{i}失败：{desc}")
            print(f"   期望状态={expected}, 实际状态={spare_part.stock_status}")
            failed += 1
    
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"通过：{passed}/{len(test_cases)}")
    print(f"失败：{failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n✅ 所有测试通过！库存状态自动检测功能正常工作。")
    else:
        print(f"\n❌ 有 {failed} 个测试失败，请检查代码。")
    
    # 清理测试数据
    print("\n清理测试数据...")
    for i in range(1, len(test_cases) + 1):
        spare_part = SparePart.query.filter_by(part_code=f'TEST-{i:03d}').first()
        if spare_part:
            db.session.delete(spare_part)
    
    db.session.commit()
    print("✅ 测试数据已清理")
