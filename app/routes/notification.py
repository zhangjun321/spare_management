"""
通知模块路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.system import Notification
from app.extensions import db
from datetime import datetime

notification_bp = Blueprint('notification', __name__, template_folder='../templates/notification')


@notification_bp.route('/')
@login_required
def index():
    """通知列表"""
    # 获取通知类型筛选
    notification_type = request.args.get('type', 'all')
    
    # 查询通知
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if notification_type != 'all':
        query = query.filter_by(type=notification_type)
    
    # 按创建时间倒序
    notifications = query.order_by(Notification.created_at.desc()).all()
    
    # 统计未读数量
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    return render_template('notification/list.html', 
                         notifications=notifications, 
                         unread_count=unread_count,
                         current_type=notification_type)


@notification_bp.route('/mark-as-read/<int:id>', methods=['POST'])
@login_required
def mark_as_read(id):
    """标记通知为已读"""
    notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    notification.read_at = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已标记为已读'})


@notification_bp.route('/mark-all-as-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """标记所有通知为已读"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({
        'is_read': True,
        'read_at': datetime.now()
    })
    db.session.commit()
    
    flash('所有通知已标记为已读', 'success')
    return redirect(url_for('notification.index'))


@notification_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """删除通知"""
    notification = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(notification)
    db.session.commit()
    
    flash('通知已删除', 'success')
    return redirect(url_for('notification.index'))


@notification_bp.route('/api/unread-count')
@login_required
def unread_count():
    """获取未读通知数量"""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@notification_bp.route('/api/recent')
@login_required
def get_recent():
    """获取最近的通知（用于顶部导航栏下拉菜单）"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                      .order_by(Notification.created_at.desc())\
                                      .limit(5).all()
    
    result = []
    for n in notifications:
        result.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'level': n.level,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'notifications': result})
