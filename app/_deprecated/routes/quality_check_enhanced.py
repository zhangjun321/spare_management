"""
质检管理 API 路由 - 增强版
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.warehouse_v3 import QualityCheck, QualityCheckItem, QualityCheckStandard
from app.models.warehouse_v3.inbound import InboundOrderV3, InboundOrderItemV3
from app.utils.concurrency import with_transaction, with_retry
from datetime import datetime
import json

quality_check_bp = Blueprint('quality_check', __name__, url_prefix='/api/quality-check')


@quality_check_bp.route('/checks', methods=['GET'])
@login_required
def get_quality_checks():
    """获取质检单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', type=str)
        check_type = request.args.get('check_type', type=str)
        
        query = QualityCheck.query.order_by(QualityCheck.created_at.desc())
        
        if status:
            query = query.filter(QualityCheck.status == status)
        if check_type:
            query = query.filter(QualityCheck.check_type == check_type)
        
        checks = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'list': [check.to_dict() for check in checks.items],
                'total': checks.total,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks', methods=['POST'])
@login_required
@with_transaction
def create_quality_check():
    """创建质检单"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['inbound_order_id', 'check_type', 'inspection_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400
        
        # 检查入库单是否存在
        inbound_order = InboundOrderV3.query.get(data['inbound_order_id'])
        if not inbound_order:
            return jsonify({
                'success': False,
                'message': '入库单不存在'
            }), 404
        
        # 生成质检单号
        check_no = QualityCheck.generate_check_no()
        
        check = QualityCheck(
            check_no=check_no,
            inbound_order_id=data['inbound_order_id'],
            check_type=data['check_type'],
            inspection_type=data['inspection_type'],
            check_method=data.get('check_method', 'sampling'),
            sample_ratio=data.get('sample_ratio', 0.1),
            status='pending',
            remark=data.get('remark', '')
        )
        
        db.session.add(check)
        db.session.flush()
        
        # 自动创建质检明细（从入库单明细复制）
        inbound_items = InboundOrderItemV3.query.filter_by(inbound_order_id=inbound_order.id).all()
        for item in inbound_items:
            check_item = QualityCheckItem(
                check_id=check.id,
                inbound_item_id=item.id,
                part_id=item.spare_part_id,
                expected_quantity=item.quantity,
                checked_quantity=0,
                qualified_quantity=0,
                unqualified_quantity=0,
                unit=item.unit,
                status='pending'
            )
            db.session.add(check_item)
        
        return jsonify({
            'success': True,
            'message': '质检单创建成功',
            'data': check.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>', methods=['GET'])
@login_required
def get_quality_check(check_id):
    """获取质检单详情"""
    try:
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': check.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/items', methods=['GET'])
@login_required
def get_quality_check_items(check_id):
    """获取质检单明细"""
    try:
        items = QualityCheckItem.query.filter_by(check_id=check_id).all()
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in items]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/items/<int:item_id>', methods=['POST'])
@login_required
@with_transaction
def submit_quality_check_item(check_id, item_id):
    """提交质检结果"""
    try:
        data = request.get_json()
        
        check_item = QualityCheckItem.query.get(item_id)
        if not check_item:
            return jsonify({
                'success': False,
                'message': '质检明细不存在'
            }), 404
        
        if check_item.check_id != check_id:
            return jsonify({
                'success': False,
                'message': '质检明细不属于该质检单'
            }), 404
        
        # 更新质检数据
        check_item.checked_quantity = data.get('checked_quantity', check_item.checked_quantity)
        check_item.qualified_quantity = data.get('qualified_quantity', 0)
        check_item.unqualified_quantity = data.get('unqualified_quantity', 0)
        check_item.defect_type = data.get('defect_type')
        check_item.defect_level = data.get('defect_level')
        check_item.defect_description = data.get('defect_description', '')
        check_item.remark = data.get('remark', '')
        check_item.inspected_at = datetime.utcnow()
        check_item.inspector_id = current_user.id
        check_item.status = 'completed'
        
        db.session.flush()
        
        # 检查是否所有明细都已质检
        check = QualityCheck.query.get(check_id)
        all_items = QualityCheckItem.query.filter_by(check_id=check_id).all()
        all_checked = all(item.checked_quantity > 0 or item.status == 'completed' for item in all_items)
        
        if all_checked:
            # 汇总数据
            total_quantity = sum(item.checked_quantity or 0 for item in all_items)
            qualified_count = sum(item.qualified_quantity or 0 for item in all_items)
            unqualified_count = sum(item.unqualified_quantity or 0 for item in all_items)
            
            check.total_quantity = total_quantity
            check.qualified_count = qualified_count
            check.unqualified_count = unqualified_count
            check.calculate_result()
        
        return jsonify({
            'success': True,
            'message': '质检结果提交成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/start', methods=['POST'])
@login_required
@with_transaction
def start_quality_check(check_id):
    """开始质检"""
    try:
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        if check.status != 'pending':
            return jsonify({
                'success': False,
                'message': '当前状态不能开始质检'
            }), 400
        
        check.status = 'inspecting'
        check.started_at = datetime.utcnow()
        check.started_by = current_user.id
        db.session.flush()
        
        return jsonify({
            'success': True,
            'message': '质检已开始'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/complete', methods=['POST'])
@login_required
@with_transaction
def complete_quality_check(check_id):
    """完成质检"""
    try:
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        # 检查是否所有明细都已质检
        all_items = QualityCheckItem.query.filter_by(check_id=check_id).all()
        all_checked = all(item.checked_quantity > 0 or item.status == 'completed' for item in all_items)
        
        if not all_checked:
            return jsonify({
                'success': False,
                'message': '还有明细未完成质检'
            }), 400
        
        # 汇总数据
        total_quantity = sum(item.checked_quantity or 0 for item in all_items)
        qualified_count = sum(item.qualified_quantity or 0 for item in all_items)
        unqualified_count = sum(item.unqualified_quantity or 0 for item in all_items)
        
        check.total_quantity = total_quantity
        check.qualified_count = qualified_count
        check.unqualified_count = unqualified_count
        check.calculate_result()
        
        check.status = 'completed'
        check.completed_at = datetime.utcnow()
        check.completed_by = current_user.id
        db.session.flush()
        
        return jsonify({
            'success': True,
            'message': '质检已完成',
            'data': check.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/cancel', methods=['POST'])
@login_required
@with_transaction
def cancel_quality_check(check_id):
    """取消质检"""
    try:
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        if check.status not in ['pending', 'inspecting']:
            return jsonify({
                'success': False,
                'message': '当前状态不能取消'
            }), 400
        
        check.status = 'cancelled'
        check.cancelled_at = datetime.utcnow()
        check.cancelled_by = current_user.id
        db.session.flush()
        
        return jsonify({
            'success': True,
            'message': '质检已取消'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/stats', methods=['GET'])
@login_required
def get_quality_stats():
    """获取质检统计信息"""
    try:
        # 按状态统计
        pending_count = QualityCheck.query.filter_by(status='pending').count()
        inspecting_count = QualityCheck.query.filter_by(status='inspecting').count()
        completed_count = QualityCheck.query.filter_by(status='completed').count()
        cancelled_count = QualityCheck.query.filter_by(status='cancelled').count()
        
        # 今日质检数量
        today = datetime.now().date()
        today_count = QualityCheck.query.filter(
            db.func.date(QualityCheck.created_at) == today
        ).count()
        
        # 合格率统计
        all_checks = QualityCheck.query.filter(QualityCheck.status == 'completed').all()
        total_qualified = sum(check.qualified_count or 0 for check in all_checks)
        total_unqualified = sum(check.unqualified_count or 0 for check in all_checks)
        total_checked = total_qualified + total_unqualified
        pass_rate = (total_qualified / total_checked * 100) if total_checked > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'by_status': {
                    'pending': pending_count,
                    'inspecting': inspecting_count,
                    'completed': completed_count,
                    'cancelled': cancelled_count
                },
                'today_count': today_count,
                'pass_rate': round(pass_rate, 2),
                'total_qualified': total_qualified,
                'total_unqualified': total_unqualified
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# 质检标准管理
@quality_check_bp.route('/standards', methods=['GET'])
@login_required
def get_quality_standards():
    """获取质检标准列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        part_code = request.args.get('part_code', type=str)
        is_active = request.args.get('is_active', type=bool)
        
        query = QualityCheckStandard.query.order_by(QualityCheckStandard.created_at.desc())
        
        if part_code:
            query = query.filter(QualityCheckStandard.part_code.like(f'%{part_code}%'))
        if is_active is not None:
            query = query.filter(QualityCheckStandard.is_active == is_active)
        
        standards = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'list': [std.to_dict() for std in standards.items],
                'total': standards.total,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/standards', methods=['POST'])
@login_required
@with_transaction
def create_quality_standard():
    """创建质检标准"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['part_id', 'part_code', 'check_item']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400
        
        # 检查是否已存在相同标准
        existing = QualityCheckStandard.query.filter_by(
            part_id=data['part_id'],
            check_item=data['check_item']
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': '该备件的该检验项目已存在标准'
            }), 400
        
        standard = QualityCheckStandard(
            part_id=data['part_id'],
            part_code=data['part_code'],
            check_item=data['check_item'],
            check_method=data.get('check_method', ''),
            standard_value=data.get('standard_value', ''),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            unit=data.get('unit', ''),
            severity_level=data.get('severity_level', 'normal'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(standard)
        
        return jsonify({
            'success': True,
            'message': '质检标准创建成功',
            'data': standard.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/standards/<int:standard_id>', methods=['PUT'])
@login_required
@with_transaction
def update_quality_standard(standard_id):
    """更新质检标准"""
    try:
        standard = QualityCheckStandard.query.get(standard_id)
        if not standard:
            return jsonify({
                'success': False,
                'message': '质检标准不存在'
            }), 404
        
        data = request.get_json()
        
        if 'check_item' in data:
            standard.check_item = data['check_item']
        if 'check_method' in data:
            standard.check_method = data['check_method']
        if 'standard_value' in data:
            standard.standard_value = data['standard_value']
        if 'min_value' in data:
            standard.min_value = data['min_value']
        if 'max_value' in data:
            standard.max_value = data['max_value']
        if 'unit' in data:
            standard.unit = data['unit']
        if 'severity_level' in data:
            standard.severity_level = data['severity_level']
        if 'is_active' in data:
            standard.is_active = data['is_active']
        
        standard.updated_at = datetime.utcnow()
        
        return jsonify({
            'success': True,
            'message': '质检标准更新成功',
            'data': standard.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/standards/<int:standard_id>', methods=['DELETE'])
@login_required
@with_transaction
def delete_quality_standard(standard_id):
    """删除质检标准"""
    try:
        standard = QualityCheckStandard.query.get(standard_id)
        if not standard:
            return jsonify({
                'success': False,
                'message': '质检标准不存在'
            }), 404
        
        db.session.delete(standard)
        
        return jsonify({
            'success': True,
            'message': '质检标准删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
