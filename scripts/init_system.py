"""
系统初始化脚本
创建系统角色和默认管理员账户
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.extensions import generate_password_hash


def create_system_roles():
    """创建系统角色"""
    roles = [
        {
            'name': 'admin',
            'display_name': '系统管理员',
            'description': '拥有系统所有权限',
            'is_system': True,
            'permissions': {
                'spare_part': ['*'],
                'warehouse': ['*'],
                'transaction': ['*'],
                'equipment': ['*'],
                'maintenance': ['*'],
                'purchase': ['*'],
                'report': ['*'],
                'system': ['*'],
                'user': ['*']
            }
        },
        {
            'name': 'warehouse_manager',
            'display_name': '仓库管理员',
            'description': '管理仓库和库存',
            'is_system': True,
            'permissions': {
                'spare_part': ['view', 'create', 'update'],
                'warehouse': ['*'],
                'transaction': ['*'],
                'equipment': ['view'],
                'maintenance': ['view'],
                'purchase': ['view'],
                'report': ['view']
            }
        },
        {
            'name': 'purchaser',
            'display_name': '采购员',
            'description': '负责采购管理',
            'is_system': True,
            'permissions': {
                'spare_part': ['view'],
                'warehouse': ['view'],
                'purchase': ['*'],
                'supplier': ['*'],
                'report': ['view']
            }
        },
        {
            'name': 'maintenance_manager',
            'display_name': '维修管理员',
            'description': '管理设备和维修',
            'is_system': True,
            'permissions': {
                'spare_part': ['view'],
                'warehouse': ['view'],
                'transaction': ['create'],
                'equipment': ['*'],
                'maintenance': ['*'],
                'report': ['view']
            }
        },
        {
            'name': 'accountant',
            'display_name': '财务人员',
            'description': '负责财务和报表',
            'is_system': True,
            'permissions': {
                'spare_part': ['view'],
                'warehouse': ['view'],
                'purchase': ['view'],
                'maintenance': ['view'],
                'report': ['*']
            }
        },
        {
            'name': 'normal_user',
            'display_name': '普通用户',
            'description': '普通用户，只有查看权限',
            'is_system': True,
            'permissions': {
                'spare_part': ['view'],
                'equipment': ['view'],
                'maintenance': ['view']
            }
        }
    ]
    
    import json
    for role_data in roles:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(
                name=role_data['name'],
                display_name=role_data['display_name'],
                description=role_data['description'],
                is_system=role_data['is_system'],
                permissions=json.dumps(role_data.get('permissions', {}))
            )
            db.session.add(role)
            print(f"创建角色：{role_data['display_name']}")
        else:
            print(f"角色已存在：{role_data['display_name']}")
    
    db.session.commit()
    print("系统角色初始化完成！")


def create_default_admin():
    """创建默认管理员账户"""
    admin_user = User.query.filter_by(username='admin').first()
    
    if not admin_user:
        # 获取 admin 角色
        admin_role = Role.query.filter_by(name='admin').first()
        
        if admin_role:
            user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                real_name='系统管理员',
                role_id=admin_role.id,
                is_admin=True,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            print("\n默认管理员账户创建成功！")
            print("用户名：admin")
            print("密码：admin123")
        else:
            print("错误：未找到 admin 角色，请先创建系统角色")
    else:
        print("管理员账户已存在")


if __name__ == '__main__':
    app = create_app('development')
    
    with app.app_context():
        print("=" * 60)
        print("开始初始化系统...")
        print("=" * 60)
        
        # 创建系统角色
        create_system_roles()
        
        # 创建默认管理员
        create_default_admin()
        
        print("=" * 60)
        print("系统初始化完成！")
        print("=" * 60)
