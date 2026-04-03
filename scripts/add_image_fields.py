"""
添加备件图片字段到数据库
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
    
    # 添加新字段
    print("\n[步骤 1] 添加侧面图字段...")
    sql = "ALTER TABLE spare_part ADD COLUMN side_image_url VARCHAR(500) NULL DEFAULT NULL COMMENT '侧面图 URL'"
    try:
        cursor.execute(sql)
        print("[OK] 已添加 side_image_url 字段")
    except Exception as e:
        print(f"[INFO] side_image_url 字段可能已存在：{str(e)}")
    
    print("\n[步骤 2] 添加详细图字段...")
    sql = "ALTER TABLE spare_part ADD COLUMN detail_image_url VARCHAR(500) NULL DEFAULT NULL COMMENT '详细图 URL'"
    try:
        cursor.execute(sql)
        print("[OK] 已添加 detail_image_url 字段")
    except Exception as e:
        print(f"[INFO] detail_image_url 字段可能已存在：{str(e)}")
    
    print("\n[步骤 3] 添加电路图字段...")
    sql = "ALTER TABLE spare_part ADD COLUMN circuit_image_url VARCHAR(500) NULL DEFAULT NULL COMMENT '电路图 URL'"
    try:
        cursor.execute(sql)
        print("[OK] 已添加 circuit_image_url 字段")
    except Exception as e:
        print(f"[INFO] circuit_image_url 字段可能已存在：{str(e)}")
    
    print("\n[步骤 4] 添加透视图字段...")
    sql = "ALTER TABLE spare_part ADD COLUMN perspective_image_url VARCHAR(500) NULL DEFAULT NULL COMMENT '透视图 URL'"
    try:
        cursor.execute(sql)
        print("[OK] 已添加 perspective_image_url 字段")
    except Exception as e:
        print(f"[INFO] perspective_image_url 字段可能已存在：{str(e)}")
    
    conn.commit()
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*50)
    print("[SUCCESS] 数据库表结构更新完成！")
    print("新增字段:")
    print("  - side_image_url (侧面图 URL)")
    print("  - detail_image_url (详细图 URL)")
    print("  - circuit_image_url (电路图 URL)")
    print("  - perspective_image_url (透视图 URL)")
    print("="*50)
    
except Exception as e:
    print(f"\n[ERROR] 错误：{str(e)}")
    import traceback
    print(traceback.format_exc())
