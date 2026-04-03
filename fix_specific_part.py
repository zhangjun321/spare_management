"""
修复特定备件的路径
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
    
    # 查询特定备件
    part_code = 'SKFX-A-001-001-EHD'
    print(f"\n查询备件: {part_code}")
    cursor.execute("SELECT id, part_code, name, image_url, thumbnail_url FROM spare_part WHERE part_code = %s", (part_code,))
    part = cursor.fetchone()
    
    if part:
        print(f"当前数据:")
        print(f"  image_url: {part['image_url']}")
        print(f"  thumbnail_url: {part['thumbnail_url']}")
        
        # 修复路径
        new_image_url = part['image_url'].replace('\\', '/') if part['image_url'] else None
        new_thumbnail_url = part['thumbnail_url'].replace('\\', '/') if part['thumbnail_url'] else None
        
        print(f"\n修复后:")
        print(f"  image_url: {new_image_url}")
        print(f"  thumbnail_url: {new_thumbnail_url}")
        
        # 更新
        cursor.execute(
            "UPDATE spare_part SET image_url = %s, thumbnail_url = %s WHERE id = %s",
            (new_image_url, new_thumbnail_url, part['id'])
        )
        conn.commit()
        print("\n✅ 更新成功！")
    else:
        print(f"未找到备件: {part_code}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    print(traceback.format_exc())
