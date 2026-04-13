"""
检查两个数据库的备件数据
"""

import pymysql

# 数据库配置
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Kra@211314',
    'charset': 'utf8mb4'
}

print("=" * 80)
print("数据库对比检查")
print("=" * 80)

try:
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    
    # 1. 检查 spare_management 数据库
    print("\n【1. spare_management 数据库】")
    cursor.execute("USE spare_management")
    cursor.execute("SELECT COUNT(*) FROM spare_part")
    count1 = cursor.fetchone()[0]
    print(f"  spare_part 表记录数：{count1}")
    
    if count1 > 0:
        cursor.execute("SELECT id, name, part_code, current_stock FROM spare_part LIMIT 5")
        rows = cursor.fetchall()
        print("  前 5 条记录:")
        for row in rows:
            print(f"    {row[0]}. {row[1]} ({row[2]}) - 库存：{row[3]}")
    
    # 2. 检查 spare_parts_db 数据库
    print("\n【2. spare_parts_db 数据库】")
    cursor.execute("USE spare_parts_db")
    cursor.execute("SHOW TABLES LIKE '%part%'")
    tables = cursor.fetchall()
    print(f"  包含'part'的表：{len(tables)} 个")
    for t in tables:
        print(f"    - {t[0]}")
    
    # 检查 spare_part 或类似表
    cursor.execute("SHOW TABLES")
    all_tables = cursor.fetchall()
    part_tables = [t[0] for t in all_tables if 'part' in t[0].lower() or 'spare' in t[0].lower()]
    
    if part_tables:
        print(f"\n  备件相关表：{part_tables}")
        
        # 尝试查询每个表
        for table in part_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    {table}: {count} 条记录")
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    print(f"      前 3 条:")
                    for row in rows:
                        print(f"        {row}")
            except Exception as e:
                print(f"    {table}: 查询失败 - {e}")
    
    # 3. 对比结果
    print("\n【3. 结论】")
    cursor.execute("USE spare_management")
    cursor.execute("SELECT COUNT(*) FROM spare_part")
    count_mgmt = cursor.fetchone()[0]
    
    cursor.execute("USE spare_parts_db")
    has_parts_db = True
    try:
        cursor.execute("SELECT COUNT(*) FROM spare_part")
        count_parts = cursor.fetchone()[0]
    except:
        count_parts = 0
        has_parts_db = False
    
    print(f"  ✓ spare_management: {count_mgmt} 条备件记录")
    print(f"  ✓ spare_parts_db: {count_parts} 条备件记录")
    
    if count_parts > count_mgmt:
        print(f"\n  💡 建议：spare_parts_db 有更多数据，应该使用该数据库或导入数据")
    else:
        print(f"\n  ℹ️  当前 spare_management 数据库数据充足")
    
    conn.close()
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"数据库查询失败：{e}")
    import traceback
    traceback.print_exc()
