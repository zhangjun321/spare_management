# -*- coding: utf-8 -*-
"""
数据库备份管理路由 - 重写版本
"""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from app.services.database_backup_service import DatabaseBackupService
import os
import json
import logging

# 创建蓝图
backup_bp = Blueprint('backup', __name__, template_folder='../templates/backup')

# 配置日志
logger = logging.getLogger(__name__)


@backup_bp.route('/')
@login_required
def backup_index():
    """备份管理首页"""
    return render_template('backup/index.html')


@backup_bp.route('/api/list', methods=['GET'])
@login_required
def get_backups():
    """获取备份列表"""
    try:
        logger.info(f"用户 {current_user.username} 请求获取备份列表")
        backups = DatabaseBackupService.get_backup_list()
        logger.info(f"获取到 {len(backups)} 个备份")
        
        return jsonify({
            'status': 'success',
            'message': '获取成功',
            'data': backups
        }), 200
    except Exception as e:
        logger.error(f"获取备份列表失败：{str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'获取备份列表失败：{str(e)}'
        }), 500


@backup_bp.route('/api/create', methods=['POST'])
@login_required
def create_backup():
    """创建备份"""
    logger.error("!!! 进入 create_backup 函数 !!!")
    logger.error(f"当前用户：{current_user.username if current_user.is_authenticated else '匿名用户'}")
    logger.error(f"请求路径：{request.path}")
    logger.error(f"请求方法：{request.method}")
    
    try:
        logger.info(f"用户 {current_user.username} 请求创建备份")
        
        # 打印请求详情（不含敏感请求头）
        logger.info(f"请求方法：{request.method}")
        
        # 获取 JSON 数据
        data = request.get_json(silent=True)
        logger.info(f"解析后的数据：{data}")
        
        if data is None:
            logger.warning("请求数据为空，尝试从表单获取")
            data = {}
        
        # 获取备份名称
        backup_name = data.get('backup_name')
        logger.info(f"备份名称：{backup_name}")
        
        # 测试数据库备份服务
        logger.info("开始测试数据库备份服务...")
        from app.services.database_backup_service import DatabaseBackupService
        logger.info(f"BACKUP_DIR: {DatabaseBackupService.BACKUP_DIR}")
        logger.info(f"SQLALCHEMY_DATABASE_URI: {current_app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
        # 创建备份
        logger.info("开始执行备份...")
        success, result = DatabaseBackupService.create_backup(
            backup_name=backup_name,
            backup_type='manual',
            created_by=current_user.id
        )
        
        if success:
            logger.info(f"备份成功：{result.backup_name}")
            return jsonify({
                'status': 'success',
                'message': '备份创建成功',
                'data': result.to_dict()
            }), 200
        else:
            logger.error(f"备份失败：{result}")
            return jsonify({
                'status': 'error',
                'message': f'备份失败：{str(result)}'
            }), 400
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"创建备份时发生异常：{str(e)}")
        logger.error(f"异常堆栈：{error_traceback}")
        return jsonify({
            'status': 'error',
            'message': f'服务器错误：{str(e)}'
        }), 500


@backup_bp.route('/api/<int:backup_id>/delete', methods=['POST'])
@login_required
def delete_backup(backup_id):
    """删除备份"""
    try:
        logger.info(f"用户 {current_user.username} 请求删除备份 {backup_id}")
        success, message = DatabaseBackupService.delete_backup(backup_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
    except Exception as e:
        logger.error(f"删除备份失败：{str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'删除失败：{str(e)}'
        }), 500


@backup_bp.route('/api/<int:backup_id>/restore', methods=['POST'])
@login_required
def restore_backup(backup_id):
    """恢复备份"""
    try:
        logger.info(f"用户 {current_user.username} 请求恢复备份 {backup_id}")
        success, message = DatabaseBackupService.restore_backup(backup_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
    except Exception as e:
        logger.error(f"恢复备份失败：{str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'恢复失败：{str(e)}'
        }), 500


@backup_bp.route('/api/<int:backup_id>/download', methods=['GET'])
@login_required
def download_backup(backup_id):
    """下载备份"""
    try:
        logger.info(f"用户 {current_user.username} 请求下载备份 {backup_id}")
        
        # 获取备份信息
        backups = DatabaseBackupService.get_backup_list()
        backup_item = next((b for b in backups if b['id'] == backup_id), None)
        
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
    except Exception as e:
        logger.error(f"下载备份失败：{str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'下载失败：{str(e)}'
        }), 500


@backup_bp.route('/api/cleanup', methods=['POST'])
@login_required
def cleanup_backups():
    """清理旧备份"""
    try:
        logger.info(f"用户 {current_user.username} 请求清理旧备份")
        
        data = request.get_json(silent=True)
        if data is None:
            data = {}
        
        days = data.get('days', 30)
        logger.info(f"清理 {days} 天前的备份")
        
        deleted_count = DatabaseBackupService.cleanup_old_backups(days)
        
        return jsonify({
            'status': 'success',
            'message': f'清理了 {deleted_count} 个旧备份',
            'data': {'deleted_count': deleted_count}
        }), 200
    except Exception as e:
        logger.error(f"清理备份失败：{str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'清理失败：{str(e)}'
        }), 500
