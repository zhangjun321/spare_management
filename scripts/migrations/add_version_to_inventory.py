"""
数据库迁移脚本 - 添加 version 字段到 inventory_v3 表
"""

import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Kra@211314',
    'port': 3306,
    'database': 'spare_management',
    'charset': 'utf8mb4'
}

def add_version_column():
    """添加 version 字段到 inventory_v3 表"""
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'spare_management' 
            AND TABLE_NAME = 'inventory_v3' 
            AND COLUMN_NAME = 'version'
        """)
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("[OK] version 字段已存在，无需添加")
        else:
            # 添加 version 字段
            cursor.execute("""
                ALTER TABLE inventory_v3 
                ADD COLUMN version INT DEFAULT 0 NOT NULL 
                COMMENT '版本号（乐观锁）' 
                AFTER updated_at
            """)
            
            conn.commit()
            print("[OK] 成功添加 version 字段到 inventory_v3 表")
        
        # 检查其他相关表是否也需要 version 字段
        tables_to_check = [
            ('warehouse_v3', '仓库表'),
            ('warehouse_location_v3', '库位表'),
            ('spare_part', '备件表'),
            ('inbound_order_v3', '入库单表'),
            ('outbound_order_v3', '出库单表')
        ]
        
        print("\n检查其他表的 version 字段:")
        for table, comment in tables_to_check:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = 'spare_management' 
                AND TABLE_NAME = '{table}' 
                AND COLUMN_NAME = 'version'
            """)
            
            exists = cursor.fetchone()[0]
            if exists:
                print(f"  [OK] {table} ({comment}) - version 字段已存在")
            else:
                print(f"  [WARN] {table} ({comment}) - 缺少 version 字段")
        
        cursor.close()
        conn.close()
        
        print("\n迁移完成！")
        
    except Exception as e:
        print(f"[ERROR] 迁移失败：{str(e)}")
        raise

if __name__ == '__main__':
    add_version_column()
