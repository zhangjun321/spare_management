"""
验证修复是否成功
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
    
    part_code = 'SKFX-A-001-001-EHD'
    cursor.execute("SELECT id, part_code, name, image_url, thumbnail_url FROM spare_part WHERE part_code = %s", (part_code,))
    part = cursor.fetchone()
    
    if part:
        print(f"\n备件: {part['part_code']} - {part['name']}")
        print(f"image_url: {part['image_url']}")
        print(f"thumbnail_url: {part['thumbnail_url']}")
        
        has_backslash = '\\' in (part['image_url'] or '') or '\\' in (part['thumbnail_url'] or '')
        print(f"\n是否还有反斜杠: {'是' if has_backslash else '否'}")
        
        if not has_backslash:
            print("\n修复成功！路径已使用正斜杠！")
    else:
        print("未找到备件")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"错误: {str(e)}")
