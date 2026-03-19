"""
检查库存状态是否正确
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
    # 统计数据
    total_parts = SparePart.query.count()
    zero_stock_parts = SparePart.query.filter_by(current_stock=0).count()
    low_stock_parts = SparePart.query.filter_by(stock_status='low').count()
    normal_stock_parts = SparePart.query.filter_by(stock_status='normal').count()
    overstocked_parts = SparePart.query.filter_by(stock_status='overstocked').count()
    
    print("=" * 80)
    print("库存状态统计")
    print("=" * 80)
    print(f"总备件数量：{total_parts}")
    print(f"当前库存为 0 的数量：{zero_stock_parts}")
    print(f"库存状态为'low'的数量：{low_stock_parts}")
    print(f"库存状态为'normal'的数量：{normal_stock_parts}")
    print(f"库存状态为'overstocked'的数量：{overstocked_parts}")
    print()
    
    # 检查库存为 0 但状态为 normal 的备件
    print("=" * 80)
    print("问题数据：当前库存为 0 但状态为'normal'的备件")
    print("=" * 80)
    
    problem_parts = SparePart.query.filter(
        SparePart.current_stock == 0,
        SparePart.stock_status == 'normal'
    ).limit(10).all()
    
    if problem_parts:
        print(f"发现 {len(problem_parts)} 条问题数据（显示前 10 条）:\n")
        for part in problem_parts:
            print(f"备件代码：{part.part_code}")
            print(f"  备件名称：{part.name}")
            print(f"  当前库存：{part.current_stock}")
            print(f"  最低库存：{part.min_stock}")
            print(f"  最高库存：{part.max_stock}")
            print(f"  库存状态：{part.stock_status} ❌ 应该是'low'")
            print(f"  安全库存：{part.safety_stock}")
            print()
    else:
        print("✅ 未发现问题数据")
    
    print()
    print("=" * 80)
    print("库存状态规则检查")
    print("=" * 80)
    
    # 检查库存状态规则
    test_parts = SparePart.query.limit(5).all()
    print("\n随机抽取 5 条记录验证规则:\n")
    
    for part in test_parts:
        expected_status = 'normal'
        if part.current_stock <= part.min_stock:
            expected_status = 'low'
        elif part.max_stock and part.current_stock >= part.max_stock:
            expected_status = 'overstocked'
        
        status_match = "✅" if part.stock_status == expected_status else "❌"
        print(f"{status_match} 备件代码：{part.part_code}")
        print(f"  当前库存：{part.current_stock}, 最低库存：{part.min_stock}, 最高库存：{part.max_stock}")
        print(f"  当前状态：{part.stock_status}, 期望状态：{expected_status}")
        print()
