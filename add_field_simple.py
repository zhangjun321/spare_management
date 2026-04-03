"""
直接使用PyMySQL添加字段（无emoji）
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
    
    print("检查字段是否存在...")
    cursor.execute("DESCRIBE spare_part")
    columns = [col[0] for col in cursor.fetchall()]
    
    if 'thumbnail_url' in columns:
        print("thumbnail_url字段已存在")
    else:
        print("正在添加thumbnail_url字段...")
        sql = "ALTER TABLE spare_part ADD COLUMN thumbnail_url VARCHAR(500) COMMENT '缩略图 URL'"
        cursor.execute(sql)
        conn.commit()
        print("thumbnail_url字段添加成功！")
    
    print("\n当前spare_part表的字段：")
    for col in columns:
        print(f"  - {col}")
    
    cursor.close()
    conn.close()
    print("\n数据库连接已关闭")
    
except Exception as e:
    print(f"错误: {str(e)}")
    import traceback
    print(traceback.format_exc())
