# -*- coding: utf-8 -*-
"""
数据库备份管理路由
"""

from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from app.utils.decorators import permission_required
from app.services.database_backup_service import DatabaseBackupService
import os

backup_bp = Blueprint('backup', __name__, template_folder='../templates/backup')


@backup_bp.route('/')
@login_required
@permission_required('system', 'read')
def backup_index():
    """备份管理首页"""
    return render_template('backup/index.html')


@backup_bp.route('/api/list')
@login_required
@permission_required('system', 'read')
def get_backups():
    """获取备份列表"""
    backups = DatabaseBackupService.get_backup_list()
    return jsonify({
        'status': 'success',
        'data': backups
    })


@backup_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('system', 'write')
def create_backup():
    """创建备份"""
    data = request.get_json()
    backup_name = data.get('backup_name') if data else None
    
    success, result = DatabaseBackupService.create_backup(
        backup_name=backup_name,
        created_by=current_user.id
    )
    
    if success:
        return jsonify({
            'status': 'success',
            'message': '备份创建成功',
            'data': result.to_dict()
        })
    else:
        return jsonify({
            'status': 'error',
            'message': result
        }), 400


@backup_bp.route('/api/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('system', 'write')
def delete_backup(id):
    """删除备份"""
    success, message = DatabaseBackupService.delete_backup(id)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': message
        })
    else:
        return jsonify({
            'status': 'error',
            'message': message
        }), 400


@backup_bp.route('/api/<int:id>/restore', methods=['POST'])
@login_required
@permission_required('system', 'admin')
def restore_backup(id):
    """恢复备份"""
    success, message = DatabaseBackupService.restore_backup(id)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': message
        })
    else:
        return jsonify({
            'status': 'error',
            'message': message
        }), 400


@backup_bp.route('/api/<int:id>/download')
@login_required
@permission_required('system', 'read')
def download_backup(id):
    """下载备份"""
    backup = DatabaseBackupService.get_backup_list()
    backup_item = next((b for b in backup if b['id'] == id), None)
    
    if not backup_item:
        return jsonify({
            'status': 'error',
            'message': '备份不存在'
        }), 404
    
    if not os.path.exists(backup_item['backup_file']):
        return jsonify({
            'status': 'error',
            'message': '备份文件不存在'
        }), 404
    
    return send_file(
        backup_item['backup_file'],
        as_attachment=True,
        download_name=os.path.basename(backup_item['backup_file'])
    )


@backup_bp.route('/api/cleanup', methods=['POST'])
@login_required
@permission_required('system', 'admin')
def cleanup_backups():
    """清理旧备份"""
    data = request.get_json()
    days = data.get('days', 30) if data else 30
    
    deleted_count = DatabaseBackupService.cleanup_old_backups(days)
    
    return jsonify({
        'status': 'success',
        'message': f'清理了 {deleted_count} 个旧备份',
        'data': {'deleted_count': deleted_count}
    })
