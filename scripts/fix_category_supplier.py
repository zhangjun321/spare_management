"""
修复 Category 和 Supplier 表的缺失字段
"""

import sys
import os
import pymysql
from dotenv import load_dotenv

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# 获取数据库配置
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'spare_parts_db')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')

def fix_tables():
    """修复数据库表结构"""
    
    # 连接数据库
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4'
    )
    
    try:
        cursor = connection.cursor()
        
        print("=" * 60)
        print("开始修复 Category 和 Supplier 表...")
        print("=" * 60)
        
        # 检查并添加 category 表的 status 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'category' 
            AND COLUMN_NAME = 'status'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `category` 
                ADD COLUMN `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态' AFTER `sort_order`
            """)
            print("✓ 添加 category.status 字段成功")
        else:
            print("✓ category.status 字段已存在")
        
        # 检查并添加 supplier 表的 is_active 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'supplier' 
            AND COLUMN_NAME = 'is_active'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `supplier` 
                ADD COLUMN `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用' AFTER `status`
            """)
            print("✓ 添加 supplier.is_active 字段成功")
        else:
            print("✓ supplier.is_active 字段已存在")
        
        connection.commit()
        
        print("\n" + "=" * 60)
        print("数据库表结构修复完成！")
        print("=" * 60)
        
        cursor.close()
        
    except Exception as e:
        print(f"✗ 错误：{e}")
        connection.rollback()
        raise
    finally:
        connection.close()

if __name__ == '__main__':
    print("=" * 60)
    print("开始修复数据库表结构...")
    print("=" * 60)
    fix_tables()
    print("\n完成！")
