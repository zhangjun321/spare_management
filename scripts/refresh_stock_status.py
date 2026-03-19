"""
刷新库存状态
根据当前库存数量重新计算并更新所有备件的库存状态
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
    print("刷新库存状态")
    print("=" * 80)
    
    # 刷新前统计
    print("\n刷新前统计：")
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'normal'")
    normal_before = cursor.fetchone()[0]
    print(f"  normal: {normal_before}")
    
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'low'")
    low_before = cursor.fetchone()[0]
    print(f"  low: {low_before}")
    
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'overstocked'")
    overstocked_before = cursor.fetchone()[0]
    print(f"  overstocked: {overstocked_before}")
    
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'out'")
    out_before = cursor.fetchone()[0]
    print(f"  out: {out_before}")
    
    # 执行更新
    print("\n正在更新库存状态...")
    
    # 使用 CASE 语句一次性更新所有记录
    cursor.execute("""
        UPDATE spare_part 
        SET stock_status = CASE
            WHEN current_stock = 0 THEN 'out'
            WHEN current_stock <= min_stock THEN 'low'
            WHEN max_stock IS NOT NULL AND current_stock >= max_stock THEN 'overstocked'
            ELSE 'normal'
        END
    """)
    
    affected_rows = cursor.rowcount
    connection.commit()
    
    print(f"✅ 已更新 {affected_rows} 条记录")
    
    # 刷新后统计
    print("\n刷新后统计：")
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'normal'")
    normal_after = cursor.fetchone()[0]
    print(f"  normal: {normal_after}")
    
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'low'")
    low_after = cursor.fetchone()[0]
    print(f"  low: {low_after}")
    
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'overstocked'")
    overstocked_after = cursor.fetchone()[0]
    print(f"  overstocked: {overstocked_after}")
    
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE stock_status = 'out'")
    out_after = cursor.fetchone()[0]
    print(f"  out: {out_after}")
    
    # 验证结果
    print("\n" + "=" * 80)
    print("验证结果（前 10 条记录）")
    print("=" * 80)
    
    cursor.execute("""
        SELECT part_code, name, current_stock, min_stock, max_stock, stock_status
        FROM spare_part 
        LIMIT 10
    """)
    
    parts = cursor.fetchall()
    
    for part in parts:
        part_code, name, current_stock, min_stock, max_stock, stock_status = part
        
        # 计算期望状态
        if current_stock == 0:
            expected_status = 'out'
        elif current_stock <= min_stock:
            expected_status = 'low'
        elif max_stock and current_stock >= max_stock:
            expected_status = 'overstocked'
        else:
            expected_status = 'normal'
        
        status_match = "✅" if stock_status == expected_status else "❌"
        print(f"{status_match} {part_code}: 库存={current_stock}, 最低={min_stock}, 最高={max_stock} → 状态={stock_status}")
    
    print("\n" + "=" * 80)
    print("刷新完成！")
    print("=" * 80)
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ 错误：{e}")
    if 'connection' in locals():
        connection.rollback()
