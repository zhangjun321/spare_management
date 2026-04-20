"""
仪表盘模块
显示系统概览和统计信息
"""

from flask import Blueprint, render_template, redirect, url_for, jsonify, request, make_response
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
import functools
import hashlib

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')

# ==================== 缓存机制 ====================
_cache_store = {}

def cache_response(seconds=30):
    """缓存装饰器"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{f.__name__}:{hashlib.md5(str(request.args).encode()).hexdigest()}"
            
            # 检查缓存
            if cache_key in _cache_store:
                cached_data, expiry = _cache_store[cache_key]
                if datetime.now() < expiry:
                    return cached_data
            
            # 执行函数
            result = f(*args, **kwargs)
            
            # 缓存结果
            _cache_store[cache_key] = (result, datetime.now() + timedelta(seconds=seconds))
            
            # 清理过期缓存
            _clean_expired_cache()
            
            return result
        return decorated_function
    return decorator

def _clean_expired_cache():
    """清理过期缓存"""
    global _cache_store
    now = datetime.now()
    keys_to_delete = [k for k, (_, expiry) in _cache_store.items() if now >= expiry]
    for k in keys_to_delete:
        del _cache_store[k]


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
    """获取仪表盘统计数据（优化版）"""
    # 一次性查询所有统计数据
    stats = {}
    
    # 备件统计（一次性查询）
    spare_stats = db.session.query(
        func.count(SparePart.id).label('total_count'),
        func.coalesce(func.sum(SparePart.current_stock), 0).label('total_stock'),
        func.count(case((SparePart.stock_status == 'normal', 1))).label('normal'),
        func.count(case((SparePart.stock_status == 'low', 1))).label('low'),
        func.count(case((SparePart.stock_status == 'out', 1))).label('out'),
        func.count(case((SparePart.stock_status == 'overstocked', 1))).label('overstocked')
    ).first()
    
    stats['spare_parts_count'] = spare_stats.total_count
    stats['spare_parts_total_stock'] = spare_stats.total_stock
    
    # 设备统计
    stats['equipment_count'] = Equipment.query.count()
    
    # 待处理维修工单统计
    stats['pending_maintenance_count'] = MaintenanceOrder.query.filter(
        MaintenanceOrder.status.in_(['created', 'assigned', 'pending'])
    ).count()
    
    # 今日交易统计（使用索引优化）
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    stats['today_transactions_count'] = Transaction.query.filter(
        Transaction.created_at >= today,
        Transaction.created_at < tomorrow
    ).count()
    
    # 库存状态统计
    stats['stock_status'] = {
        'normal': spare_stats.normal,
        'low': spare_stats.low,
        'out': spare_stats.out,
        'overstocked': spare_stats.overstocked
    }
    
    return stats


@dashboard_bp.route('/api/stats')
@login_required
@cache_response(seconds=30)
def api_stats():
    """获取统计数据 API"""
    stats = get_dashboard_stats()
    return jsonify(stats)


@dashboard_bp.route('/api/transaction-trend')
@login_required
@cache_response(seconds=60)
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
@cache_response(seconds=60)
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
@cache_response(seconds=120)
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


# ==================== 增强的仪表盘分析API ====================

@dashboard_bp.route('/api/analysis/inventory-turnover')
@login_required
def api_inventory_turnover():
    """获取库存周转率分析"""
    try:
        from datetime import datetime, timedelta
        
        period = request.args.get('period', '30')
        period_days = int(period)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # 计算出库总量
        outbound_total = db.session.query(
            func.sum(Transaction.total_qty)
        ).filter(
            Transaction.tx_type == 'outbound',
            Transaction.created_at >= start_date
        ).scalar() or 0
        
        # 计算平均库存
        total_parts = SparePart.query.count()
        avg_stock = db.session.query(
            func.avg(SparePart.current_stock)
        ).scalar() or 0
        
        turnover_rate = round(float(outbound_total) / (avg_stock * total_parts) * 100, 2) if avg_stock > 0 and total_parts > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'period_days': period_days,
                'outbound_total': float(outbound_total),
                'avg_stock': float(avg_stock),
                'turnover_rate': turnover_rate,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/analysis/equipment-oee')
@login_required
def api_equipment_oee():
    """获取设备OEE（整体设备效率）分析"""
    try:
        total_equipment = Equipment.query.count()
        running_equipment = Equipment.query.filter_by(status='running').count()
        maintenance_equipment = Equipment.query.filter_by(status='maintenance').count()
        
        # 计算可用性
        availability = round((running_equipment / total_equipment * 100), 2) if total_equipment > 0 else 0
        
        # 获取近期工单完成情况
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        total_orders = MaintenanceOrder.query.filter(
            MaintenanceOrder.created_at >= start_date
        ).count()
        completed_orders = MaintenanceOrder.query.filter(
            MaintenanceOrder.status == 'completed',
            MaintenanceOrder.created_at >= start_date
        ).count()
        
        performance = round((completed_orders / total_orders * 100), 2) if total_orders > 0 else 0
        
        # 计算OEE (简化版本)
        oee = round((availability * performance) / 100, 2)
        
        return jsonify({
            'success': True,
            'data': {
                'total_equipment': total_equipment,
                'running_equipment': running_equipment,
                'maintenance_equipment': maintenance_equipment,
                'availability': availability,
                'performance': performance,
                'oee': oee,
                'quality_rate': 98.5  # 模拟质量率
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/analysis/stock-age')
@login_required
def api_stock_age():
    """获取库龄分析"""
    try:
        from app.models.batch import Batch
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # 统计不同库龄区间的备件数量
        age_ranges = {
            '0_30': {'label': '0-30天', 'count': 0, 'value': 0},
            '30_90': {'label': '30-90天', 'count': 0, 'value': 0},
            '90_180': {'label': '90-180天', 'count': 0, 'value': 0},
            '180_365': {'label': '180-365天', 'count': 0, 'value': 0},
            'over_365': {'label': '超过1年', 'count': 0, 'value': 0}
        }
        
        batches = Batch.query.all()
        
        for batch in batches:
            if batch.production_date:
                age_days = (now.date() - batch.production_date).days
                value = float(batch.quantity or 0) * float(batch.unit_price or 0)
                
                if age_days <= 30:
                    age_ranges['0_30']['count'] += 1
                    age_ranges['0_30']['value'] += value
                elif age_days <= 90:
                    age_ranges['30_90']['count'] += 1
                    age_ranges['30_90']['value'] += value
                elif age_days <= 180:
                    age_ranges['90_180']['count'] += 1
                    age_ranges['90_180']['value'] += value
                elif age_days <= 365:
                    age_ranges['180_365']['count'] += 1
                    age_ranges['180_365']['value'] += value
                else:
                    age_ranges['over_365']['count'] += 1
                    age_ranges['over_365']['value'] += value
        
        return jsonify({
            'success': True,
            'data': age_ranges
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/alerts/active')
@login_required
def api_active_alerts():
    """获取活跃告警列表"""
    try:
        from app.models.system import Alert
        
        alerts = Alert.query.filter_by(status='active').order_by(Alert.created_at.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': alert.id,
                'type': alert.alert_type,
                'title': alert.title,
                'message': alert.message,
                'level': alert.level,
                'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M:%S') if alert.created_at else None
            } for alert in alerts]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/export/dashboard-data')
@login_required
def api_export_dashboard_data():
    """导出仪表盘数据"""
    try:
        stats = get_dashboard_stats()
        
        export_data = {
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'spare_parts_count': stats['spare_parts_count'],
                'equipment_count': stats['equipment_count'],
                'pending_maintenance_count': stats['pending_maintenance_count'],
                'today_transactions_count': stats['today_transactions_count']
            },
            'stock_status': stats['stock_status']
        }
        
        return jsonify({
            'success': True,
            'data': export_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/trend/comparison')
@login_required
def api_trend_comparison():
    """获取同比环比趋势对比"""
    try:
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # 本期（最近30天）
        current_end = now
        current_start = current_end - timedelta(days=30)
        
        # 上期（前30天）
        prev_end = current_start
        prev_start = prev_end - timedelta(days=30)
        
        # 去年同期
        last_year_start = current_start.replace(year=current_start.year - 1)
        last_year_end = current_end.replace(year=current_end.year - 1)
        
        def get_stats(start_date, end_date):
            inbound = db.session.query(
                func.sum(Transaction.total_qty)
            ).filter(
                Transaction.tx_type == 'inbound',
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            ).scalar() or 0
            
            outbound = db.session.query(
                func.sum(Transaction.total_qty)
            ).filter(
                Transaction.tx_type == 'outbound',
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            ).scalar() or 0
            
            orders = MaintenanceOrder.query.filter(
                MaintenanceOrder.created_at >= start_date,
                MaintenanceOrder.created_at <= end_date
            ).count()
            
            return {
                'inbound': float(inbound),
                'outbound': float(outbound),
                'orders': orders
            }
        
        current_stats = get_stats(current_start, current_end)
        prev_stats = get_stats(prev_start, prev_end)
        last_year_stats = get_stats(last_year_start, last_year_end)
        
        def calc_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 2)
        
        return jsonify({
            'success': True,
            'data': {
                'current': current_stats,
                'previous': prev_stats,
                'last_year': last_year_stats,
                'mom_change': {  # 环比
                    'inbound': calc_change(current_stats['inbound'], prev_stats['inbound']),
                    'outbound': calc_change(current_stats['outbound'], prev_stats['outbound']),
                    'orders': calc_change(current_stats['orders'], prev_stats['orders'])
                },
                'yoy_change': {  # 同比
                    'inbound': calc_change(current_stats['inbound'], last_year_stats['inbound']),
                    'outbound': calc_change(current_stats['outbound'], last_year_stats['outbound']),
                    'orders': calc_change(current_stats['orders'], last_year_stats['orders'])
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 新的AI分析API ====================

@dashboard_bp.route('/api/ai/demand-forecast')
@login_required
def api_demand_forecast():
    """获取需求预测"""
    try:
        ai_service = get_dashboard_ai_service()
        result = ai_service.get_demand_forecast()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/ai/abc-analysis')
@login_required
def api_abc_analysis():
    """获取ABC分类分析"""
    try:
        ai_service = get_dashboard_ai_service()
        result = ai_service.get_abc_analysis()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/ai/performance-insights')
@login_required
def api_performance_insights():
    """获取综合绩效洞察"""
    try:
        ai_service = get_dashboard_ai_service()
        result = ai_service.get_performance_insights()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



