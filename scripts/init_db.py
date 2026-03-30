#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
功能:
1. 创建数据库
2. 执行 SQL 脚本创建所有表
3. 初始化基础数据
"""

import pymysql
import os
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Kra@211314.',
    'charset': 'utf8mb4'
}

DATABASE_NAME = 'spare_parts_db'


def print_separator(char="=", length=80):
    print(char * length)


def get_connection(database=None):
    """获取数据库连接"""
    config = DB_CONFIG.copy()
    if database:
        config['database'] = database
    return pymysql.connect(**config)


def create_database():
    """创建数据库"""
    print(f"\n[1/3] 创建数据库 {DATABASE_NAME}...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 检查数据库是否已存在
        cursor.execute("SHOW DATABASES LIKE %s", (DATABASE_NAME,))
        if cursor.fetchone():
            print(f"  数据库 {DATABASE_NAME} 已存在，正在删除...")
            cursor.execute(f"DROP DATABASE {DATABASE_NAME}")
        
        # 创建数据库
        cursor.execute(f"""
            CREATE DATABASE {DATABASE_NAME} 
            CHARACTER SET utf8mb4 
            COLLATE utf8mb4_unicode_ci
        """)
        print(f"  [OK] 数据库 {DATABASE_NAME} 创建成功")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] 创建数据库失败：{str(e)}")
        return False


def execute_sql_script():
    """执行 SQL 脚本"""
    print(f"\n[2/3] 执行 SQL 脚本创建表...")
    
    try:
        # 读取 SQL 脚本
        script_path = os.path.join(os.path.dirname(__file__), 'create_tables.sql')
        
        if not os.path.exists(script_path):
            print(f"  [ERROR] SQL 脚本不存在：{script_path}")
            return False
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 连接数据库并执行
        conn = get_connection(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 执行 SQL 脚本 (按分号分割)
        statements = sql_script.split(';')
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
            
            try:
                cursor.execute(statement)
                success_count += 1
            except Exception as e:
                # 忽略一些非关键错误
                error_msg = str(e)
                if 'DROP TABLE IF EXISTS' in statement and 'doesn\'t exist' not in error_msg:
                    error_count += 1
                    print(f"  警告：语句 {i+1} 执行失败：{error_msg}")
        
        conn.commit()
        
        print(f"  [OK] SQL 脚本执行完成")
        print(f"    成功：{success_count} 条语句")
        print(f"    失败：{error_count} 条语句")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] 执行 SQL 脚本失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_database():
    """验证数据库"""
    print(f"\n[3/3] 验证数据库...")
    
    try:
        conn = get_connection(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 检查表数量
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"  [OK] 共创建 {len(tables)} 个表")
        
        # 显示所有表
        print(f"\n  表列表:")
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            
            # 获取表注释
            cursor.execute(f"SHOW TABLE STATUS WHERE Name = '{table_name}'")
            status = cursor.fetchone()
            comment = status[4] if status and len(status) > 4 else ''
            
            print(f"    {i:2d}. {table_name:<30} {comment}")
        
        # 检查角色数据
        cursor.execute("SELECT COUNT(*) FROM role")
        role_count = cursor.fetchone()[0]
        print(f"\n  [OK] 初始化 {role_count} 个系统角色")
        
        # 显示角色
        cursor.execute("SELECT name, display_name FROM role")
        roles = cursor.fetchall()
        print(f"\n  系统角色:")
        for role in roles:
            print(f"    - {role[0]} ({role[1]})")
        
        cursor.close()
        conn.close()
        
        print(f"\n{'='*80}")
        print(f"数据库初始化完成!")
        print(f"{'='*80}")
        print(f"数据库：{DATABASE_NAME}")
        print(f"表数量：{len(tables)}")
        print(f"系统角色：{role_count} 个")
        print(f"{'='*80}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] 验证失败：{str(e)}")
        return False


def main():
    """主函数"""
    print_separator()
    print("备件管理系统 - 数据库初始化")
    print_separator()
    print(f"数据库：{DATABASE_NAME}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()
    
    # 1. 创建数据库
    if not create_database():
        print("\n数据库创建失败，终止操作")
        return False
    
    # 2. 执行 SQL 脚本
    if not execute_sql_script():
        print("\nSQL 脚本执行失败，但数据库已创建")
        return False
    
    # 3. 验证数据库
    if not verify_database():
        print("\n数据库验证失败")
        return False
    
    return True


if __name__ == '__main__':
    print("\n重要提示:")
    print("=" * 80)
    print("1. 本脚本会创建数据库并初始化所有表")
    print("2. 如果数据库已存在，会被删除并重新创建 (数据会丢失!)")
    print("3. 请确保已备份重要数据")
    print("=" * 80)
    print()
    
    response = input("是否继续？(输入 YES 继续，其他取消): ")
    if response != 'YES':
        print("操作已取消")
        exit(0)
    
    success = main()
    
    if success:
        print("\n[OK] 数据库初始化成功!")
        print("\n下一步:")
        print("1. 安装 Python 依赖：pip install -r requirements.txt")
        print("2. 启动应用：python run.py")
        print("3. 访问系统：http://localhost:5000")
        print("4. 默认管理员：admin / admin123")
    else:
        print("\n[ERROR] 数据库初始化失败!")
    
    input("\n按回车键退出...")
