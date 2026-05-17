#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设置MySQL数据库 - 创建数据库和表
"""
import os
import sys
import io
from dotenv import load_dotenv

# 强制使用UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

try:
    import pymysql
    from pymysql.cursors import DictCursor
    
    # 连接MySQL服务器（不指定数据库，先创建数据库）
    print("正在连接MySQL服务器...")
    connection = pymysql.connect(
        host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        charset='utf8mb4',
        cursorclass=DictCursor
    )
    print("MySQL连接成功！")
    
    with connection.cursor() as cursor:
        # 创建数据库
        db_name = os.environ.get('MYSQL_DATABASE', 'spare_parts_db')
        print(f"正在创建数据库: {db_name}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("数据库创建成功！")
        
        # 选择数据库
        cursor.execute(f"USE `{db_name}`")
        
        # 执行迁移脚本
        migration_file = os.path.join(basedir, 'database', 'migrations', 'add_spare_part_advanced_models.sql')
        if os.path.exists(migration_file):
            print("正在执行数据库迁移...")
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
                # 按分号分割SQL语句，逐个执行
                statements = []
                current_statement = []
                in_multi_line = False
                
                for line in sql_content.split('\n'):
                    stripped = line.strip()
                    
                    if stripped.startswith('--') or stripped.startswith('#'):
                        continue
                        
                    if stripped:
                        current_statement.append(line)
                        
                        if stripped.endswith(';'):
                            statements.append('\n'.join(current_statement))
                            current_statement = []
                
                if current_statement:
                    statements.append('\n'.join(current_statement))
                
                for i, stmt in enumerate(statements, 1):
                    stmt = stmt.strip()
                    if stmt:
                        try:
                            cursor.execute(stmt)
                        except Exception as e:
                            print(f"  警告: 执行语句 {i} 时出错: {e}")
                
                connection.commit()
                print("数据库迁移完成！")
    
    connection.close()
    print("\n" + "=" * 80)
    print("MySQL数据库设置完成！")
    print("=" * 80)
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
