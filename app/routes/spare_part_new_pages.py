"""
备件管理模块高级功能前端页面路由
包含5个功能页面：预测与补货、质量管理、故障诊断、生命周期、综合分析
"""

from flask import Blueprint, render_template, make_response
from flask_login import login_required
from datetime import datetime

spare_part_new_pages_bp = Blueprint('spare_part_new_pages', __name__, url_prefix='/spare_parts_plus')


def add_no_cache_headers(response):
    """添加禁止缓存的响应头"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ========================================
# 功能1：智能预测与补货页面
# ========================================

@spare_part_new_pages_bp.route('/prediction')
@login_required
def prediction_dashboard():
    """智能预测与补货主页面"""
    response = make_response(render_template('spare_parts_new/prediction.html'))
    return add_no_cache_headers(response)


# ========================================
# 功能2：备件质量管理页面
# ========================================

@spare_part_new_pages_bp.route('/quality')
@login_required
def quality_dashboard():
    """备件质量管理主页面"""
    response = make_response(render_template('spare_parts_new/quality.html'))
    return add_no_cache_headers(response)


# ========================================
# 功能3：故障诊断与维护页面
# ========================================

@spare_part_new_pages_bp.route('/diagnosis')
@login_required
def diagnosis_dashboard():
    """故障诊断与维护主页面"""
    response = make_response(render_template('spare_parts_new/diagnosis.html'))
    return add_no_cache_headers(response)


# ========================================
# 功能4：生命周期管理页面
# ========================================

@spare_part_new_pages_bp.route('/lifecycle')
@login_required
def lifecycle_dashboard():
    """生命周期管理主页面"""
    response = make_response(render_template('spare_parts_new/lifecycle.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Surrogate-Control'] = 'no-store'
    return response


# ========================================
# 功能5：综合分析驾驶舱
# ========================================

@spare_part_new_pages_bp.route('/dashboard')
@login_required
def spare_part_dashboard():
    """综合分析驾驶舱页面"""
    response = make_response(render_template('spare_parts_new/dashboard.html'))
    return add_no_cache_headers(response)
