#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本 - 直接执行版本
自动创建数据库和所有表，无需用户交互
"""

import pymysql
import os
import sys
from datetime import datetime

# 数据库配置 - 尝试多个可能的密码
PASSWORDS_TO_TRY = [
    'Kra@211314.',
    'Kra@211314',
    'Kr@211314',
    ''
]

DATABASE_NAME = 'spare_parts_db'
SQL_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'create_tables.sql')


def try_connect(password):
    """尝试连接 MySQL"""
    try:
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password=password,
            charset='utf8mb4'
        )
        return conn
    except Exception:
        return None


def get_connection():
    """获取数据库连接"""
    print("正在尝试连接 MySQL...")
    
    for password in PASSWORDS_TO_TRY:
        print(f"  尝试密码：{'*' * len(password)}")
        conn = try_connect(password)
        if conn:
            print(f"  ✓ 连接成功!")
            return conn, password
    
    print("  ✗ 所有密码都尝试失败")
    return None, None


def create_database(conn, db_name):
    """创建数据库"""
    print(f"\n[1/3] 创建数据库 {db_name}...")
    
    try:
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
        if cursor.fetchone():
            print(f"  数据库已存在，正在删除...")
            cursor.execute(f"DROP DATABASE {db_name}")
        
        # 创建数据库
        cursor.execute(f"""
            CREATE DATABASE {db_name} 
            CHARACTER SET utf8mb4 
            COLLATE utf8mb4_unicode_ci
        """)
        print(f"  ✓ 数据库 {db_name} 创建成功")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"  ✗ 创建失败：{str(e)}")
        return False


def execute_sql_script(conn, db_name):
    """执行 SQL 脚本"""
    print(f"\n[2/3] 执行 SQL 脚本...")
    
    try:
        # 切换到新数据库
        conn.select_db(db_name)
        cursor = conn.cursor()
        
        # 读取 SQL 脚本
        if not os.path.exists(SQL_SCRIPT_PATH):
            print(f"  ✗ SQL 脚本不存在：{SQL_SCRIPT_PATH}")
            return False
        
        with open(SQL_SCRIPT_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 执行 SQL (按分号分割)
        statements = sql_script.split(';')
        success_count = 0
        
        print(f"  正在执行 {len(statements)} 条 SQL 语句...")
        
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
            
            try:
                cursor.execute(statement)
                success_count += 1
            except Exception as e:
                # 忽略 DROP TABLE 错误
                if 'DROP TABLE' in statement and "doesn't exist" in str(e):
                    success_count += 1
                else:
                    print(f"    警告：语句 {i+1} 失败：{str(e)[:100]}")
        
        conn.commit()
        print(f"  ✓ 执行完成，成功 {success_count} 条语句")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"  ✗ 执行失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_database(conn, db_name):
    """验证数据库"""
    print(f"\n[3/3] 验证数据库...")
    
    try:
        conn.select_db(db_name)
        cursor = conn.cursor()
        
        # 检查表数量
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"  ✓ 共创建 {len(tables)} 个表")
        
        # 显示表名
        print(f"\n  表列表:")
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            try:
                cursor.execute(f"SHOW TABLE STATUS WHERE Name = '{table_name}'")
                status = cursor.fetchone()
                comment = status[4] if status and len(status) > 4 else ''
                print(f"    {i:2d}. {table_name:<35} {comment}")
            except:
                print(f"    {i:2d}. {table_name}")
        
        # 检查角色数据
        cursor.execute("SELECT COUNT(*) FROM role")
        role_count = cursor.fetchone()[0]
        print(f"\n  ✓ 初始化 {role_count} 个系统角色")
        
        # 显示角色
        cursor.execute("SELECT name, display_name FROM role")
        roles = cursor.fetchall()
        print(f"\n  系统角色:")
        for role in roles:
            print(f"    - {role[0]:<25} ({role[1]})")
        
        cursor.close()
        
        print(f"\n{'='*80}")
        print(f"数据库初始化完成!")
        print(f"{'='*80}")
        print(f"数据库：{db_name}")
        print(f"表数量：{len(tables)}")
        print(f"系统角色：{role_count} 个")
        print(f"{'='*80}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 验证失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("="*80)
    print("备件管理系统 - 数据库初始化")
    print("="*80)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 1. 连接 MySQL
    conn, password = get_connection()
    if not conn:
        print("\n✗ 无法连接 MySQL，请检查:")
        print("  1. MySQL 服务是否启动")
        print("  2. root 用户密码是否正确")
        print("  3. 是否允许本地连接")
        return False
    
    # 2. 创建数据库
    if not create_database(conn, DATABASE_NAME):
        print("\n✗ 数据库创建失败")
        conn.close()
        return False
    
    # 3. 执行 SQL 脚本
    if not execute_sql_script(conn, DATABASE_NAME):
        print("\n✗ SQL 脚本执行失败")
        conn.close()
        return False
    
    # 4. 验证数据库
    if not verify_database(conn, DATABASE_NAME):
        print("\n✗ 数据库验证失败")
        conn.close()
        return False
    
    conn.close()
    
    print("\n✓ 所有操作成功完成!")
    print("\n下一步:")
    print("  1. 安装 Python 依赖：pip install -r requirements.txt")
    print("  2. 启动应用：python run.py")
    print("  3. 访问系统：http://localhost:5000")
    print("  4. 默认管理员：admin / admin123")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 发生错误：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n按回车键退出...")
    input()
