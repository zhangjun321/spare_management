"""
仪表盘模块
显示系统概览和统计信息
"""

from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.spare_part import SparePart
from app.models.equipment import Equipment
from app.models.maintenance import MaintenanceOrder
from app.models.transaction import Transaction
from datetime import datetime, timedelta
from app.extensions import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')


@dashboard_bp.route('/')
@dashboard_bp.route('/home')
@login_required
def index():
    """仪表盘首页"""
    # 统计信息
    stats = get_dashboard_stats()
    
    # 最近交易
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    
    # 待处理维修工单
    pending_maintenance = MaintenanceOrder.query.filter(
        MaintenanceOrder.status.in_(['created', 'assigned'])
    ).order_by(MaintenanceOrder.created_at.desc()).limit(5).all()
    
    # 库存预警（包括低库存和缺货）
    low_stock_parts = SparePart.query.filter(
        SparePart.stock_status.in_(['low', 'out'])
    ).limit(5).all()
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        recent_transactions=recent_transactions,
        pending_maintenance=pending_maintenance,
        low_stock_parts=low_stock_parts
    )


def get_dashboard_stats():
    """获取仪表盘统计数据"""
    # 查询备件种类和总库存
    spare_parts_query = db.session.query(
        func.count(SparePart.id).label('count'),
        func.coalesce(func.sum(SparePart.current_stock), 0).label('total_stock')
    ).all()
    
    stats = {
        'spare_parts_count': spare_parts_query[0].count,
        'spare_parts_total_stock': spare_parts_query[0].total_stock,
        'equipment_count': Equipment.query.count(),
        'pending_maintenance_count': MaintenanceOrder.query.filter(
            MaintenanceOrder.status.in_(['created', 'assigned'])
        ).count(),
        'today_transactions_count': Transaction.query.filter(
            func.date(Transaction.created_at) == datetime.today().date()
        ).count()
    }
    
    # 库存状态统计
    stats['stock_status'] = {
        'normal': SparePart.query.filter_by(stock_status='normal').count(),
        'low': SparePart.query.filter_by(stock_status='low').count(),
        'out': SparePart.query.filter_by(stock_status='out').count(),
        'overstocked': SparePart.query.filter_by(stock_status='overstocked').count()
    }
    
    return stats


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """获取统计数据 API"""
    stats = get_dashboard_stats()
    return jsonify(stats)


@dashboard_bp.route('/privacy-policy')
def privacy_policy():
    """隐私政策页面"""
    return render_template('dashboard/privacy_policy.html')


@dashboard_bp.route('/terms-of-service')
def terms_of_service():
    """服务条款页面"""
    return render_template('dashboard/terms_of_service.html')


@dashboard_bp.route('/help-center')
def help_center():
    """帮助中心页面"""
    return render_template('dashboard/help_center.html')
