# -*- coding: utf-8 -*-
"""
角色权限管理路由
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.utils.decorators import permission_required
import json
from datetime import datetime

roles_bp = Blueprint('roles', __name__, template_folder='../templates/roles')


@roles_bp.route('/')
@login_required
@permission_required('system', 'read')
def roles_index():
    """角色管理首页"""
    return render_template('roles/index.html')


@roles_bp.route('/api/list')
@login_required
@permission_required('system', 'read')
def get_roles():
    """获取角色列表"""
    try:
        roles = Role.query.order_by(Role.created_at.desc()).all()
        
        roles_data = []
        for role in roles:
            user_count = role.users.count() if role.users else 0
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'display_name': role.display_name,
                'description': role.description,
                'is_system': role.is_system,
                'user_count': user_count,
                'created_at': role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else None
            })
        
        return jsonify({
            'status': 'success',
            'data': roles_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取角色列表失败：{str(e)}'
        }), 500


@roles_bp.route('/api/<int:role_id>')
@login_required
@permission_required('system', 'read')
def get_role(role_id):
    """获取单个角色详情"""
    try:
        role = Role.query.get_or_404(role_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': role.id,
                'name': role.name,
                'display_name': role.display_name,
                'description': role.description,
                'permissions': role.get_permissions(),
                'is_system': role.is_system
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取角色失败：{str(e)}'
        }), 500


@roles_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('system', 'write')
def create_role():
    """创建角色"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'display_name' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        # 检查角色名称是否已存在
        existing_role = Role.query.filter_by(name=data['name']).first()
        if existing_role:
            return jsonify({
                'status': 'error',
                'message': '角色名称已存在'
            }), 400
        
        role = Role(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description', ''),
            permissions=json.dumps(data.get('permissions', {})),
            is_system=False
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '角色创建成功',
            'data': {'id': role.id}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'创建角色失败：{str(e)}'
        }), 500


@roles_bp.route('/api/<int:role_id>/update', methods=['PUT'])
@login_required
@permission_required('system', 'write')
def update_role(role_id):
    """更新角色"""
    try:
        role = Role.query.get_or_404(role_id)
        
        if role.is_system:
            return jsonify({
                'status': 'error',
                'message': '系统内置角色不可修改'
            }), 400
        
        data = request.get_json()
        
        if 'display_name' in data:
            role.display_name = data['display_name']
        if 'description' in data:
            role.description = data['description']
        if 'permissions' in data:
            role.permissions = json.dumps(data['permissions'])
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '角色更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'更新角色失败：{str(e)}'
        }), 500


@roles_bp.route('/api/<int:role_id>/delete', methods=['DELETE'])
@login_required
@permission_required('system', 'write')
def delete_role(role_id):
    """删除角色"""
    try:
        role = Role.query.get_or_404(role_id)
        
        if role.is_system:
            return jsonify({
                'status': 'error',
                'message': '系统内置角色不可删除'
            }), 400
        
        # 检查是否有用户使用此角色
        user_count = role.users.count() if role.users else 0
        if user_count > 0:
            return jsonify({
                'status': 'error',
                'message': f'该角色下还有 {user_count} 个用户，无法删除'
            }), 400
        
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '角色删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除角色失败：{str(e)}'
        }), 500


@roles_bp.route('/api/<int:role_id>/users')
@login_required
@permission_required('system', 'read')
def get_role_users(role_id):
    """获取角色下的用户列表"""
    try:
        role = Role.query.get_or_404(role_id)
        users = role.users.all() if role.users else []
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'email': user.email,
                'is_active': user.is_active
            })
        
        return jsonify({
            'status': 'success',
            'data': users_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取用户列表失败：{str(e)}'
        }), 500


@roles_bp.route('/api/permissions/modules')
@login_required
@permission_required('system', 'read')
def get_permission_modules():
    """获取权限模块列表"""
    modules = [
        {'code': 'spare_parts', 'name': '备件管理'},
        {'code': 'batches', 'name': '批次管理'},
        {'code': 'warehouses', 'name': '仓库管理'},
        {'code': 'transactions', 'name': '交易管理'},
        {'code': 'equipment', 'name': '设备管理'},
        {'code': 'maintenance', 'name': '维修管理'},
        {'code': 'purchase', 'name': '采购管理'},
        {'code': 'reports', 'name': '报表统计'},
        {'code': 'system', 'name': '系统管理'},
        {'code': 'backup', 'name': '数据备份'},
        {'code': 'monitor', 'name': '系统监控'},
        {'code': 'logs', 'name': '日志审计'},
        {'code': 'config', 'name': '系统配置'},
        {'code': 'roles', 'name': '角色管理'}
    ]
    
    actions = [
        {'code': 'read', 'name': '查看'},
        {'code': 'create', 'name': '创建'},
        {'code': 'update', 'name': '编辑'},
        {'code': 'delete', 'name': '删除'},
        {'code': 'export', 'name': '导出'},
        {'code': 'admin', 'name': '管理'}
    ]
    
    return jsonify({
        'status': 'success',
        'data': {
            'modules': modules,
            'actions': actions
        }
    })
