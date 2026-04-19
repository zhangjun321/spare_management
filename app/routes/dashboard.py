"""
仪表盘模块
显示系统概览和统计信息
"""

from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app.models.spare_part import SparePart
from app.models.equipment import Equipment
from app.models.maintenance import MaintenanceOrder
from app.models.transaction import Transaction
from app.models.warehouse import Warehouse
from datetime import datetime, timedelta
from app.extensions import db
from sqlalchemy import func, case
from app.services.dashboard_ai_service import get_dashboard_ai_service
from app.services.kpi_service import get_kpi_service

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
        MaintenanceOrder.status.in_(['created', 'assigned', 'pending'])
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
            MaintenanceOrder.status.in_(['created', 'assigned', 'pending'])
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


@dashboard_bp.route('/api/transaction-trend')
@login_required
def api_transaction_trend():
    """获取出入库趋势数据 API"""
    today = datetime.today().date()
    start_date = today - timedelta(days=29)
    
    # 按日期统计出入库数量
    results = db.session.query(
        func.date(Transaction.created_at).label('date'),
        func.sum(case((Transaction.tx_type == 'inbound', Transaction.total_qty), else_=0)).label('inbound'),
        func.sum(case((Transaction.tx_type == 'outbound', Transaction.total_qty), else_=0)).label('outbound')
    ).filter(
        func.date(Transaction.created_at) >= start_date
    ).group_by(
        func.date(Transaction.created_at)
    ).order_by(
        func.date(Transaction.created_at)
    ).all()
    
    # 构建完整日期范围的数据
    date_range = []
    inbound_data = []
    outbound_data = []
    
    current_date = start_date
    while current_date <= today:
        date_str = current_date.strftime('%m-%d')
        date_range.append(date_str)
        
        # 查找对应日期的数据
        day_data = next((r for r in results if r.date == current_date), None)
        inbound_data.append(float(day_data.inbound) if day_data and day_data.inbound else 0)
        outbound_data.append(float(day_data.outbound) if day_data and day_data.outbound else 0)
        
        current_date += timedelta(days=1)
    
    return jsonify({
        'labels': date_range,
        'inbound': inbound_data,
        'outbound': outbound_data
    })


@dashboard_bp.route('/api/maintenance-status')
@login_required
def api_maintenance_status():
    """获取维修工单状态分布 API"""
    # 按状态统计工单数量
    results = db.session.query(
        MaintenanceOrder.status,
        func.count(MaintenanceOrder.id).label('count')
    ).group_by(
        MaintenanceOrder.status
    ).all()
    
    status_map = {
        'created': '待处理',
        'assigned': '已指派',
        'pending': '进行中',
        'in_progress': '进行中',
        'completed': '已完成',
        'cancelled': '已取消'
    }
    
    status_count = {
        '待处理': 0,
        '进行中': 0,
        '已完成': 0,
        '已取消': 0
    }
    
    for r in results:
        display_name = status_map.get(r.status, '其他')
        if display_name in status_count:
            status_count[display_name] += r.count
        else:
            status_count['其他'] = status_count.get('其他', 0) + r.count
    
    labels = list(status_count.keys())
    data = list(status_count.values())
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@dashboard_bp.route('/api/spare-part-value')
@login_required
def api_spare_part_value():
    """获取备件分类库存价值 API"""
    from app.models.category import Category
    
    # 按分类统计库存价值（使用 current_stock * unit_price 计算）
    results = db.session.query(
        Category.name.label('category_name'),
        func.count(SparePart.id).label('count'),
        func.coalesce(func.sum(SparePart.current_stock), 0).label('total_stock'),
        func.coalesce(func.sum(SparePart.current_stock * SparePart.unit_price), 0).label('total_value')
    ).join(
        Category, SparePart.category_id == Category.id
    ).filter(
        SparePart.category_id.isnot(None)
    ).group_by(
        Category.id, Category.name
    ).order_by(
        func.sum(SparePart.current_stock * SparePart.unit_price).desc()
    ).limit(10).all()
    
    labels = []
    data = []
    
    for r in results:
        labels.append(r.category_name or '未分类')
        # 使用实际的单价计算价值，如果没有单价则使用100元估算
        estimated_value = float(r.total_value) if r.total_value else float(r.total_stock) * 100
        data.append(estimated_value)
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@dashboard_bp.route('/api/equipment-status-trend')
@login_required
def api_equipment_status_trend():
    """获取设备状态趋势 API（简化版，用当前状态模拟过去7天）"""
    today = datetime.today().date()
    labels = []
    
    # 过去7天日期标签
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        labels.append(date.strftime('%m-%d'))
    
    # 获取当前设备状态统计
    running = Equipment.query.filter_by(status='running').count()
    stopped = Equipment.query.filter_by(status='stopped').count()
    maintenance = Equipment.query.filter_by(status='maintenance').count()
    
    # 模拟过去7天的趋势（简单波动）
    running_data = [max(1, running + i % 3 - 1) for i in range(7)]
    stopped_data = [max(1, stopped + (i + 1) % 3 - 1) for i in range(7)]
    maintenance_data = [max(0, maintenance + (i + 2) % 3 - 1) for i in range(7)]
    
    return jsonify({
        'labels': labels,
        'running': running_data,
        'stopped': stopped_data,
        'maintenance': maintenance_data
    })


@dashboard_bp.route('/api/warehouse-utilization')
@login_required
def api_warehouse_utilization():
    """获取仓库利用率 API"""
    warehouses = Warehouse.query.all()
    
    labels = []
    data = []
    
    for wh in warehouses:
        labels.append(wh.name or f'仓库{wh.id}')
        # 模拟利用率：随机生成 50%-95%
        import random
        utilization = random.randint(50, 95)
        data.append(utilization)
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@dashboard_bp.route('/api/stock-status')
@login_required
def api_stock_status():
    """获取库存状态分布 API"""
    stats = get_dashboard_stats()
    
    status_map = {
        'normal': '正常库存',
        'low': '低库存',
        'out': '缺货',
        'overstocked': '超储'
    }
    
    labels = []
    data = []
    
    for key, name in status_map.items():
        if stats['stock_status'][key] > 0:
            labels.append(name)
            data.append(stats['stock_status'][key])
    
    return jsonify({
        'labels': labels,
        'data': data
    })


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


# ==================== AI洞察API ====================

@dashboard_bp.route('/api/ai/insights')
@login_required
def api_ai_insights():
    """获取综合智能洞察"""
    try:
        ai_service = get_dashboard_ai_service()
        insights = ai_service.get_intelligent_insights()
        return jsonify({
            'success': True,
            'data': insights
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/ai/health-score')
@login_required
def api_ai_health_score():
    """获取库存健康评分"""
    try:
        ai_service = get_dashboard_ai_service()
        result = ai_service.get_inventory_health_score()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/ai/anomalies')
@login_required
def api_ai_anomalies():
    """获取异常检测报告"""
    try:
        ai_service = get_dashboard_ai_service()
        result = ai_service.get_anomaly_report()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/ai/refresh-analysis', methods=['POST'])
@login_required
def api_ai_refresh_analysis():
    """刷新分析结果"""
    try:
        ai_service = get_dashboard_ai_service()
        result = ai_service.refresh_analysis()
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== KPI管理API ====================

@dashboard_bp.route('/api/kpi/config')
@login_required
def api_kpi_config_list():
    """获取KPI配置列表"""
    try:
        kpi_service = get_kpi_service()
        kpis = kpi_service.get_active_kpis()
        return jsonify({
            'success': True,
            'data': [kpi.to_dict() for kpi in kpis]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/kpi/summary')
@login_required
def api_kpi_summary():
    """获取KPI汇总数据"""
    try:
        kpi_service = get_kpi_service()
        period = request.args.get('period', 'daily')
        summary = kpi_service.get_kpi_summary(period)
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/kpi/history')
@login_required
def api_kpi_history():
    """获取KPI历史数据"""
    try:
        kpi_service = get_kpi_service()
        kpi_id = request.args.get('kpi_id', type=int)
        days = request.args.get('days', 30, type=int)

        if kpi_id:
            history = kpi_service.get_kpi_history(kpi_id, days)
            return jsonify({
                'success': True,
                'data': history
            })
        else:
            return jsonify({
                'success': False,
                'error': '缺少kpi_id参数'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/kpi/leaderboard')
@login_required
def api_kpi_leaderboard():
    """获取排行榜数据"""
    try:
        kpi_service = get_kpi_service()
        leaderboard_type = request.args.get('type', 'equipment')
        data = kpi_service.get_leaderboard(leaderboard_type)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/kpi/record-snapshot', methods=['POST'])
@login_required
def api_kpi_record_snapshot():
    """记录KPI快照"""
    try:
        kpi_service = get_kpi_service()
        success = kpi_service.record_kpi_snapshot()
        return jsonify({
            'success': success,
            'message': '快照记录成功' if success else '快照记录失败'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 仪表盘数据API ====================

@dashboard_bp.route('/api/dashboard/all-data')
@login_required
def api_dashboard_all_data():
    """获取仪表盘所有数据（一次性获取）"""
    try:
        # 获取基础统计
        stats = get_dashboard_stats()

        # 获取KPI数据
        kpi_service = get_kpi_service()
        kpi_summary = kpi_service.get_kpi_summary('daily')

        # 获取AI洞察（简化版本）
        ai_service = get_dashboard_ai_service()
        health_score = ai_service.get_inventory_health_score()

        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'kpi_summary': kpi_summary,
                'health_score': health_score
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



