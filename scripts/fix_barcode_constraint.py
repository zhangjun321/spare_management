"""
修复 barcode 字段的唯一约束问题
1. 先将所有空字符串的 barcode 更新为 NULL
2. 然后修改字段允许为 NULL
"""
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# 数据库连接配置
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'spare_parts_db'),
    'charset': 'utf8mb4'
}

try:
    print("正在连接数据库...")
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    # 第一步：将所有空字符串的 barcode 更新为 NULL
    print("\n[步骤 1] 正在清理空字符串的 barcode...")
    sql_update = "UPDATE spare_part SET barcode = NULL WHERE barcode = ''"
    cursor.execute(sql_update)
    conn.commit()
    print(f"[OK] 已更新 {cursor.rowcount} 条记录")
    
    # 第二步：修改 barcode 字段，允许为 NULL
    print("\n[步骤 2] 正在修改 barcode 字段...")
    sql_alter = "ALTER TABLE spare_part MODIFY COLUMN barcode VARCHAR(100) NULL DEFAULT NULL COMMENT '条形码'"
    cursor.execute(sql_alter)
    conn.commit()
    print("[OK] 数据库表结构修改成功！")
    
    # 第三步：删除唯一索引（如果还存在问题）
    print("\n[步骤 3] 检查唯一索引...")
    try:
        # 检查是否有唯一索引
        cursor.execute("SHOW INDEX FROM spare_part WHERE Key_name = 'barcode'")
        indexes = cursor.fetchall()
        if indexes:
            print(f"[INFO] 找到 barcode 索引：{indexes[0]}")
            # 如果是唯一索引，需要删除
            if indexes[0][1] == 0:  # Non_unique = 0 表示唯一索引
                print("[INFO] 删除唯一索引...")
                cursor.execute("ALTER TABLE spare_part DROP INDEX barcode")
                print("[OK] 已删除唯一索引")
                
                # 重新创建普通索引
                print("[INFO] 创建普通索引...")
                cursor.execute("ALTER TABLE spare_part ADD INDEX barcode (barcode)")
                print("[OK] 已创建普通索引")
    except Exception as e:
        print(f"[WARNING] 索引操作失败：{str(e)}")
        print("[INFO] 继续执行...")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*50)
    print("[SUCCESS] 所有修复步骤完成！")
    print("="*50)
    
except Exception as e:
    print(f"\n[ERROR] 错误：{str(e)}")
    import traceback
    print(traceback.format_exc())
