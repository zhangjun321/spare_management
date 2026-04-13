"""
质检管理 API 路由
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.warehouse_v3.quality_check import QualityCheck, QualityCheckItem
from app.models.warehouse_v3.inbound import InboundOrderV3
from app.services.warehouse_v3.quality_check_service import QualityCheckService
from datetime import datetime
from decimal import Decimal

quality_check_bp = Blueprint('quality_check_v3', __name__, url_prefix='/api/quality-check/v3')


@quality_check_bp.route('/checks', methods=['GET'])
@login_required
def get_quality_checks():
    """获取质检单列表"""
    try:
        status = request.args.get('status')
        inbound_order_id = request.args.get('inbound_order_id')
        
        query = QualityCheck.query
        
        if status:
            query = query.filter_by(status=status)
        if inbound_order_id:
            query = query.filter_by(inbound_order_id=int(inbound_order_id))
        
        checks = query.order_by(QualityCheck.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [check.to_dict() for check in checks]
        })
    except Exception as e:
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
        
        data = check.to_dict()
        data['items'] = [item.to_dict() for item in check.items.all()]
        
        return jsonify({
            'success': True,
            'data': data
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
        if 'inbound_order_id' not in data:
            return jsonify({
                'success': False,
                'message': '缺少入库单 ID'
            }), 400
        
        # 检查入库单是否存在
        inbound_order = InboundOrderV3.query.get(data['inbound_order_id'])
        if not inbound_order:
            return jsonify({
                'success': False,
                'message': '入库单不存在'
            }), 404
        
        # 检查入库单状态
        if inbound_order.status not in ['pending', 'received']:
            return jsonify({
                'success': False,
                'message': f'入库单状态不正确：{inbound_order.status}'
            }), 400
        
        # 创建质检单
        check = QualityCheckService.create_quality_check({
            'inbound_order_id': data['inbound_order_id'],
            'check_type': data.get('check_type', 'inbound'),
            'inspection_type': data.get('inspection_type', 'sampling'),
            'check_method': data.get('check_method', 'sampling'),
            'sample_ratio': data.get('sample_ratio'),
            'sample_size': data.get('sample_size'),
            'created_by': current_user.id,
            'remark': data.get('remark')
        })
        
        return jsonify({
            'success': True,
            'message': '质检单创建成功',
            'data': check.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/start', methods=['POST'])
@login_required
def start_inspection(check_id):
    """开始质检"""
    try:
        success = QualityCheckService.start_inspection(check_id, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '质检已开始'
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法开始质检，请检查质检单状态'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/submit', methods=['POST'])
@login_required
def submit_inspection_result(check_id):
    """提交质检结果"""
    try:
        data = request.get_json()
        
        if 'items' not in data:
            return jsonify({
                'success': False,
                'message': '缺少质检项目数据'
            }), 400
        
        success, message = QualityCheckService.submit_inspection_result(
            check_id,
            data['items'],
            current_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/approve', methods=['POST'])
@login_required
def approve_quality_check(check_id):
    """审批质检结果"""
    try:
        data = request.get_json()
        approved = data.get('approved', True)
        
        success = QualityCheckService.approve_quality_check(check_id, current_user.id, approved)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'质检单已{"批准" if approved else "拒绝"}'
            })
        else:
            return jsonify({
                'success': False,
                'message': '审批失败，请检查质检单状态'
            }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/complete', methods=['POST'])
@login_required
def complete_quality_check(check_id):
    """完成质检并入库"""
    try:
        check = QualityCheck.query.get(check_id)
        if not check:
            return jsonify({
                'success': False,
                'message': '质检单不存在'
            }), 404
        
        if check.status != 'approved':
            return jsonify({
                'success': False,
                'message': '质检单未批准，无法入库'
            }), 400
        
        success, message = QualityCheckService.complete_inbound_with_check(
            check.inbound_order_id,
            current_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/checks/<int:check_id>/cancel', methods=['POST'])
@login_required
def cancel_quality_check(check_id):
    """取消质检单"""
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
                'message': f'无法取消状态为 {check.status} 的质检单'
            }), 400
        
        check.status = 'cancelled'
        check.cancelled_at = datetime.utcnow()
        check.cancelled_by = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '质检单已取消'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取质检统计信息"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        stats = QualityCheckService.get_quality_check_statistics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_bp.route('/items/<int:item_id>', methods=['PUT'])
@login_required
def update_quality_check_item(item_id):
    """更新质检项目"""
    try:
        data = request.get_json()
        
        item = QualityCheckItem.query.get(item_id)
        if not item:
            return jsonify({
                'success': False,
                'message': '质检项目不存在'
            }), 404
        
        # 更新字段
        if 'checked_quantity' in data:
            item.checked_quantity = Decimal(str(data['checked_quantity']))
        if 'qualified_quantity' in data:
            item.qualified_quantity = Decimal(str(data['qualified_quantity']))
        if 'unqualified_quantity' in data:
            item.unqualified_quantity = Decimal(str(data['unqualified_quantity']))
        if 'pass_rate' in data:
            item.pass_rate = data['pass_rate']
        if 'remark' in data:
            item.remark = data['remark']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '质检项目已更新',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
