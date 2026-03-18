"""
直接修复数据库字段不一致问题（使用 pymysql）
"""

import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Kra@211314',
    'database': 'spare_parts_db'
}

def execute_sql(sql, description):
    """执行 SQL 语句"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        print(f"✓ {description}")
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"✗ {description} - 错误：{e}")
        return False

def check_column_exists(table_name, column_name):
    """检查列是否存在"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        sql = f"""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'spare_parts_db' 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
        """
        cursor.execute(sql)
        result = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        return result > 0
    except Exception as e:
        print(f"✗ 检查字段失败：{table_name}.{column_name} - 错误：{e}")
        return False

def add_column_if_not_exists(table_name, column_name, column_type, default=None, comment=None):
    """如果列不存在则添加"""
    if check_column_exists(table_name, column_name):
        print(f"- 字段已存在：{table_name}.{column_name}")
        return True
    
    sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_type}"
    if default is not None:
        sql += f" DEFAULT {default}"
    if comment:
        sql += f" COMMENT '{comment}'"
    
    return execute_sql(sql, f"添加字段：{table_name}.{column_name}")

def update_data(sql, description):
    """更新数据"""
    return execute_sql(sql, description)

def fix_forms():
    """修复表单文件"""
    print("\n=== 修复表单文件 ===")
    form_file = 'd:/Trae/spare_management/app/forms/spare_parts.py'
    
    with open(form_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 修复 SparePartSearchForm 中的 Category 查询
    old_category_query = "Category.query.filter_by(status='active')"
    new_category_query = "Category.query.filter_by(is_active=True)"
    
    if old_category_query in content:
        content = content.replace(old_category_query, new_category_query)
        print("✓ 已修复 Category 查询（status -> is_active）")
        modified = True
    
    # 修复 SparePartSearchForm 中的 Supplier 查询
    old_supplier_query = "Supplier.query.filter_by(status='active')"
    new_supplier_query = "Supplier.query.filter_by(is_active=True)"
    
    if old_supplier_query in content:
        content = content.replace(old_supplier_query, new_supplier_query)
        print("✓ 已修复 Supplier 查询（status -> is_active）")
        modified = True
    
    if modified:
        with open(form_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ 表单文件已更新")
    else:
        print("- 表单文件无需修改")

def main():
    print("=" * 60)
    print("开始修复所有字段不一致问题")
    print("=" * 60)
    
    # 1. 修复 Category 表：添加 status 字段
    print("\n=== 修复 Category 表 ===")
    add_column_if_not_exists(
        'category',
        'status',
        "VARCHAR(20)",
        default="'active'",
        comment='状态 (active/inactive)'
    )
    
    # 2. 修复 Supplier 表：添加 is_active 字段
    print("\n=== 修复 Supplier 表 ===")
    add_column_if_not_exists(
        'supplier',
        'is_active',
        "BOOLEAN",
        default="TRUE",
        comment='是否启用'
    )
    
    # 3. 同步 Supplier 数据
    print("\n=== 同步 Supplier 状态字段 ===")
    update_sql = """
        UPDATE supplier 
        SET is_active = CASE 
            WHEN status = 'active' THEN TRUE 
            ELSE FALSE 
        END
        WHERE is_active IS NULL
    """
    update_data(update_sql, "同步 Supplier 状态字段")
    
    # 4. 同步 Category 数据
    print("\n=== 同步 Category 状态字段 ===")
    update_sql = """
        UPDATE category 
        SET status = CASE 
            WHEN is_active = TRUE THEN 'active' 
            ELSE 'inactive' 
        END
        WHERE status IS NULL
    """
    update_data(update_sql, "同步 Category 状态字段")
    
    # 5. 修复表单文件
    fix_forms()
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
    print("\n修复内容总结：")
    print("1. Category 表添加了 status 字段")
    print("2. Supplier 表添加了 is_active 字段")
    print("3. 同步了所有状态数据")
    print("4. 表单文件统一使用 is_active 字段进行查询")
    print("\n建议：")
    print("- 重启 Flask 应用以应用更改")
    print("- 测试备件管理功能是否正常")

if __name__ == '__main__':
    main()
