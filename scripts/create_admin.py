"""
直接创建管理员账户脚本
使用 SQL 直接插入数据，绕过模型关系
"""

import sys
import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# 获取数据库配置
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'spare_parts_db')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')

def create_admin():
    """创建系统管理员账户"""
    
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
        
        # 1. 检查并创建 admin 角色
        cursor.execute("SELECT id FROM role WHERE name = 'admin'")
        role = cursor.fetchone()
        
        if not role:
            # 创建 admin 角色
            cursor.execute("""
                INSERT INTO role (name, display_name, description, is_system, permissions)
                VALUES ('admin', '系统管理员', '拥有系统所有权限', 1, '{}')
            """)
            role_id = cursor.lastrowid
            print("✓ 创建 admin 角色成功")
        else:
            role_id = role[0]
            print("✓ admin 角色已存在")
        
        # 2. 检查管理员账户是否存在
        cursor.execute("SELECT id FROM user WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if not admin:
            # 生成密码哈希
            password_hash = generate_password_hash('Kra@211314')
            
            # 创建管理员账户
            cursor.execute("""
                INSERT INTO user (
                    username, email, password_hash, real_name, 
                    role_id, is_admin, is_active
                ) VALUES (
                    'admin',
                    '41717654@qq.com',
                    %s,
                    '系统管理员',
                    %s,
                    1,
                    1
                )
            """, (password_hash, role_id))
            
            connection.commit()
            print("\n✓ 管理员账户创建成功！")
            print("=" * 60)
            print("用户名：admin")
            print("邮箱：41717654@qq.com")
            print("密码：Kra@211314")
            print("=" * 60)
        else:
            # 更新现有管理员账户
            password_hash = generate_password_hash('Kra@211314')
            cursor.execute("""
                UPDATE user 
                SET email = '41717654@qq.com',
                    password_hash = %s,
                    role_id = %s,
                    is_admin = 1,
                    is_active = 1
                WHERE username = 'admin'
            """, (password_hash, role_id))
            
            connection.commit()
            print("\n✓ 管理员账户已更新！")
            print("=" * 60)
            print("用户名：admin")
            print("邮箱：41717654@qq.com")
            print("密码：Kra@211314")
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
    print("开始创建系统管理员...")
    print("=" * 60)
    create_admin()
    print("\n完成！")
