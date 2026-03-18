"""
修复数据库表结构
添加缺失的字段
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
        
        print("开始修复数据库表结构...")
        
        # 检查并添加 spare_part 表的 remark 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'spare_part' 
            AND COLUMN_NAME = 'remark'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `spare_part` 
                ADD COLUMN `remark` TEXT COMMENT '备注' AFTER `image_url`
            """)
            print("✓ 添加 spare_part.remark 字段成功")
        else:
            print("✓ spare_part.remark 字段已存在")
        
        # 检查并添加 spare_part 表的 is_active 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'spare_part' 
            AND COLUMN_NAME = 'is_active'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `spare_part` 
                ADD COLUMN `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用' AFTER `image_url`
            """)
            print("✓ 添加 spare_part.is_active 字段成功")
        else:
            print("✓ spare_part.is_active 字段已存在")
        
        # 检查并添加 equipment 表的 supplier_id 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'equipment' 
            AND COLUMN_NAME = 'supplier_id'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `equipment` 
                ADD COLUMN `supplier_id` INT COMMENT '供应商 ID' AFTER `warranty_expiry`
            """)
            print("✓ 添加 equipment.supplier_id 字段成功")
        else:
            print("✓ equipment.supplier_id 字段已存在")
        
        # 检查并添加 equipment 表的 purchase_price 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'equipment' 
            AND COLUMN_NAME = 'purchase_price'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `equipment` 
                ADD COLUMN `purchase_price` DECIMAL(10,2) COMMENT '购买价格' AFTER `supplier_id`
            """)
            print("✓ 添加 equipment.purchase_price 字段成功")
        else:
            print("✓ equipment.purchase_price 字段已存在")
        
        # 检查并添加 equipment 表的 remark 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'equipment' 
            AND COLUMN_NAME = 'remark'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `equipment` 
                ADD COLUMN `remark` TEXT COMMENT '备注' AFTER `purchase_price`
            """)
            print("✓ 添加 equipment.remark 字段成功")
        else:
            print("✓ equipment.remark 字段已存在")
        
        # 检查并添加 equipment 表的 is_active 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'equipment' 
            AND COLUMN_NAME = 'is_active'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `equipment` 
                ADD COLUMN `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用' AFTER `remark`
            """)
            print("✓ 添加 equipment.is_active 字段成功")
        else:
            print("✓ equipment.is_active 字段已存在")
        
        # 检查并添加 equipment 表的 created_by 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'equipment' 
            AND COLUMN_NAME = 'created_by'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `equipment` 
                ADD COLUMN `created_by` INT COMMENT '创建人 ID' AFTER `updated_at`
            """)
            print("✓ 添加 equipment.created_by 字段成功")
        else:
            print("✓ equipment.created_by 字段已存在")
        
        # 检查并添加 maintenance_order 表的 title 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'maintenance_order' 
            AND COLUMN_NAME = 'title'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `maintenance_order` 
                ADD COLUMN `title` VARCHAR(200) COMMENT '工单标题' AFTER `equipment_id`
            """)
            print("✓ 添加 maintenance_order.title 字段成功")
        else:
            print("✓ maintenance_order.title 字段已存在")
        
        # 检查并添加 maintenance_order 表的 type 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'maintenance_order' 
            AND COLUMN_NAME = 'type'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE `maintenance_order` 
                ADD COLUMN `type` VARCHAR(20) COMMENT '工单类型' AFTER `priority`
            """)
            print("✓ 添加 maintenance_order.type 字段成功")
        else:
            print("✓ maintenance_order.type 字段已存在")
        
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
