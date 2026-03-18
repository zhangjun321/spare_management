#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
插入初始数据脚本
"""

import pymysql
import json

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Kra@211314',
    'database': 'spare_parts_db',
    'charset': 'utf8mb4'
}


def insert_system_roles():
    """插入系统角色"""
    print("正在插入系统角色...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        roles = [
            {
                'name': 'admin',
                'display_name': '系统管理员',
                'description': '拥有所有权限',
                'permissions': json.dumps({"*": ["create", "read", "update", "delete"]}, ensure_ascii=False),
                'is_system': True
            },
            {
                'name': 'warehouse_manager',
                'display_name': '仓库管理员',
                'description': '负责仓库管理',
                'permissions': json.dumps({
                    "spare_parts": ["create", "read", "update"],
                    "batches": ["create", "read", "update"],
                    "warehouses": ["read"],
                    "transactions": ["create", "read"],
                    "reports": ["read"]
                }, ensure_ascii=False),
                'is_system': True
            },
            {
                'name': 'purchaser',
                'display_name': '采购员',
                'description': '负责采购管理',
                'permissions': json.dumps({
                    "spare_parts": ["read"],
                    "suppliers": ["create", "read", "update"],
                    "purchase": ["create", "read", "update"],
                    "reports": ["read"]
                }, ensure_ascii=False),
                'is_system': True
            },
            {
                'name': 'maintenance_manager',
                'display_name': '维修管理员',
                'description': '负责维修管理',
                'permissions': json.dumps({
                    "equipment": ["create", "read", "update"],
                    "maintenance": ["create", "read", "update", "delete"],
                    "spare_parts": ["read"],
                    "reports": ["read"]
                }, ensure_ascii=False),
                'is_system': True
            },
            {
                'name': 'accountant',
                'display_name': '财务人员',
                'description': '负责财务管理',
                'permissions': json.dumps({
                    "spare_parts": ["read"],
                    "maintenance": ["read"],
                    "purchase": ["read"],
                    "reports": ["read", "export"]
                }, ensure_ascii=False),
                'is_system': True
            },
            {
                'name': 'normal_user',
                'display_name': '普通用户',
                'description': '普通用户',
                'permissions': json.dumps({
                    "spare_parts": ["read"],
                    "inventory": ["read"]
                }, ensure_ascii=False),
                'is_system': True
            }
        ]
        
        for role_data in roles:
            # 检查是否已存在
            cursor.execute("SELECT id FROM role WHERE name = %s", (role_data['name'],))
            if cursor.fetchone():
                print(f"  角色 {role_data['display_name']} 已存在，跳过")
                continue
            
            # 插入角色
            cursor.execute("""
                INSERT INTO role (name, display_name, description, permissions, is_system)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                role_data['name'],
                role_data['display_name'],
                role_data['description'],
                role_data['permissions'],
                role_data['is_system']
            ))
            print(f"  ✓ 插入角色：{role_data['display_name']}")
        
        conn.commit()
        print("\n系统角色插入完成!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"错误：{str(e)}")
        return False


def create_default_admin():
    """创建默认管理员账户"""
    print("\n正在创建默认管理员账户...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取 admin 角色 ID
        cursor.execute("SELECT id FROM role WHERE name = 'admin'")
        result = cursor.fetchone()
        if not result:
            print("  ✗ 未找到 admin 角色")
            return False
        
        role_id = result[0]
        
        # 检查 admin 用户是否已存在
        cursor.execute("SELECT id FROM user WHERE username = 'admin'")
        if cursor.fetchone():
            print("  admin 用户已存在")
            return True
        
        # 使用 bcrypt 加密密码
        import bcrypt
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 插入管理员
        cursor.execute("""
            INSERT INTO user (username, email, password_hash, real_name, role_id, is_admin, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('admin', 'admin@example.com', password_hash, '系统管理员', role_id, True, True))
        
        conn.commit()
        print("  ✓ 默认管理员账户创建成功!")
        print("    用户名：admin")
        print("    密码：admin123")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"错误：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("="*80)
    print("插入初始数据")
    print("="*80)
    
    # 1. 插入系统角色
    if not insert_system_roles():
        print("\n角色插入失败")
        return False
    
    # 2. 创建默认管理员
    if not create_default_admin():
        print("\n管理员创建失败")
        return False
    
    print("\n" + "="*80)
    print("初始数据插入完成!")
    print("="*80)
    print("\n系统信息:")
    print("  - 6 个系统角色已创建")
    print("  - 默认管理员账户：admin / admin123")
    print("\n重要提示:")
    print("  首次登录后请立即修改管理员密码!")
    print("="*80)
    
    return True


if __name__ == '__main__':
    success = main()
    if not success:
        print("\n操作失败!")
    else:
        print("\n操作成功!")
    
    print("\n按回车键退出...")
    input()
