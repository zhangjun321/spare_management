#!/usr/bin/env python
"""
验证超储备件在图表中的显示
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.spare_part import SparePart
from app.routes.dashboard import get_dashboard_stats

app = create_app()

with app.app_context():
    print("=" * 60)
    print("验证超储备件数据显示")
    print("=" * 60)
    
    stats = get_dashboard_stats()
    
    print(f"\n库存状态统计:")
    print(f"  正常：{stats['stock_status']['normal']}")
    print(f"  低库存：{stats['stock_status']['low']}")
    print(f"  缺货：{stats['stock_status']['out']}")
    print(f"  超储：{stats['stock_status']['overstocked']}")
    
    total = sum(stats['stock_status'].values())
    print(f"\n总计：{total}")
    
    if stats['stock_status']['overstocked'] > 0:
        print(f"\n✓ 超储备件数量正确：{stats['stock_status']['overstocked']}")
        
        overstocked_parts = SparePart.query.filter_by(stock_status='overstocked').all()
        print(f"\n超储备件列表:")
        for part in overstocked_parts[:5]:
            print(f"  - {part.part_code}: {part.name} (库存：{part.current_stock}, 最大：{part.max_stock})")
        
        if len(overstocked_parts) > 5:
            print(f"  ... 还有 {len(overstocked_parts) - 5} 个超储备件")
    else:
        print("\n✗ 警告：超储备件数量为 0，请检查数据是否正确更新")
    
    print("\n" + "=" * 60)
