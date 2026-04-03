"""
修复第二条备件的缩略图和数据库
"""
import os
from PIL import Image
import pymysql
from dotenv import load_dotenv

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

part_code = 'FAGX-A-002-002-PWP'
part_id = 32

base_dir = r'D:\Trae\spare_management\uploads\images'
part_dir = os.path.join(base_dir, part_code)

print(f"正在处理备件: {part_code} (ID: {part_id})")
print(f"目录: {part_dir}")

# 检查front.jpg是否存在
front_path = os.path.join(part_dir, 'front.jpg')
print(f"\n检查front.jpg: {front_path}")
if os.path.exists(front_path):
    print("  front.jpg 存在")
    
    # 生成缩略图
    thumbnail_path = os.path.join(part_dir, 'thumbnail.jpg')
    print(f"\n生成缩略图: {thumbnail_path}")
    try:
        with Image.open(front_path) as img:
            img.thumbnail((200, 150))
            img.save(thumbnail_path)
        print("  缩略图生成成功！")
    except Exception as e:
        print(f"  缩略图生成失败: {str(e)}")
else:
    print("  front.jpg 不存在！")

# 更新数据库
print(f"\n更新数据库...")
try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    image_url = f"/uploads/images/{part_code}/front.jpg"
    thumbnail_url = f"/uploads/images/{part_code}/thumbnail.jpg"
    
    print(f"  image_url: {image_url}")
    print(f"  thumbnail_url: {thumbnail_url}")
    
    cursor.execute(
        "UPDATE spare_part SET image_url = %s, thumbnail_url = %s WHERE id = %s",
        (image_url, thumbnail_url, part_id)
    )
    
    conn.commit()
    print("  数据库更新成功！")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  数据库更新失败: {str(e)}")
    import traceback
    print(traceback.format_exc())

print("\n完成！")
