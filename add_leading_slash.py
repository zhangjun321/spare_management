"""
给路径添加前导斜杠
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
    
    # 查询没有前导斜杠的备件
    print("\n查询没有前导斜杠的备件...")
    cursor.execute("SELECT id, part_code, name, image_url, thumbnail_url FROM spare_part WHERE image_url LIKE 'uploads/%' OR thumbnail_url LIKE 'uploads/%'")
    parts = cursor.fetchall()
    
    if parts:
        print(f"\n找到 {len(parts)} 个需要修复的备件：")
        
        for part in parts:
            print(f"\n修复: {part['part_code']} - {part['name']}")
            
            # 修复 image_url
            new_image_url = part['image_url']
            if new_image_url and new_image_url.startswith('uploads/'):
                new_image_url = '/' + new_image_url
                print(f"  image_url: {part['image_url']} -> {new_image_url}")
            
            # 修复 thumbnail_url
            new_thumbnail_url = part['thumbnail_url']
            if new_thumbnail_url and new_thumbnail_url.startswith('uploads/'):
                new_thumbnail_url = '/' + new_thumbnail_url
                print(f"  thumbnail_url: {part['thumbnail_url']} -> {new_thumbnail_url}")
            
            # 更新数据库
            cursor.execute(
                "UPDATE spare_part SET image_url = %s, thumbnail_url = %s WHERE id = %s",
                (new_image_url, new_thumbnail_url, part['id'])
            )
        
        conn.commit()
        print(f"\n成功修复了 {len(parts)} 个备件的路径！")
    else:
        print("\n没有需要修复的备件")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    print(traceback.format_exc())
