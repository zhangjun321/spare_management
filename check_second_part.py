"""
检查第二条备件的数据
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
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 查询前3条备件
    print("\n查询前3条备件...")
    cursor.execute("SELECT id, part_code, name, supplier_id FROM spare_part ORDER BY id LIMIT 3")
    parts = cursor.fetchall()
    
    for i, part in enumerate(parts, 1):
        print(f"\n备件 {i}:")
        print(f"  ID: {part['id']}")
        print(f"  备件代码: {part['part_code']}")
        print(f"  名称: {part['name']}")
        print(f"  供应商ID: {part['supplier_id']}")
        
        if part['supplier_id']:
            cursor.execute("SELECT name FROM supplier WHERE id = %s", (part['supplier_id'],))
            supplier = cursor.fetchone()
            if supplier:
                print(f"  供应商名称: {supplier['name']}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    print(traceback.format_exc())
