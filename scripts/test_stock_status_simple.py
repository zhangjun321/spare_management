"""
测试库存状态自动检测功能（使用 pymysql）
验证库存状态计算逻辑是否正确
"""

import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Kra@211314',
    'database': 'spare_parts_db',
    'charset': 'utf8mb4'
}

try:
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
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
        # 使用 SQL CASE 语句计算期望状态
        cursor.execute("""
            SELECT CASE
                WHEN %s = 0 THEN 'out'
                WHEN %s <= %s THEN 'low'
                WHEN %s IS NOT NULL AND %s >= %s THEN 'overstocked'
                ELSE 'normal'
            END as calculated_status
        """, (current, current, min_s, max_s, max_s, current, max_s))
        
        result = cursor.fetchone()
        calculated_status = result[0]
        
        # 验证结果
        if calculated_status == expected:
            print(f"✅ 测试{i}通过：{desc}")
            print(f"   计算状态={calculated_status}")
            passed += 1
        else:
            print(f"❌ 测试{i}失败：{desc}")
            print(f"   期望状态={expected}, 计算状态={calculated_status}")
            failed += 1
    
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"通过：{passed}/{len(test_cases)}")
    print(f"失败：{failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n✅ 所有测试通过！库存状态自动检测逻辑正确。")
    else:
        print(f"\n❌ 有 {failed} 个测试失败，请检查代码。")
    
    # 显示当前数据库中的实际数据验证
    print("\n" + "=" * 80)
    print("验证数据库中的实际数据")
    print("=" * 80)
    
    cursor.execute("""
        SELECT part_code, current_stock, min_stock, max_stock, stock_status
        FROM spare_part
        LIMIT 10
    """)
    
    parts = cursor.fetchall()
    
    print("\n前 10 条记录验证：")
    for part in parts:
        part_code, current, min_s, max_s, actual_status = part
        
        # 计算期望状态
        if current == 0:
            expected = 'out'
        elif current <= min_s:
            expected = 'low'
        elif max_s and current >= max_s:
            expected = 'overstocked'
        else:
            expected = 'normal'
        
        status_match = "✅" if actual_status == expected else "❌"
        print(f"{status_match} {part_code}: 库存={current}, 最低={min_s}, 最高={max_s} → 状态={actual_status}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ 错误：{e}")
