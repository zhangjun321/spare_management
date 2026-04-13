from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.batch_genealogy_service import BatchGenealogyService, BatchTraceService
from app.models.warehouse_v3.batch_genealogy import BatchGenealogy, BatchTrace
from app.models.warehouse_v3.inventory import InventoryV3
from datetime import datetime

batch_genealogy_bp = Blueprint('batch_genealogy', __name__, url_prefix='/api/batch-genealogy')


# ==================== 批次谱系 API ====================

@batch_genealogy_bp.route('/split', methods=['POST'])
def create_split():
    """创建批次拆分谱系"""
    data = request.get_json()
    
    parent_batch_id = data.get('parent_batch_id')
    child_batch_ids = data.get('child_batch_ids', [])
    quantities = data.get('quantities', [])
    operation_type = data.get('operation_type')
    operation_id = data.get('operation_id')
    remark = data.get('remark')
    
    if not parent_batch_id or not child_batch_ids:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    try:
        genealogies = BatchGenealogyService.create_split_genealogy(
            parent_batch_id=parent_batch_id,
            child_batch_ids=child_batch_ids,
            quantities=quantities,
            operation_type=operation_type,
            operation_id=operation_id,
            remark=remark
        )
        
        return jsonify({
            'success': True,
            'message': '批次拆分谱系创建成功',
            'data': [g.to_dict() for g in genealogies]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@batch_genealogy_bp.route('/merge', methods=['POST'])
def create_merge():
    """创建批次合并谱系"""
    data = request.get_json()
    
    parent_batch_id = data.get('parent_batch_id')
    child_batch_ids = data.get('child_batch_ids', [])
    quantities = data.get('quantities', [])
    operation_type = data.get('operation_type')
    operation_id = data.get('operation_id')
    remark = data.get('remark')
    
    if not parent_batch_id or not child_batch_ids:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    try:
        genealogies = BatchGenealogyService.create_merge_genealogy(
            parent_batch_id=parent_batch_id,
            child_batch_ids=child_batch_ids,
            quantities=quantities,
            operation_type=operation_type,
            operation_id=operation_id,
            remark=remark
        )
        
        return jsonify({
            'success': True,
            'message': '批次合并谱系创建成功',
            'data': [g.to_dict() for g in genealogies]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@batch_genealogy_bp.route('/trace/<int:inventory_id>', methods=['GET'])
def get_batch_trace(inventory_id):
    """获取批次完整追溯链"""
    direction = request.args.get('direction', 'both')  # up, down, both
    depth = request.args.get('depth', 10, type=int)
    
    result = BatchGenealogyService.get_batch_genealogy(inventory_id, direction, depth)
    
    return jsonify({
        'success': True,
        'data': result
    })


@batch_genealogy_bp.route('/full-trace/<int:inventory_id>', methods=['GET'])
def get_full_trace(inventory_id):
    """获取批次完整追溯信息（包含谱系和流转记录）"""
    result = BatchGenealogyService.get_batch_full_trace(inventory_id)
    
    if not result:
        return jsonify({'success': False, 'message': '批次不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': result
    })


# ==================== 批次追溯查询 API ====================

@batch_genealogy_bp.route('/part-trace/<int:part_id>', methods=['GET'])
def get_part_trace(part_id):
    """获取备件批次追溯记录"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    traces = BatchTraceService.get_part_trace(part_id, warehouse_id, start_date, end_date)
    
    return jsonify({
        'success': True,
        'data': traces
    })


@batch_genealogy_bp.route('/batch-trace/<batch_no>', methods=['GET'])
def get_batch_trace_by_no(batch_no):
    """根据批次号获取追溯记录"""
    traces = BatchTraceService.get_batch_trace_by_batch_no(batch_no)
    
    return jsonify({
        'success': True,
        'data': traces
    })


@batch_genealogy_bp.route('/inventory-trace/<int:inventory_id>', methods=['GET'])
def get_inventory_trace(inventory_id):
    """获取库存批次完整追溯链"""
    traces = BatchTraceService.get_inventory_trace(inventory_id)
    
    return jsonify({
        'success': True,
        'data': traces
    })


# ==================== 追溯统计 API ====================

@batch_genealogy_bp.route('/statistics', methods=['GET'])
def get_trace_statistics():
    """获取追溯统计信息"""
    part_id = request.args.get('part_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = BatchTrace.query
    
    if part_id:
        query = query.filter_by(part_id=part_id)
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(BatchTrace.operation_time >= start_date)
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(BatchTrace.operation_time <= end_date)
    
    # 统计不同类型操作数量
    total_count = query.count()
    inbound_count = query.filter_by(trace_type='INBOUND').count()
    outbound_count = query.filter_by(trace_type='OUTBOUND').count()
    transfer_count = query.filter_by(trace_type='TRANSFER').count()
    adjust_count = query.filter_by(trace_type='ADJUST').count()
    
    return jsonify({
        'success': True,
        'data': {
            'total_count': total_count,
            'inbound_count': inbound_count,
            'outbound_count': outbound_count,
            'transfer_count': transfer_count,
            'adjust_count': adjust_count
        }
    })
