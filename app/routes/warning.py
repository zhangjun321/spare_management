from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.warehouse_v3 import WarningRule, WarningLog
from app.models.warehouse_v3.inventory import InventoryV3
from datetime import datetime
import json

warning_bp = Blueprint('warning', __name__, url_prefix='/api/warning')


@warning_bp.route('/rules', methods=['GET'])
@login_required
def get_warning_rules():
    """获取所有预警规则"""
    try:
        rules = WarningRule.query.order_by(WarningRule.created_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [rule.to_dict() for rule in rules]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/rules', methods=['POST'])
@login_required
def create_warning_rule():
    """创建预警规则"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['rule_name', 'rule_type', 'condition_field', 'condition_operator', 'threshold_value']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400
        
        # 检查规则名称是否重复
        existing_rule = WarningRule.query.filter_by(rule_name=data['rule_name']).first()
        if existing_rule:
            return jsonify({
                'success': False,
                'message': '规则名称已存在'
            }), 400
        
        rule = WarningRule(
            rule_name=data['rule_name'],
            rule_type=data['rule_type'],
            condition_field=data['condition_field'],
            condition_operator=data['condition_operator'],
            threshold_value=data['threshold_value'],
            threshold_unit=data.get('threshold_unit', ''),
            warning_level=data.get('warning_level', 'medium'),
            notification_method=json.dumps(data.get('notification_methods', [])),
            enabled=data.get('enabled', True),
            remark=data.get('remark', '')
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '预警规则创建成功',
            'data': rule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@login_required
def update_warning_rule(rule_id):
    """更新预警规则"""
    try:
        rule = WarningRule.query.get(rule_id)
        if not rule:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404
        
        data = request.get_json()
        
        # 更新字段
        if 'rule_name' in data:
            # 检查名称是否重复
            existing = WarningRule.query.filter_by(rule_name=data['rule_name']).first()
            if existing and existing.id != rule_id:
                return jsonify({
                    'success': False,
                    'message': '规则名称已存在'
                }), 400
            rule.rule_name = data['rule_name']
        
        if 'rule_type' in data:
            rule.rule_type = data['rule_type']
        if 'condition_field' in data:
            rule.condition_field = data['condition_field']
        if 'condition_operator' in data:
            rule.condition_operator = data['condition_operator']
        if 'threshold_value' in data:
            rule.threshold_value = data['threshold_value']
        if 'threshold_unit' in data:
            rule.threshold_unit = data['threshold_unit']
        if 'warning_level' in data:
            rule.warning_level = data['warning_level']
        if 'notification_methods' in data:
            rule.notification_method = json.dumps(data['notification_methods'])
        if 'enabled' in data:
            rule.enabled = data['enabled']
        if 'remark' in data:
            rule.remark = data['remark']
        
        rule.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '预警规则更新成功',
            'data': rule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@login_required
def delete_warning_rule(rule_id):
    """删除预警规则"""
    try:
        rule = WarningRule.query.get(rule_id)
        if not rule:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404
        
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '预警规则删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/rules/<int:rule_id>/toggle', methods=['POST'])
@login_required
def toggle_warning_rule(rule_id):
    """启用/禁用预警规则"""
    try:
        rule = WarningRule.query.get(rule_id)
        if not rule:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404
        
        rule.enabled = not rule.enabled
        rule.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'规则已{"启用" if rule.enabled else "禁用"}',
            'data': rule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/logs', methods=['GET'])
@login_required
def get_warning_logs():
    """获取预警日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        logs = WarningLog.query.order_by(WarningLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'list': [log.to_dict() for log in logs.items],
                'total': logs.total,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/check', methods=['POST'])
@login_required
def check_warnings():
    """检查库存并触发预警"""
    try:
        data = request.get_json()
        inventory_ids = data.get('inventory_ids', [])
        
        # 获取所有启用的预警规则
        rules = WarningRule.query.filter_by(enabled=True).all()
        
        triggered_warnings = []
        
        # 如果没有指定库存 ID，检查所有库存
        if not inventory_ids:
            inventories = InventoryV3.query.all()
        else:
            inventories = InventoryV3.query.filter(InventoryV3.id.in_(inventory_ids)).all()
        
        for inventory in inventories:
            for rule in rules:
                # 检查规则类型是否匹配
                if rule.rule_type == 'stock' and rule.condition_field == 'quantity':
                    # 获取当前库存数量
                    current_value = inventory.quantity
                    
                    # 根据条件运算符检查是否触发预警
                    triggered = False
                    if rule.condition_operator == '<=' and current_value <= float(rule.threshold_value):
                        triggered = True
                    elif rule.condition_operator == '<' and current_value < float(rule.threshold_value):
                        triggered = True
                    elif rule.condition_operator == '>=' and current_value >= float(rule.threshold_value):
                        triggered = True
                    elif rule.condition_operator == '>' and current_value > float(rule.threshold_value):
                        triggered = True
                    elif rule.condition_operator == '=' and current_value == float(rule.threshold_value):
                        triggered = True
                    
                    if triggered:
                        # 创建预警日志
                        warning_log = WarningLog(
                            rule_id=rule.id,
                            inventory_id=inventory.id,
                            warning_type=rule.rule_type,
                            warning_level=rule.warning_level,
                            warning_content=f'库存 {inventory.part_name} (规格：{inventory.specification}) 当前数量 {current_value} {rule.threshold_unit}, 触发预警条件：{rule.condition_operator} {rule.threshold_value}',
                            current_value=str(current_value),
                            threshold_value=rule.threshold_value,
                            notification_sent=True,
                            notification_time=datetime.now()
                        )
                        db.session.add(warning_log)
                        triggered_warnings.append({
                            'inventory': inventory.to_dict(),
                            'rule': rule.to_dict(),
                            'log': warning_log.to_dict()
                        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'检查完成，触发 {len(triggered_warnings)} 条预警',
            'data': triggered_warnings
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/stats', methods=['GET'])
@login_required
def get_warning_stats():
    """获取预警统计信息"""
    try:
        # 按级别统计
        high_count = WarningLog.query.filter_by(warning_level='high').count()
        medium_count = WarningLog.query.filter_by(warning_level='medium').count()
        low_count = WarningLog.query.filter_by(warning_level='low').count()
        
        # 今日预警数量
        today = datetime.now().date()
        today_count = WarningLog.query.filter(
            db.func.date(WarningLog.created_at) == today
        ).count()
        
        # 未处理预警数量（假设已读标记为 False）
        unread_count = WarningLog.query.filter_by(is_read=False).count()
        
        return jsonify({
            'success': True,
            'data': {
                'by_level': {
                    'high': high_count,
                    'medium': medium_count,
                    'low': low_count
                },
                'today_count': today_count,
                'unread_count': unread_count,
                'total_count': high_count + medium_count + low_count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/logs/<int:log_id>/read', methods=['POST'])
@login_required
def mark_warning_as_read(log_id):
    """标记预警为已读"""
    try:
        log = WarningLog.query.get(log_id)
        if not log:
            return jsonify({
                'success': False,
                'message': '预警日志不存在'
            }), 404
        
        log.is_read = True
        log.read_time = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '已标记为已读'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@warning_bp.route('/logs/batch-read', methods=['POST'])
@login_required
def batch_mark_warnings_as_read():
    """批量标记预警为已读"""
    try:
        data = request.get_json()
        log_ids = data.get('log_ids', [])
        
        if not log_ids:
            return jsonify({
                'success': False,
                'message': '请指定要标记的预警日志 ID'
            }), 400
        
        WarningLog.query.filter(WarningLog.id.in_(log_ids)).update(
            {'is_read': True, 'read_time': datetime.now()},
            synchronize_session=False
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功标记 {len(log_ids)} 条预警为已读'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
