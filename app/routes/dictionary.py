# -*- coding: utf-8 -*-
"""
数据字典管理路由
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.extensions import db
from app.models.dictionary import DictType, DictItem, init_system_dicts
from app.utils.decorators import permission_required
from datetime import datetime

dictionary_bp = Blueprint('dictionary', __name__, template_folder='../templates/dictionary')


@dictionary_bp.route('/')
@login_required
@permission_required('system', 'read')
def dictionary_index():
    """字典管理首页"""
    # 初始化系统内置字典（如果不存在）
    try:
        init_system_dicts()
    except Exception as e:
        pass
    return render_template('dictionary/index.html')


@dictionary_bp.route('/api/types')
@login_required
@permission_required('system', 'read')
def get_dict_types():
    """获取字典类型列表"""
    try:
        types = DictType.query.order_by(DictType.sort_order, DictType.created_at.desc()).all()
        
        types_data = []
        for dict_type in types:
            item_count = dict_type.items.count() if dict_type.items else 0
            types_data.append({
                'id': dict_type.id,
                'dict_name': dict_type.dict_name,
                'dict_code': dict_type.dict_code,
                'description': dict_type.description,
                'status': dict_type.status,
                'is_system': dict_type.is_system,
                'sort_order': dict_type.sort_order,
                'item_count': item_count,
                'created_at': dict_type.created_at.strftime('%Y-%m-%d %H:%M:%S') if dict_type.created_at else None
            })
        
        return jsonify({
            'status': 'success',
            'data': types_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取字典类型列表失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/types/<int:type_id>')
@login_required
@permission_required('system', 'read')
def get_dict_type(type_id):
    """获取单个字典类型详情"""
    try:
        dict_type = DictType.query.get_or_404(type_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': dict_type.id,
                'dict_name': dict_type.dict_name,
                'dict_code': dict_type.dict_code,
                'description': dict_type.description,
                'status': dict_type.status,
                'is_system': dict_type.is_system,
                'sort_order': dict_type.sort_order
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取字典类型失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/types/create', methods=['POST'])
@login_required
@permission_required('system', 'write')
def create_dict_type():
    """创建字典类型"""
    try:
        data = request.get_json()
        
        if not data or 'dict_name' not in data or 'dict_code' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        # 检查字典编码是否已存在
        existing = DictType.query.filter_by(dict_code=data['dict_code']).first()
        if existing:
            return jsonify({
                'status': 'error',
                'message': '字典编码已存在'
            }), 400
        
        dict_type = DictType(
            dict_name=data['dict_name'],
            dict_code=data['dict_code'],
            description=data.get('description', ''),
            status=data.get('status', True),
            is_system=False,
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(dict_type)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '字典类型创建成功',
            'data': {'id': dict_type.id}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'创建字典类型失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/types/<int:type_id>/update', methods=['PUT'])
@login_required
@permission_required('system', 'write')
def update_dict_type(type_id):
    """更新字典类型"""
    try:
        dict_type = DictType.query.get_or_404(type_id)
        
        if dict_type.is_system:
            return jsonify({
                'status': 'error',
                'message': '系统内置字典不可修改'
            }), 400
        
        data = request.get_json()
        
        if 'dict_name' in data:
            dict_type.dict_name = data['dict_name']
        if 'description' in data:
            dict_type.description = data['description']
        if 'status' in data:
            dict_type.status = data['status']
        if 'sort_order' in data:
            dict_type.sort_order = data['sort_order']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '字典类型更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'更新字典类型失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/types/<int:type_id>/delete', methods=['DELETE'])
@login_required
@permission_required('system', 'write')
def delete_dict_type(type_id):
    """删除字典类型"""
    try:
        dict_type = DictType.query.get_or_404(type_id)
        
        if dict_type.is_system:
            return jsonify({
                'status': 'error',
                'message': '系统内置字典不可删除'
            }), 400
        
        db.session.delete(dict_type)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '字典类型删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除字典类型失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/types/<int:type_id>/items')
@login_required
@permission_required('system', 'read')
def get_dict_items(type_id):
    """获取字典项列表"""
    try:
        dict_type = DictType.query.get_or_404(type_id)
        items = dict_type.items.order_by(DictItem.sort_order, DictItem.created_at.desc()).all()
        
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'dict_type_id': item.dict_type_id,
                'item_label': item.item_label,
                'item_value': item.item_value,
                'description': item.description,
                'status': item.status,
                'sort_order': item.sort_order,
                'css_class': item.css_class,
                'is_default': item.is_default,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else None
            })
        
        return jsonify({
            'status': 'success',
            'data': items_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取字典项列表失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/items/<int:item_id>')
@login_required
@permission_required('system', 'read')
def get_dict_item(item_id):
    """获取单个字典项详情"""
    try:
        item = DictItem.query.get_or_404(item_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': item.id,
                'dict_type_id': item.dict_type_id,
                'item_label': item.item_label,
                'item_value': item.item_value,
                'description': item.description,
                'status': item.status,
                'sort_order': item.sort_order,
                'css_class': item.css_class,
                'is_default': item.is_default
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取字典项失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/items/create', methods=['POST'])
@login_required
@permission_required('system', 'write')
def create_dict_item():
    """创建字典项"""
    try:
        data = request.get_json()
        
        if not data or 'item_label' not in data or 'item_value' not in data or 'dict_type_id' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400
        
        # 检查字典类型是否存在
        dict_type = DictType.query.get_or_404(data['dict_type_id'])
        
        if dict_type.is_system:
            return jsonify({
                'status': 'error',
                'message': '系统内置字典不可修改'
            }), 400
        
        item = DictItem(
            dict_type_id=data['dict_type_id'],
            item_label=data['item_label'],
            item_value=data['item_value'],
            description=data.get('description', ''),
            status=data.get('status', True),
            sort_order=data.get('sort_order', 0),
            css_class=data.get('css_class', ''),
            is_default=data.get('is_default', False)
        )
        
        # 如果设为默认，取消其他的默认
        if item.is_default:
            dict_type.items.filter_by(is_default=True).update({'is_default': False})
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '字典项创建成功',
            'data': {'id': item.id}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'创建字典项失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/items/<int:item_id>/update', methods=['PUT'])
@login_required
@permission_required('system', 'write')
def update_dict_item(item_id):
    """更新字典项"""
    try:
        item = DictItem.query.get_or_404(item_id)
        
        # 检查是否是系统内置
        if item.dict_type and item.dict_type.is_system:
            return jsonify({
                'status': 'error',
                'message': '系统内置字典不可修改'
            }), 400
        
        data = request.get_json()
        
        if 'item_label' in data:
            item.item_label = data['item_label']
        if 'item_value' in data:
            item.item_value = data['item_value']
        if 'description' in data:
            item.description = data['description']
        if 'status' in data:
            item.status = data['status']
        if 'sort_order' in data:
            item.sort_order = data['sort_order']
        if 'css_class' in data:
            item.css_class = data['css_class']
        
        # 处理默认选项
        if 'is_default' in data:
            was_default = item.is_default
            item.is_default = data['is_default']
            
            # 如果设为默认，取消其他的默认
            if item.is_default and not was_default:
                DictItem.query.filter(
                    DictItem.dict_type_id == item.dict_type_id,
                    DictItem.id != item.id
                ).update({'is_default': False})
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '字典项更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'更新字典项失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/items/<int:item_id>/delete', methods=['DELETE'])
@login_required
@permission_required('system', 'write')
def delete_dict_item(item_id):
    """删除字典项"""
    try:
        item = DictItem.query.get_or_404(item_id)
        
        # 检查是否是系统内置
        if item.dict_type and item.dict_type.is_system:
            return jsonify({
                'status': 'error',
                'message': '系统内置字典不可修改'
            }), 400
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '字典项删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除字典项失败：{str(e)}'
        }), 500


@dictionary_bp.route('/api/public/<dict_code>')
@login_required
def get_public_dict(dict_code):
    """获取公共字典数据（用于前端展示）"""
    try:
        dict_type = DictType.query.filter_by(dict_code=dict_code, status=True).first_or_404()
        
        items = dict_type.items.filter_by(status=True).order_by(
            DictItem.sort_order, DictItem.created_at.desc()
        ).all()
        
        items_data = []
        for item in items:
            items_data.append({
                'label': item.item_label,
                'value': item.item_value,
                'css_class': item.css_class,
                'is_default': item.is_default
            })
        
        return jsonify({
            'status': 'success',
            'data': items_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取字典数据失败：{str(e)}'
        }), 500
