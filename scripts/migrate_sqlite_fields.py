#!/usr/bin/env python3
"""
SQLite数据库迁移脚本 - 添加warehouse_id和location_id字段
"""

import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'spare_parts.db')

def execute_sql(sql, description):
    """执行SQL语句"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print(f"✅ {description}成功")
        return True
    except sqlite3.Error as e:
        if "duplicate column name" in str(e):
            print(f"⚠️  字段已存在，跳过")
            return True
        else:
            print(f"❌ {description}失败：{e}")
            return False
    finally:
        if 'conn' in locals():
            conn.close()

def run_migration():
    """执行数据库迁移"""
    print("🔍 开始SQLite数据库迁移...")
    print("=" * 60)
    
    # 添加 warehouse_id 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN warehouse_id INTEGER",
        "添加 warehouse_id 字段"
    )
    
    # 添加 location_id 字段
    execute_sql(
        "ALTER TABLE spare_part ADD COLUMN location_id INTEGER",
        "添加 location_id 字段"
    )
    
    print("=" * 60)
    print("✅ 数据库迁移完成！")
    print("=" * 60)
    
    # 验证迁移结果
    print("\n📊 验证迁移结果...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询表结构
        cursor.execute('PRAGMA table_info(spare_part);')
        columns = cursor.fetchall()
        
        print(f"✅ 当前表结构包含 {len(columns)} 个字段")
        
        # 检查新字段是否存在
        column_names = [col[1] for col in columns]
        if 'warehouse_id' in column_names:
            print("✅ warehouse_id 字段已添加")
        else:
            print("❌ warehouse_id 字段未添加")
        
        if 'location_id' in column_names:
            print("✅ location_id 字段已添加")
        else:
            print("❌ location_id 字段未添加")
        
        # 查询记录数
        cursor.execute("SELECT COUNT(*) FROM spare_part")
        count = cursor.fetchone()[0]
        print(f"✅ 当前数据库记录数：{count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 验证失败：{e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    exit(0 if success else 1)
