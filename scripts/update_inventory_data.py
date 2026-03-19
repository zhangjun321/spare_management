"""
更新备件库存数据
按照指定比例分布：
- 正常库存：90%
- 低库存：3%
- 缺货：2%
- 超储：5%
"""

import pymysql
import random

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
    print("更新备件库存数据")
    print("=" * 80)
    
    # 获取所有备件
    cursor.execute("""
        SELECT id, part_code, name, min_stock, max_stock 
        FROM spare_part 
        ORDER BY id
    """)
    
    parts = cursor.fetchall()
    total_count = len(parts)
    
    print(f"\n总备件数量：{total_count}")
    
    # 计算各状态数量
    out_count = int(total_count * 0.02)  # 缺货 2%
    low_count = int(total_count * 0.03)  # 低库存 3%
    overstocked_count = int(total_count * 0.05)  # 超储 5%
    normal_count = total_count - out_count - low_count - overstocked_count  # 正常 90%
    
    print(f"\n目标分布：")
    print(f"  缺货 (2%): {out_count} 个")
    print(f"  低库存 (3%): {low_count} 个")
    print(f"  超储 (5%): {overstocked_count} 个")
    print(f"  正常 (90%): {normal_count} 个")
    print(f"  总计：{out_count + low_count + overstocked_count + normal_count} 个")
    
    # 随机打乱备件顺序
    parts_list = list(parts)
    random.shuffle(parts_list)
    
    # 分配库存状态
    out_parts = parts_list[:out_count]
    low_parts = parts_list[out_count:out_count + low_count]
    overstocked_parts = parts_list[out_count + low_count:out_count + low_count + overstocked_count]
    normal_parts = parts_list[out_count + low_count + overstocked_count:]
    
    print("\n" + "=" * 80)
    print("开始更新库存数据...")
    print("=" * 80)
    
    updated_count = 0
    
    # 更新缺货（库存 = 0）
    print(f"\n[缺货] 更新缺货备件 ({len(out_parts)} 个)...")
    for part in out_parts:
        part_id, part_code, name, min_stock, max_stock = part
        current_stock = 0
        
        cursor.execute("""
            UPDATE spare_part 
            SET current_stock = %s
            WHERE id = %s
        """, (current_stock, part_id))
        
        updated_count += 1
        
        if updated_count % 10 == 0 or updated_count == len(out_parts):
            print(f"  已更新 {updated_count}/{len(out_parts)} 个")
    
    # 更新低库存（0 < 库存 <= min_stock）
    print(f"\n[低库存] 更新低库存备件 ({len(low_parts)} 个)...")
    for part in low_parts:
        part_id, part_code, name, min_stock, max_stock = part
        
        # 确保 min_stock 不为 0，如果是 0 则设置为 10
        if min_stock == 0 or min_stock is None:
            min_stock = 10
        
        # 生成 1 到 min_stock 之间的随机数
        current_stock = random.randint(1, min_stock)
        
        cursor.execute("""
            UPDATE spare_part 
            SET current_stock = %s
            WHERE id = %s
        """, (current_stock, part_id))
        
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"  已更新 {updated_count} 个")
    
    # 更新超储（库存 >= max_stock）
    print(f"\n[超储] 更新超储备件 ({len(overstocked_parts)} 个)...")
    for part in overstocked_parts:
        part_id, part_code, name, min_stock, max_stock = part
        
        # 确保 max_stock 不为 0，如果是 0 则设置为 100
        if max_stock == 0 or max_stock is None:
            max_stock = 100
        
        # 生成 max_stock 到 max_stock*1.5 之间的随机数
        current_stock = random.randint(max_stock, int(max_stock * 1.5))
        
        cursor.execute("""
            UPDATE spare_part 
            SET current_stock = %s
            WHERE id = %s
        """, (current_stock, part_id))
        
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"  已更新 {updated_count} 个")
    
    # 更新正常库存（min_stock < 库存 < max_stock）
    print(f"\n[正常] 更新正常库存备件 ({len(normal_parts)} 个)...")
    for part in normal_parts:
        part_id, part_code, name, min_stock, max_stock = part
        
        # 确保 min_stock 和 max_stock 合理
        if min_stock == 0 or min_stock is None:
            min_stock = 10
        if max_stock == 0 or max_stock is None:
            max_stock = 100
        
        # 确保 min_stock < max_stock
        if min_stock >= max_stock:
            max_stock = min_stock * 10
        
        # 生成 min_stock+1 到 max_stock-1 之间的随机数
        if max_stock - min_stock > 1:
            current_stock = random.randint(min_stock + 1, max_stock - 1)
        else:
            current_stock = min_stock + 5
        
        cursor.execute("""
            UPDATE spare_part 
            SET current_stock = %s
            WHERE id = %s
        """, (current_stock, part_id))
        
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"  已更新 {updated_count} 个")
    
    # 提交事务
    connection.commit()
    
    print("\n" + "=" * 80)
    print(f"✅ 库存数据更新完成！共更新 {total_count} 条记录")
    print("=" * 80)
    
    # 验证结果
    print("\n" + "=" * 80)
    print("验证更新结果")
    print("=" * 80)
    
    # 统计各状态数量
    cursor.execute("SELECT COUNT(*) FROM spare_part WHERE current_stock = 0")
    out_actual = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM spare_part 
        WHERE current_stock > 0 AND current_stock <= min_stock
    """)
    low_actual = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM spare_part 
        WHERE current_stock > min_stock AND (max_stock IS NULL OR current_stock < max_stock)
    """)
    normal_actual = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM spare_part 
        WHERE max_stock IS NOT NULL AND current_stock >= max_stock
    """)
    overstocked_actual = cursor.fetchone()[0]
    
    print(f"\n实际分布：")
    print(f"  🔴 缺货：{out_actual} 个 ({out_actual/total_count*100:.1f}%)")
    print(f"  🟠 低库存：{low_actual} 个 ({low_actual/total_count*100:.1f}%)")
    print(f"  ✅ 正常：{normal_actual} 个 ({normal_actual/total_count*100:.1f}%)")
    print(f"  🟡 超储：{overstocked_actual} 个 ({overstocked_actual/total_count*100:.1f}%)")
    print(f"  总计：{out_actual + low_actual + normal_actual + overstocked_actual} 个")
    
    # 显示示例数据
    print("\n" + "=" * 80)
    print("示例数据（每种状态显示 3 个）")
    print("=" * 80)
    
    # 缺货示例
    cursor.execute("""
        SELECT part_code, name, current_stock, min_stock, max_stock
        FROM spare_part 
        WHERE current_stock = 0
        LIMIT 3
    """)
    print("\n[缺货] 示例：")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[2]}, 最低={part[3]}, 最高={part[4]}")
    
    # 低库存示例
    cursor.execute("""
        SELECT part_code, name, current_stock, min_stock, max_stock
        FROM spare_part 
        WHERE current_stock > 0 AND current_stock <= min_stock
        LIMIT 3
    """)
    print("\n[低库存] 示例：")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[2]}, 最低={part[3]}, 最高={part[4]}")
    
    # 正常示例
    cursor.execute("""
        SELECT part_code, name, current_stock, min_stock, max_stock
        FROM spare_part 
        WHERE current_stock > min_stock AND (max_stock IS NULL OR current_stock < max_stock)
        LIMIT 3
    """)
    print("\n[正常] 示例：")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[2]}, 最低={part[3]}, 最高={part[4]}")
    
    # 超储示例
    cursor.execute("""
        SELECT part_code, name, current_stock, min_stock, max_stock
        FROM spare_part 
        WHERE max_stock IS NOT NULL AND current_stock >= max_stock
        LIMIT 3
    """)
    print("\n[超储] 示例：")
    for part in cursor.fetchall():
        print(f"  {part[0]}: 库存={part[2]}, 最低={part[3]}, 最高={part[4]}")
    
    print("\n" + "=" * 80)
    print("更新完成！")
    print("=" * 80)
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ 错误：{e}")
    if 'connection' in locals():
        connection.rollback()
