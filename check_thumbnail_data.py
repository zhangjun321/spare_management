"""
检查备件的thumbnail_url数据
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
    
    print("\n查询备件数据...")
    cursor.execute("SELECT id, part_code, name, image_url, thumbnail_url FROM spare_part WHERE thumbnail_url IS NOT NULL LIMIT 5")
    parts = cursor.fetchall()
    
    if parts:
        print(f"\n找到 {len(parts)} 个有thumbnail_url的备件：")
        for part in parts:
            print(f"\nID: {part['id']}")
            print(f"备件代码: {part['part_code']}")
            print(f"名称: {part['name']}")
            print(f"image_url: {part['image_url']}")
            print(f"thumbnail_url: {part['thumbnail_url']}")
    else:
        print("\n没有找到有thumbnail_url的备件")
    
    cursor.close()
    conn.close()
    print("\n数据库连接已关闭")
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    print(traceback.format_exc())
