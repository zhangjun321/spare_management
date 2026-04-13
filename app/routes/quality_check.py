from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.warehouse_v3 import QualityCheck, QualityCheckItem
from app.models.warehouse_v3.inbound import InboundOrderV3, InboundOrderItemV3
from datetime import datetime
import json

quality_check_bp = Blueprint('quality_check', __name__, url_prefix='/api/quality-check')


@quality_check_bp.route('/checks', methods=['GET'])
@login_required
def get_quality_checks():
    """获取质检单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)  # 增加每页数量，减少请求次数
        
        checks = QualityCheck.query.order_by(QualityCheck.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
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
def create_quality_check():
    """创建质检单"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['inbound_order_id', 'check_type']
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
        check_no = f"QC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        check = QualityCheck(
            check_no=check_no,
            inbound_order_id=data['inbound_order_id'],
            check_type=data['check_type'],
            check_method=data.get('check_method', 'sampling'),
            sample_ratio=data.get('sample_ratio', 0.1),
            status='pending',
            created_by=data.get('created_by'),
            remark=data.get('remark', '')
        )
        
        db.session.add(check)
        db.session.commit()
        
        # 自动创建质检明细（从入库单明细复制）
        inbound_items = InboundOrderItemV3.query.filter_by(inbound_order_id=inbound_order.id).all()
        for item in inbound_items:
            check_item = QualityCheckItem(
                check_id=check.id,
                inbound_item_id=item.id,
                part_name=item.part_name,
                specification=item.specification,
                expected_quantity=item.quantity,
                checked_quantity=0,
                qualified_quantity=0,
                unqualified_quantity=0,
                unit=item.unit
            )
            db.session.add(check_item)
        
        db.session.commit()
        
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
        
        check_dict = check.to_dict()
        # 添加质检项目明细
        items = QualityCheckItem.query.filter_by(check_id=check_id).all()
        check_dict['items'] = [item.to_dict() for item in items]
        
        return jsonify({
            'success': True,
            'data': check_dict
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
        check_item.remark = data.get('remark', '')
        check_item.checked_at = datetime.now()
        check_item.checked_by = data.get('checked_by')
        
        db.session.commit()
        
        # 检查是否所有明细都已质检
        check = QualityCheck.query.get(check_id)
        all_items = QualityCheckItem.query.filter_by(check_id=check_id).all()
        all_checked = all(item.checked_quantity > 0 for item in all_items)
        
        if all_checked:
            check.status = 'completed'
            check.completed_at = datetime.now()
            db.session.commit()
        
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
def start_quality_check(check_id):
    """开始质检"""
    try:
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        check.status = 'inspecting'
        check.started_at = datetime.now()
        check.started_by = request.json.get('started_by')
        db.session.commit()
        
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
        all_checked = all(item.checked_quantity > 0 for item in all_items)
        
        if not all_checked:
            return jsonify({
                'success': False,
                'message': '还有明细未完成质检'
            }), 400
        
        check.status = 'completed'
        check.completed_at = datetime.now()
        check.completed_by = request.json.get('completed_by')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '质检已完成'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/cancel', methods=['POST'])
@login_required
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
        check.cancelled_at = datetime.now()
        check.cancelled_by = request.json.get('cancelled_by')
        db.session.commit()
        
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


@quality_check_bp.route('/checks/<int:check_id>/submit', methods=['POST'])
@login_required
def submit_quality_check(check_id):
    """提交质检结果"""
    try:
        data = request.get_json()
        
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        if check.status != 'inspecting':
            return jsonify({
                'success': False,
                'message': '质检单状态不正确'
            }), 400
        
        items = data.get('items', [])
        for item_data in items:
            check_item = QualityCheckItem.query.get(item_data['id'])
            if check_item and check_item.check_id == check_id:
                check_item.checked_quantity = item_data.get('checked_quantity', 0)
                check_item.qualified_quantity = item_data.get('qualified_quantity', 0)
                check_item.unqualified_quantity = item_data.get('unqualified_quantity', 0)
                check_item.pass_rate = item_data.get('pass_rate', 0)
                check_item.remark = item_data.get('remark', '')
                check_item.checked_at = datetime.now()
        
        # 计算总体合格率
        all_items = QualityCheckItem.query.filter_by(check_id=check_id).all()
        total_qualified = sum(item.qualified_quantity for item in all_items)
        total_checked = sum(item.checked_quantity for item in all_items)
        
        if total_checked > 0:
            overall_pass_rate = (total_qualified / total_checked) * 100
        else:
            overall_pass_rate = 0
        
        check.pass_rate = overall_pass_rate
        check.status = 'completed'
        check.completed_at = datetime.now()
        
        db.session.commit()
        
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


@quality_check_bp.route('/checks/<int:check_id>/approve', methods=['POST'])
@login_required
def approve_quality_check(check_id):
    """批准/拒绝质检单"""
    try:
        data = request.get_json()
        approved = data.get('approved', True)
        
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        if check.status != 'completed':
            return jsonify({
                'success': False,
                'message': '只有已完成的质检单才能批准'
            }), 400
        
        check.approved = approved
        check.approved_at = datetime.now()
        check.approved_by = data.get('approved_by')
        
        if not approved:
            check.status = 'rejected'
            check.rejection_reason = data.get('rejection_reason', '')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'质检单已{"批准" if approved else "拒绝"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/statistics', methods=['GET'])
@login_required
def get_quality_stats():
    """获取质检统计信息"""
    try:
        # 使用单次查询统计所有状态，减少数据库查询次数
        from sqlalchemy import func
        
        # 按状态分组统计
        status_counts = db.session.query(
            QualityCheck.status, 
            func.count(QualityCheck.id)
        ).group_by(QualityCheck.status).all()
        
        # 转换为字典
        status_dict = {status: count for status, count in status_counts}
        
        pending_count = status_dict.get('pending', 0)
        inspecting_count = status_dict.get('inspecting', 0)
        completed_count = status_dict.get('completed', 0)
        
        # 合格率统计 - 只查询必要的字段
        stats = db.session.query(
            func.sum(QualityCheckItem.qualified_quantity),
            func.sum(QualityCheckItem.unqualified_quantity)
        ).first()
        
        total_qualified = float(stats[0]) if stats[0] else 0
        total_unqualified = float(stats[1]) if stats[1] else 0
        total_checked = total_qualified + total_unqualified
        pass_rate = (total_qualified / total_checked * 100) if total_checked > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'pending': pending_count,
                'inspecting': inspecting_count,
                'completed': completed_count,
                'avg_pass_rate': round(pass_rate, 2)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
