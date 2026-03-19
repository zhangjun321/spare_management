"""
数据库迁移脚本 - 添加 8 个新字段
执行此脚本前请确保已备份数据库
"""

import sys
import os
import pymysql
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Kra@211314'),
    'database': os.getenv('DB_NAME', 'spare_parts_db'),
    'charset': 'utf8mb4'
}

def execute_sql(sql, description):
    """执行 SQL 语句"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        print(f"✅ {description}成功")
        return True
    except pymysql.err.OperationalError as e:
        if "Duplicate column name" in str(e) or e.args[0] == 1060:
            print(f"⚠️  字段已存在，跳过")
            return True
        else:
            print(f"❌ {description}失败：{e}")
            return False
    except Exception as e:
        print(f"❌ {description}失败：{e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def run_migration():
    """执行数据库迁移"""
    print("🔍 开始数据库迁移...")
    print("=" * 60)
    
    # 添加 brand 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN brand VARCHAR(100) COMMENT '品牌'",
        "添加 brand 字段"
    )
    execute_sql(
        "ALTER TABLE spare_part ADD INDEX idx_brand (brand)",
        "添加 brand 索引"
    )
    
    # 添加 barcode 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN barcode VARCHAR(100) COMMENT '条形码'",
        "添加 barcode 字段"
    )
    execute_sql(
        "ALTER TABLE spare_part ADD UNIQUE INDEX idx_barcode_unique (barcode)",
        "添加 barcode 唯一索引"
    )
    
    # 添加 safety_stock 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN safety_stock INT DEFAULT 0 COMMENT '安全库存'",
        "添加 safety_stock 字段"
    )
    
    # 添加 reorder_point 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN reorder_point INT COMMENT '再订货点'",
        "添加 reorder_point 字段"
    )
    
    # 添加 last_purchase_price 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN last_purchase_price DECIMAL(10,2) COMMENT '最近采购价'",
        "添加 last_purchase_price 字段"
    )
    
    # 添加 currency 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种'",
        "添加 currency 字段"
    )
    
    # 添加 warranty_period 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN warranty_period INT COMMENT '质保期 (月)'",
        "添加 warranty_period 字段"
    )
    
    # 添加 last_purchase_date 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN last_purchase_date DATETIME COMMENT '最后采购日期'",
        "添加 last_purchase_date 字段"
    )
    
    # 添加 technical_params 字段 (JSON 类型)
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN technical_params JSON COMMENT '技术参数'",
        "添加 technical_params 字段"
    )
    
    # 添加 datasheet_url 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN datasheet_url VARCHAR(500) COMMENT '数据手册 URL'",
        "添加 datasheet_url 字段"
    )
    
    print("=" * 60)
    print("✅ 数据库迁移完成！")
    print("=" * 60)
    
    # 验证迁移结果
    print("\n📊 验证迁移结果...")
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 查询表结构
        cursor.execute("DESCRIBE spare_part")
        columns = cursor.fetchall()
        
        print(f"✅ 当前表结构包含 {len(columns)} 个字段")
        
        # 查询记录数
        cursor.execute("SELECT COUNT(*) FROM spare_part")
        count = cursor.fetchone()[0]
        print(f"✅ 当前数据库记录数：{count}")
        
        # 查询示例记录
        cursor.execute("SELECT part_code, name FROM spare_part LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            print(f"   示例记录：{sample[0]} - {sample[1]}")
        else:
            print("⚠️  数据库为空，但迁移成功")
        
        connection.close()
        return True
    except Exception as e:
        print(f"❌ 验证失败：{e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
