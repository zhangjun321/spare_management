"""
全面修复所有字段不一致问题
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

app = create_app()

def check_and_add_column(table_name, column_name, column_type, default_value=None, comment=None):
    """检查并添加缺失的列"""
    with app.app_context():
        # 检查列是否存在
        check_sql = f"""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'spare_management' 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
        """
        result = db.session.execute(text(check_sql)).scalar()
        
        if result == 0:
            # 列不存在，添加
            add_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_type}"
            
            if default_value is not None:
                add_sql += f" DEFAULT {default_value}"
            
            if comment:
                add_sql += f" COMMENT '{comment}'"
            
            try:
                db.session.execute(text(add_sql))
                db.session.commit()
                print(f"✓ 已添加字段：{table_name}.{column_name}")
                return True
            except Exception as e:
                print(f"✗ 添加字段失败：{table_name}.{column_name}, 错误：{e}")
                db.session.rollback()
                return False
        else:
            print(f"- 字段已存在：{table_name}.{column_name}")
            return True

def fix_category_table():
    """修复 Category 表：添加 status 字段以匹配表单查询"""
    print("\n=== 修复 Category 表 ===")
    # 添加 status 字段（为了兼容表单查询）
    check_and_add_column(
        'category', 
        'status', 
        'VARCHAR(20)',
        default_value="'active'",
        comment='状态 (active/inactive)'
    )

def fix_supplier_table():
    """修复 Supplier 表：添加 is_active 字段以统一命名"""
    print("\n=== 修复 Supplier 表 ===")
    # 添加 is_active 字段（统一使用布尔值）
    check_and_add_column(
        'supplier', 
        'is_active', 
        'BOOLEAN',
        default_value="TRUE",
        comment='是否启用'
    )

def fix_maintenance_record_table():
    """修复 MaintenanceRecord 表"""
    print("\n=== 修复 MaintenanceRecord 表 ===")
    # maintenance_by 字段已经在之前的修复中添加
    # 这里可以添加其他可能缺失的字段

def synchronize_supplier_status():
    """同步 Supplier 表的 status 和 is_active 字段"""
    print("\n=== 同步 Supplier 状态字段 ===")
    with app.app_context():
        # 根据 status 更新 is_active
        update_sql = """
            UPDATE supplier 
            SET is_active = CASE 
                WHEN status = 'active' THEN TRUE 
                ELSE FALSE 
            END
            WHERE is_active IS NULL
        """
        try:
            db.session.execute(text(update_sql))
            db.session.commit()
            print("✓ 已同步 Supplier 状态字段")
        except Exception as e:
            print(f"✗ 同步失败：{e}")
            db.session.rollback()

def synchronize_category_status():
    """同步 Category 表的 is_active 和 status 字段"""
    print("\n=== 同步 Category 状态字段 ===")
    with app.app_context():
        # 根据 is_active 更新 status
        update_sql = """
            UPDATE category 
            SET status = CASE 
                WHEN is_active = TRUE THEN 'active' 
                ELSE 'inactive' 
            END
            WHERE status IS NULL
        """
        try:
            db.session.execute(text(update_sql))
            db.session.commit()
            print("✓ 已同步 Category 状态字段")
        except Exception as e:
            print(f"✗ 同步失败：{e}")
            db.session.rollback()

def fix_forms():
    """修复表单文件中的字段引用"""
    print("\n=== 修复表单文件 ===")
    form_file = os.path.join(os.path.dirname(__file__), '..', 'app', 'forms', 'spare_parts.py')
    
    with open(form_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 SparePartSearchForm 中的 Category 查询
    old_category_query = "Category.query.filter_by(status='active')"
    new_category_query = "Category.query.filter_by(is_active=True)"
    
    if old_category_query in content:
        content = content.replace(old_category_query, new_category_query)
        print("✓ 已修复 Category 查询（status -> is_active）")
    
    # 修复 SparePartSearchForm 中的 Supplier 查询
    old_supplier_query = "Supplier.query.filter_by(status='active')"
    new_supplier_query = "Supplier.query.filter_by(is_active=True)"
    
    if old_supplier_query in content:
        content = content.replace(old_supplier_query, new_supplier_query)
        print("✓ 已修复 Supplier 查询（status -> is_active）")
    
    with open(form_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 表单文件已更新")

def main():
    print("=" * 60)
    print("开始修复所有字段不一致问题")
    print("=" * 60)
    
    # 1. 修复数据库表
    fix_category_table()
    fix_supplier_table()
    fix_maintenance_record_table()
    
    # 2. 同步数据
    synchronize_supplier_status()
    synchronize_category_status()
    
    # 3. 修复表单文件
    fix_forms()
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
    print("\n修复内容总结：")
    print("1. Category 表添加了 status 字段（兼容旧查询）")
    print("2. Supplier 表添加了 is_active 字段（统一命名）")
    print("3. 表单文件统一使用 is_active 字段进行查询")
    print("4. 同步了所有状态数据")
    print("\n建议：")
    print("- 重启 Flask 应用以应用更改")
    print("- 测试备件管理功能是否正常")

if __name__ == '__main__':
    main()
