"""
质检管理页面路由
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models.warehouse_v3.quality_check import QualityCheckStandard
from app.models.spare_part import SparePart
from app import db
from sqlalchemy import and_

quality_check_pages_bp = Blueprint('quality_check_pages', __name__)


@quality_check_pages_bp.route('/quality-check')
@login_required
def quality_check():
    """质检管理页面"""
    return render_template('warehouse_v3/quality_check.html')


@quality_check_pages_bp.route('/quality-standard')
@login_required
def quality_standard():
    """质检标准管理页面"""
    return render_template('warehouse_new/quality_standard.html')


# API 路由
@quality_check_pages_bp.route('/api/quality-check/standards', methods=['GET'])
@login_required
def get_quality_standards():
    """获取质检标准列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        part_code = request.args.get('part_code', '')
        is_active = request.args.get('is_active', None)
        
        # 构建查询条件
        filters = []
        if part_code:
            filters.append(QualityCheckStandard.part_code.like(f'%{part_code}%'))
        if is_active is not None:
            filters.append(QualityCheckStandard.is_active == (is_active == 'true'))
        
        # 执行查询
        query = QualityCheckStandard.query
        if filters:
            query = query.filter(and_(*filters))
        
        # 分页
        pagination = query.order_by(QualityCheckStandard.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 格式化结果
        standards = []
        for item in pagination.items:
            part = SparePart.query.get(item.part_id) if item.part_id else None
            standards.append({
                'id': item.id,
                'part_id': item.part_id,
                'part_code': item.part_code or '',
                'part_name': part.name if part else '',
                'check_item': item.check_item,
                'check_method': item.check_method,
                'standard_value': item.standard_value,
                'min_value': float(item.min_value) if item.min_value else None,
                'max_value': float(item.max_value) if item.max_value else None,
                'unit': item.unit,
                'severity_level': item.severity_level,
                'is_active': item.is_active,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else ''
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': standards,
                'total': pagination.total
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_pages_bp.route('/api/quality-check/standards', methods=['POST'])
@login_required
def create_quality_standard():
    """创建质检标准"""
    try:
        data = request.get_json()
        
        standard = QualityCheckStandard(
            part_id=data.get('part_id'),
            part_code=data.get('part_code'),
            check_item=data.get('check_item'),
            check_method=data.get('check_method'),
            standard_value=data.get('standard_value'),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            unit=data.get('unit'),
            severity_level=data.get('severity_level', 'normal'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(standard)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_pages_bp.route('/api/quality-check/standards/<int:standard_id>', methods=['PUT'])
@login_required
def update_quality_standard(standard_id):
    """更新质检标准"""
    try:
        data = request.get_json()
        standard = QualityCheckStandard.query.get_or_404(standard_id)
        
        standard.part_id = data.get('part_id', standard.part_id)
        standard.part_code = data.get('part_code', standard.part_code)
        standard.check_item = data.get('check_item', standard.check_item)
        standard.check_method = data.get('check_method', standard.check_method)
        standard.standard_value = data.get('standard_value', standard.standard_value)
        standard.min_value = data.get('min_value', standard.min_value)
        standard.max_value = data.get('max_value', standard.max_value)
        standard.unit = data.get('unit', standard.unit)
        standard.severity_level = data.get('severity_level', standard.severity_level)
        standard.is_active = data.get('is_active', standard.is_active)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_pages_bp.route('/api/quality-check/standards/<int:standard_id>', methods=['DELETE'])
@login_required
def delete_quality_standard(standard_id):
    """删除质检标准"""
    try:
        standard = QualityCheckStandard.query.get_or_404(standard_id)
        db.session.delete(standard)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_pages_bp.route('/api/spare-parts', methods=['GET'])
@login_required
def get_spare_parts():
    """获取备件列表"""
    try:
        limit = request.args.get('limit', 1000, type=int)
        parts = SparePart.query.limit(limit).all()
        
        parts_list = []
        for part in parts:
            parts_list.append({
                'id': part.id,
                'code': part.code if hasattr(part, 'code') else part.part_code,
                'name': part.name if hasattr(part, 'name') else part.part_name,
                'specification': part.specification if hasattr(part, 'specification') else '',
                'brand': part.brand if hasattr(part, 'brand') else ''
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': parts_list
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# 质检单 API（需要创建质检单模型后实现）
@quality_check_pages_bp.route('/api/quality-check', methods=['GET'])
@login_required
def get_quality_checks():
    """获取质检单列表"""
    try:
        # 暂时返回空列表，等待模型创建
        return jsonify({
            'success': True,
            'data': {
                'list': [],
                'total': 0
            },
            'stats': {
                'pending': 0,
                'inspecting': 0,
                'completed': 0,
                'pass_rate': 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_pages_bp.route('/api/quality-check', methods=['POST'])
@login_required
def create_quality_check():
    """创建质检单"""
    try:
        data = request.get_json()
        # TODO: 实现创建逻辑
        return jsonify({
            'success': True,
            'message': '创建成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_pages_bp.route('/api/quality-check/<int:check_id>/start', methods=['POST'])
@login_required
def start_quality_check(check_id):
    """开始质检"""
    try:
        # TODO: 实现开始质检逻辑
        return jsonify({
            'success': True,
            'message': '已开始质检'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@quality_check_pages_bp.route('/api/inbound-orders', methods=['GET'])
@login_required
def get_inbound_orders():
    """获取入库单列表（简化版）"""
    try:
        limit = request.args.get('limit', 100, type=int)
        status = request.args.get('status', '')
        
        # TODO: 从数据库获取真实的入库单
        # 暂时返回空列表
        return jsonify({
            'success': True,
            'data': {
                'list': []
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
