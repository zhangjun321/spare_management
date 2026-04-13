"""
库存事务日志 API 路由
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.warehouse_v3.inventory_transaction_log import InventoryTransactionLog, InventoryTransactionSummary
from app.services.warehouse_v3.inventory_transaction_log_service import InventoryTransactionLogService
from app import db

inventory_transaction_log_bp = Blueprint('inventory_transaction_log', __name__, url_prefix='/api/inventory-transaction-log')


@inventory_transaction_log_bp.route('', methods=['GET'])
@login_required
def get_transaction_logs():
    """获取库存事务日志列表"""
    try:
        # 获取查询参数
        inventory_id = request.args.get('inventory_id', type=int)
        part_id = request.args.get('part_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        source_type = request.args.get('source_type')
        source_id = request.args.get('source_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 转换日期
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 查询日志
        result = InventoryTransactionLogService.get_transaction_logs(
            inventory_id=inventory_id,
            part_id=part_id,
            warehouse_id=warehouse_id,
            source_type=source_type,
            source_id=source_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_transaction_log_bp.route('/inventory/<int:inventory_id>', methods=['GET'])
@login_required
def get_inventory_trace(inventory_id):
    """获取特定库存的完整追溯链"""
    try:
        logs = InventoryTransactionLogService.get_inventory_trace(inventory_id)
        
        return jsonify({
            'success': True,
            'data': {
                'inventory_id': inventory_id,
                'logs': logs
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_transaction_log_bp.route('/part/<int:part_id>', methods=['GET'])
@login_required
def get_part_trace(part_id):
    """获取备件的库存变动追溯"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        logs = InventoryTransactionLogService.get_part_trace(
            part_id=part_id,
            warehouse_id=warehouse_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'data': {
                'part_id': part_id,
                'logs': logs
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_transaction_log_bp.route('/summary/daily', methods=['GET'])
@login_required
def get_daily_summary():
    """获取每日库存变动汇总"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        part_id = request.args.get('part_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            # 默认查询最近 30 天
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        summaries = []
        current_date = start_date
        while current_date <= end_date:
            if warehouse_id and part_id:
                summary = InventoryTransactionLogService.generate_daily_summary(
                    warehouse_id, part_id, current_date
                )
                summaries.append(summary.to_dict())
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'data': {
                'summaries': summaries
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_transaction_log_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取库存变动统计"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        part_id = request.args.get('part_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = datetime.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 查询统计
        query = InventoryTransactionLog.query.filter(
            InventoryTransactionLog.operation_time >= datetime.combine(start_date, datetime.min.time()),
            InventoryTransactionLog.operation_time <= datetime.combine(end_date, datetime.max.time())
        )
        
        if warehouse_id:
            query = query.filter(InventoryTransactionLog.warehouse_id == warehouse_id)
        if part_id:
            query = query.filter(InventoryTransactionLog.part_id == part_id)
        
        logs = query.all()
        
        # 统计
        stats = {
            'total_transactions': len(logs),
            'total_in': sum(log.change_quantity for log in logs if log.change_type == 'IN'),
            'total_out': sum(log.change_quantity for log in logs if log.change_type == 'OUT'),
            'total_adjust_in': sum(log.change_quantity for log in logs if log.change_type == 'ADJUST_IN'),
            'total_adjust_out': sum(log.change_quantity for log in logs if log.change_type == 'ADJUST_OUT'),
            'by_change_type': {},
            'by_source_type': {}
        }
        
        # 按变动类型统计
        for log in logs:
            if log.change_type not in stats['by_change_type']:
                stats['by_change_type'][log.change_type] = {
                    'count': 0,
                    'quantity': 0
                }
            stats['by_change_type'][log.change_type]['count'] += 1
            stats['by_change_type'][log.change_type]['quantity'] += float(log.change_quantity)
        
        # 按单据类型统计
        for log in logs:
            if log.source_type:
                if log.source_type not in stats['by_source_type']:
                    stats['by_source_type'][log.source_type] = {
                        'count': 0,
                        'quantity': 0
                    }
                stats['by_source_type'][log.source_type]['count'] += 1
                stats['by_source_type'][log.source_type]['quantity'] += float(log.change_quantity)
        
        # 转换数值类型
        for key in ['total_in', 'total_out', 'total_adjust_in', 'total_adjust_out']:
            stats[key] = float(stats[key])
        
        return jsonify({
            'success': True,
            'data': {
                'statistics': stats,
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
