"""
检查库存状态是否正确（使用 pymysql 直接连接）
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
    print("库存状态统计")
    print("=" * 80)
    
    # 总数量
    cursor.execute("SELECT COUNT(*) FROM spare_part")
    total = cursor.fetchone()[0]
    print(f"总备件数量：{total}")
    
    # 库存为 0 的数量
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE current_stock = 0")
    zero_stock = cursor.fetchone()[0]
    print(f"当前库存为 0 的数量：{zero_stock}")
    
    # 状态为 low 的数量
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'low'")
    low_stock = cursor.fetchone()[0]
    print(f"库存状态为'low'的数量：{low_stock}")
    
    # 状态为 normal 的数量
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'normal'")
    normal_stock = cursor.fetchone()[0]
    print(f"库存状态为'normal'的数量：{normal_stock}")
    
    # 状态为 overstocked 的数量
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'overstocked'")
    overstocked = cursor.fetchone()[0]
    print(f"库存状态为'overstocked'的数量：{overstocked}")
    
    print()
    print("=" * 80)
    print("问题数据：当前库存为 0 但状态为'normal'的备件")
    print("=" * 80)
    
    # 查询问题数据
    cursor.execute("""
        SELECT part_code, name, current_stock, min_stock, max_stock, stock_status, safety_stock
        FROM spare_part 
        WHERE current_stock = 0 AND stock_status = 'normal'
        LIMIT 10
    """)
    
    problem_parts = cursor.fetchall()
    
    if problem_parts:
        print(f"发现 {len(problem_parts)} 条问题数据（显示前 10 条）:\n")
        for part in problem_parts:
            print(f"备件代码：{part[0]}")
            print(f"  备件名称：{part[1]}")
            print(f"  当前库存：{part[2]}")
            print(f"  最低库存：{part[3]}")
            print(f"  最高库存：{part[4]}")
            print(f"  库存状态：{part[5]} ❌ 应该是'low'")
            print(f"  安全库存：{part[6]}")
            print()
    else:
        print("✅ 未发现问题数据")
    
    print()
    print("=" * 80)
    print("随机抽取 5 条记录验证规则")
    print("=" * 80)
    
    cursor.execute("""
        SELECT part_code, current_stock, min_stock, max_stock, stock_status
        FROM spare_part 
        LIMIT 5
    """)
    
    test_parts = cursor.fetchall()
    
    for part in test_parts:
        part_code, current_stock, min_stock, max_stock, stock_status = part
        
        # 计算期望状态
        if current_stock <= min_stock:
            expected_status = 'low'
        elif max_stock and current_stock >= max_stock:
            expected_status = 'overstocked'
        else:
            expected_status = 'normal'
        
        status_match = "✅" if stock_status == expected_status else "❌"
        print(f"{status_match} 备件代码：{part_code}")
        print(f"  当前库存：{current_stock}, 最低库存：{min_stock}, 最高库存：{max_stock}")
        print(f"  当前状态：{stock_status}, 期望状态：{expected_status}")
        print()
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ 错误：{e}")
