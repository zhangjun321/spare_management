"""
验证库存状态逻辑
检查当前数据库中的数据是否符合库存状态规则
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
    print("验证库存状态逻辑")
    print("=" * 80)
    
    # 统计信息
    cursor.execute("SELECT COUNT(*) FROM spare_part")
    total = cursor.fetchone()[0]
    print(f"\n总备件数量：{total}")
    
    # 查询所有记录并验证
    cursor.execute("""
        SELECT part_code, current_stock, min_stock, max_stock, stock_status
        FROM spare_part
        ORDER BY id
    """)
    
    parts = cursor.fetchall()
    
    correct = 0
    incorrect = 0
    examples = []
    
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
        
        if actual_status == expected:
            correct += 1
        else:
            incorrect += 1
            if len(examples) < 10:  # 只记录前 10 个错误示例
                examples.append({
                    'part_code': part_code,
                    'current': current,
                    'min_s': min_s,
                    'max_s': max_s,
                    'actual': actual_status,
                    'expected': expected
                })
    
    print("\n" + "=" * 80)
    print("验证结果")
    print("=" * 80)
    print(f"正确：{correct}/{total} ({correct/total*100:.1f}%)")
    print(f"错误：{incorrect}/{total} ({incorrect/total*100:.1f}%)")
    
    if examples:
        print("\n错误示例（前 10 个）：")
        print("-" * 80)
        for ex in examples:
            print(f"❌ {ex['part_code']}:")
            print(f"   当前库存={ex['current']}, 最低={ex['min_s']}, 最高={ex['max_s']}")
            print(f"   实际状态={ex['actual']}, 期望状态={ex['expected']}")
    
    print("\n" + "=" * 80)
    print("库存状态分布")
    print("=" * 80)
    
    cursor.execute("""
        SELECT stock_status, COUNT(*) as count
        FROM spare_part
        GROUP BY stock_status
    """)
    
    for row in cursor.fetchall():
        status, count = row
        percentage = count / total * 100
        print(f"{status}: {count} ({percentage:.1f}%)")
    
    print("\n" + "=" * 80)
    print("每种状态示例（各 3 个）")
    print("=" * 80)
    
    # 缺货示例
    cursor.execute("""
        SELECT part_code, current_stock, min_stock, max_stock
        FROM spare_part
        WHERE stock_status = 'out'
        LIMIT 3
    """)
    print("\n[缺货] out:")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[1]}, 最低={part[2]}, 最高={part[3]}")
    
    # 低库存示例
    cursor.execute("""
        SELECT part_code, current_stock, min_stock, max_stock
        FROM spare_part
        WHERE stock_status = 'low'
        LIMIT 3
    """)
    print("\n[低库存] low:")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[1]}, 最低={part[2]}, 最高={part[3]}")
    
    # 正常示例
    cursor.execute("""
        SELECT part_code, current_stock, min_stock, max_stock
        FROM spare_part
        WHERE stock_status = 'normal'
        LIMIT 3
    """)
    print("\n[正常] normal:")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[1]}, 最低={part[2]}, 最高={part[3]}")
    
    # 超储示例
    cursor.execute("""
        SELECT part_code, current_stock, min_stock, max_stock
        FROM spare_part
        WHERE stock_status = 'overstocked'
        LIMIT 3
    """)
    print("\n[超储] overstocked:")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[1]}, 最低={part[2]}, 最高={part[3]}")
    
    cursor.close()
    connection.close()
    
    if incorrect == 0:
        print("\n" + "=" * 80)
        print("✅ 所有备件的库存状态都正确！")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print(f"❌ 发现 {incorrect} 个备件的库存状态不正确，需要修复。")
        print("=" * 80)
    
except Exception as e:
    print(f"❌ 错误：{e}")
