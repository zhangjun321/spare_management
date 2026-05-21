"""
新的仓库管理模块路由
包含入库、出库、库存查询等 API
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.inbound_outbound import InboundOrder, OutboundOrder
from app.models.inventory_transaction_log import InventoryTransactionLog
from app.services.inbound_linkage_service import InboundLinkageService
from app.services.outbound_linkage_service import OutboundLinkageService
from app.services.baidu_qianfan_service import get_qianfan_service
from sqlalchemy import and_, or_
from datetime import datetime

# 创建蓝图
warehouse_new_bp = Blueprint('warehouse_new', __name__, url_prefix='/api/warehouse')


# ==================== 入库管理 ====================

@warehouse_new_bp.route('/inbound/create', methods=['POST'])
@login_required
def create_inbound():
    """创建入库单"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['spare_part_id', 'warehouse_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必填字段：{field}'
                }), 400
        
        # 创建入库单
        inbound_order, error = InboundLinkageService.create_inbound_order(data, current_user.id)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': inbound_order.to_dict(),
            'message': '入库单创建成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/inbound/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm_inbound(order_id):
    """确认入库单"""
    try:
        inbound_order, error = InboundLinkageService.confirm_inbound(order_id, current_user.id)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': inbound_order.to_dict(),
            'message': '入库单确认成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/inbound/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_inbound(order_id):
    """完成入库"""
    try:
        data = request.get_json() or {}
        received_quantity = data.get('received_quantity')
        
        inbound_order, inventory_record, error = InboundLinkageService.complete_inbound(
            order_id, received_quantity, current_user.id
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'inbound_order': inbound_order.to_dict(),
                'inventory_record': inventory_record.to_dict() if inventory_record else None
            },
            'message': '入库完成'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/inbound/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_inbound(order_id):
    """取消入库单"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason')
        
        inbound_order, error = InboundLinkageService.cancel_inbound(order_id, current_user.id, reason)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': inbound_order.to_dict(),
            'message': '入库单已取消'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/inbound/list', methods=['GET'])
@login_required
def list_inbound():
    """获取入库单列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        inbound_type = request.args.get('inbound_type')
        status = request.args.get('status')
        spare_part_id = request.args.get('spare_part_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = InboundOrder.query
        
        if inbound_type:
            query = query.filter_by(inbound_type=inbound_type)
        
        if status:
            query = query.filter_by(status=status)
        
        if spare_part_id:
            query = query.filter_by(spare_part_id=spare_part_id)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InboundOrder.created_at >= start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(InboundOrder.created_at <= end)
        
        # 排序
        query = query.order_by(InboundOrder.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'items': [order.to_dict() for order in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 出库管理 ====================

@warehouse_new_bp.route('/outbound/create', methods=['POST'])
@login_required
def create_outbound():
    """创建出库单"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['spare_part_id', 'warehouse_id', 'location_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必填字段：{field}'
                }), 400
        
        # 创建出库单
        outbound_order, error = OutboundLinkageService.create_outbound_order(data, current_user.id)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': outbound_order.to_dict(),
            'message': '出库单创建成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/outbound/<int:order_id>/approve', methods=['POST'])
@login_required
def approve_outbound(order_id):
    """审批出库单"""
    try:
        data = request.get_json() or {}
        remark = data.get('remark')
        
        outbound_order, error = OutboundLinkageService.approve_outbound(order_id, current_user.id, remark)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': outbound_order.to_dict(),
            'message': '出库单审批通过'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/outbound/<int:order_id>/reject', methods=['POST'])
@login_required
def reject_outbound(order_id):
    """拒绝出库单"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason')
        
        outbound_order, error = OutboundLinkageService.reject_outbound(order_id, current_user.id, reason)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': outbound_order.to_dict(),
            'message': '出库单已拒绝'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/outbound/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_outbound(order_id):
    """完成出库"""
    try:
        data = request.get_json() or {}
        shipped_quantity = data.get('shipped_quantity')
        
        outbound_order, inventory_record, error = OutboundLinkageService.complete_outbound(
            order_id, shipped_quantity, current_user.id
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'outbound_order': outbound_order.to_dict(),
                'inventory_record': inventory_record.to_dict() if inventory_record else None
            },
            'message': '出库完成'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/outbound/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_outbound(order_id):
    """取消出库单"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason')
        
        outbound_order, error = OutboundLinkageService.cancel_outbound(order_id, current_user.id, reason)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': outbound_order.to_dict(),
            'message': '出库单已取消'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/outbound/list', methods=['GET'])
@login_required
def list_outbound():
    """获取出库单列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        outbound_type = request.args.get('outbound_type')
        status = request.args.get('status')
        spare_part_id = request.args.get('spare_part_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        department_id = request.args.get('department_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = OutboundOrder.query
        
        if outbound_type:
            query = query.filter_by(outbound_type=outbound_type)
        
        if status:
            query = query.filter_by(status=status)
        
        if spare_part_id:
            query = query.filter_by(spare_part_id=spare_part_id)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if department_id:
            query = query.filter_by(department_id=department_id)
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(OutboundOrder.created_at >= start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(OutboundOrder.created_at <= end)
        
        # 排序
        query = query.order_by(OutboundOrder.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'items': [order.to_dict() for order in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 库存管理 ====================

@warehouse_new_bp.route('/inventory/list', methods=['GET'])
@login_required
def list_inventory():
    """获取库存记录列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        spare_part_id = request.args.get('spare_part_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        location_id = request.args.get('location_id', type=int)
        stock_status = request.args.get('stock_status')
        has_stock = request.args.get('has_stock')  # 只显示有库存的记录
        
        # 构建查询
        query = InventoryRecord.query
        
        if spare_part_id:
            query = query.filter_by(spare_part_id=spare_part_id)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if location_id:
            query = query.filter_by(location_id=location_id)
        
        if stock_status:
            query = query.filter_by(stock_status=stock_status)
        
        if has_stock == 'true':
            query = query.filter(InventoryRecord.quantity > 0)
        
        # 排序
        query = query.order_by(InventoryRecord.updated_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'items': [record.to_dict() for record in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/inventory/detail/<int:record_id>', methods=['GET'])
@login_required
def get_inventory_detail(record_id):
    """获取库存记录详情"""
    try:
        inventory_record = InventoryRecord.query.get(record_id)
        
        if not inventory_record:
            return jsonify({
                'success': False,
                'error': '库存记录不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': inventory_record.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/inventory/stock-distribution', methods=['GET'])
@login_required
def get_stock_distribution():
    """获取备件库存分布（跨仓库查询）"""
    try:
        spare_part_id = request.args.get('spare_part_id', type=int)
        
        if not spare_part_id:
            return jsonify({
                'success': False,
                'error': '请提供备件 ID'
            }), 400
        
        # 查询该备件在所有仓库的库存分布
        records = InventoryRecord.query.filter(
            InventoryRecord.spare_part_id == spare_part_id,
            InventoryRecord.quantity > 0
        ).all()
        
        distribution = []
        total_quantity = 0
        
        for record in records:
            distribution.append({
                'warehouse_id': record.warehouse_id,
                'warehouse_name': record.warehouse.name if record.warehouse else '未知仓库',
                'location_id': record.location_id,
                'location_name': record.warehouse_location.name if record.warehouse_location else '未知货位',
                'quantity': record.quantity,
                'available_quantity': record.available_quantity,
                'stock_status': record.stock_status
            })
            total_quantity += record.quantity
        
        return jsonify({
            'success': True,
            'data': {
                'spare_part_id': spare_part_id,
                'total_quantity': total_quantity,
                'distribution': distribution
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 库存变动日志 ====================

@warehouse_new_bp.route('/transaction-logs/list', methods=['GET'])
@login_required
def list_transaction_logs():
    """获取库存变动日志列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        transaction_type = request.args.get('transaction_type')
        spare_part_id = request.args.get('spare_part_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询
        query = InventoryTransactionLog.query
        
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        if spare_part_id:
            query = query.filter_by(spare_part_id=spare_part_id)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InventoryTransactionLog.created_at >= start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(InventoryTransactionLog.created_at <= end)
        
        # 排序
        query = query.order_by(InventoryTransactionLog.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'items': [log.to_dict() for log in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== AI 功能 ====================

@warehouse_new_bp.route('/ai/analyze-inventory', methods=['POST'])
@login_required
def ai_analyze_inventory():
    """AI 分析库存"""
    try:
        data = request.get_json()
        warehouse_id = data.get('warehouse_id')
        days = data.get('days', 30)
        
        # 获取库存记录
        query = InventoryRecord.query
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        inventory_records = query.all()
        
        # 调用 AI 分析
        qianfan = get_qianfan_service()
        result = qianfan.analyze_inventory_trend(inventory_records, days)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'AI 分析完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 分析失败')
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/ai/predict-demand', methods=['POST'])
@login_required
def ai_predict_demand():
    """AI 预测需求"""
    try:
        data = request.get_json()
        spare_part_id = data.get('spare_part_id')
        days = data.get('days', 30)
        
        # 获取历史数据（简化版）
        # 实际应该从 transaction_logs 获取历史出入库数据
        historical_data = []
        
        # 调用 AI 预测
        qianfan = get_qianfan_service()
        result = qianfan.predict_demand(historical_data, days)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'AI 需求预测完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 预测失败')
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/ai/recommend-location', methods=['POST'])
@login_required
def ai_recommend_location():
    """AI 推荐货位"""
    try:
        data = request.get_json()
        
        part_data = data.get('part_data', {})
        warehouse_id = data.get('warehouse_id')
        
        if not warehouse_id or not part_data:
            return jsonify({
                'success': False,
                'error': '请提供仓库 ID 和备件数据'
            }), 400
        
        # 获取可用货位（简化版）
        warehouse_locations = []
        
        # 调用 AI 推荐
        qianfan = get_qianfan_service()
        result = qianfan.recommend_location(part_data, warehouse_locations)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'AI 货位推荐完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 推荐失败')
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_new_bp.route('/ai/generate-report', methods=['POST'])
@login_required
def ai_generate_report():
    """AI 生成智能报告"""
    try:
        data = request.get_json()
        report_type = data.get('report_type', 'daily')
        
        # 获取报告数据（简化版）
        report_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_inbound': InboundOrder.query.filter(
                InboundOrder.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count(),
            'total_outbound': OutboundOrder.query.filter(
                OutboundOrder.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count(),
            'low_stock_count': InventoryRecord.query.filter_by(stock_status='low').count(),
            'out_of_stock_count': InventoryRecord.query.filter_by(stock_status='out').count()
        }
        
        # 调用 AI 生成报告
        qianfan = get_qianfan_service()
        result = qianfan.generate_intelligent_report(report_type, report_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'AI 报告生成完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 报告生成失败')
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
