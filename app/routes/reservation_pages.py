# -*- coding: utf-8 -*-
"""
库存预留前端页面路由
"""
from flask import Blueprint, render_template
from flask_login import login_required

reservation_pages_bp = Blueprint('reservation_pages', __name__, url_prefix='/reservations')


@reservation_pages_bp.route('/')
@login_required
def list_page():
    """预留列表页"""
    return render_template('reservation/list.html')


@reservation_pages_bp.route('/new')
@login_required
def new_page():
    """新建预留"""
    return render_template('reservation/form.html')


@reservation_pages_bp.route('/<int:reservation_id>')
@login_required
def detail_page(reservation_id):
    """预留详情"""
    return render_template('reservation/detail.html', reservation_id=reservation_id)
