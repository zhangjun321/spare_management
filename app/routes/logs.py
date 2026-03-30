# -*- coding: utf-8 -*-
"""
系统日志审计路由
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.utils.decorators import permission_required
from app.extensions import db
from app.models.system_log import SystemLog
from app.models.user import User
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

logs_bp = Blueprint('logs', __name__, template_folder='../templates/logs')


@logs_bp.route('/')
@login_required
@permission_required('system', 'read')
def logs_index():
    """日志审计首页"""
    return render_template('logs/index.html')


@logs_bp.route('/api/list')
@login_required
@permission_required('system', 'read')
def get_logs():
    """获取日志列表"""
    # 获取筛选参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    module = request.args.get('module', type=str)
    action = request.args.get('action', type=str)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    
    # 构建查询
    query = SystemLog.query
    
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    
    if module:
        query = query.filter(SystemLog.module == module)
    
    if action:
        query = query.filter(SystemLog.action.contains(action))
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(SystemLog.created_at >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(SystemLog.created_at < end)
        except:
            pass
    
    # 排序
    query = query.order_by(SystemLog.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    
    # 转换为字典
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'action': log.action,
            'module': log.module,
            'user_id': log.user_id,
            'username': log.username,
            'ip_address': log.ip_address,
            'request_method': log.request_method,
            'request_url': log.request_url,
            'status': log.status,
            'error_message': log.error_message,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else None
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            'logs': logs_data,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    })


@logs_bp.route('/api/statistics')
@login_required
@permission_required('system', 'read')
def get_logs_statistics():
    """获取日志统计"""
    # 获取最近 7 天的数据
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # 按日期统计
    daily_stats = db.session.query(
        db.func.date(SystemLog.created_at).label('date'),
        db.func.count(SystemLog.id).label('count')
    ).filter(
        SystemLog.created_at >= seven_days_ago
    ).group_by(
        db.func.date(SystemLog.created_at)
    ).all()
    
    # 按用户统计
    user_stats = db.session.query(
        SystemLog.username,
        db.func.count(SystemLog.id).label('count')
    ).filter(
        SystemLog.created_at >= seven_days_ago
    ).group_by(
        SystemLog.username
    ).order_by(
        db.func.count(SystemLog.id).desc()
    ).limit(10).all()
    
    # 按模块统计
    module_stats = db.session.query(
        SystemLog.module,
        db.func.count(SystemLog.id).label('count')
    ).filter(
        SystemLog.created_at >= seven_days_ago
    ).group_by(
        SystemLog.module
    ).order_by(
        db.func.count(SystemLog.id).desc()
    ).all()
    
    # 按操作类型统计
    action_stats = db.session.query(
        SystemLog.action,
        db.func.count(SystemLog.id).label('count')
    ).filter(
        SystemLog.created_at >= seven_days_ago
    ).group_by(
        SystemLog.action
    ).order_by(
        db.func.count(SystemLog.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'daily_stats': [
                {'date': str(stat.date), 'count': stat.count}
                for stat in daily_stats
            ],
            'user_stats': [
                {'username': stat.username, 'count': stat.count}
                for stat in user_stats
            ],
            'module_stats': [
                {'module': stat.module, 'count': stat.count}
                for stat in module_stats
            ],
            'action_stats': [
                {'action': stat.action, 'count': stat.count}
                for stat in action_stats
            ]
        }
    })


@logs_bp.route('/api/users')
@login_required
@permission_required('system', 'read')
def get_log_users():
    """获取有日志的用户列表"""
    users = db.session.query(User).join(SystemLog).distinct().all()
    
    users_data = [
        {'id': user.id, 'username': user.username, 'email': user.email}
        for user in users
    ]
    
    return jsonify({
        'status': 'success',
        'data': users_data
    })


@logs_bp.route('/export')
@login_required
@permission_required('system', 'write')
def export_logs():
    """导出日志"""
    # 获取筛选参数
    user_id = request.args.get('user_id', type=int)
    module = request.args.get('module', type=str)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    
    # 构建查询
    query = SystemLog.query
    
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    
    if module:
        query = query.filter(SystemLog.module == module)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(SystemLog.created_at >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(SystemLog.created_at < end)
        except:
            pass
    
    # 排序
    query = query.order_by(SystemLog.created_at.desc())
    
    # 获取所有数据
    logs = query.all()
    
    # 转换为 DataFrame
    data = []
    for log in logs:
        data.append({
            '时间': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
            '用户': log.username,
            '模块': log.module,
            '操作': log.action,
            'IP 地址': log.ip_address,
            '请求方法': log.request_method,
            '请求 URL': log.request_url,
            '状态': log.status,
            '错误信息': log.error_message or ''
        })
    
    df = pd.DataFrame(data)
    
    # 导出为 Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='操作日志')
    
    output.seek(0)
    
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'operation_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )
