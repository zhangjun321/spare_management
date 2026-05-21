# -*- coding: utf-8 -*-
"""
调拨单前端页面路由
"""
from flask import Blueprint, render_template
from flask_login import login_required

transfer_order_pages_bp = Blueprint('transfer_order_pages', __name__, url_prefix='/transfer-orders')


@transfer_order_pages_bp.route('/')
@login_required
def list_page():
    """调拨单列表页"""
    return render_template('transfer_order/list.html')


@transfer_order_pages_bp.route('/new')
@login_required
def new_page():
    """新建调拨单"""
    return render_template('transfer_order/form.html', is_edit=False)


@transfer_order_pages_bp.route('/<int:order_id>/edit')
@login_required
def edit_page(order_id):
    """编辑调拨单"""
    return render_template('transfer_order/form.html', is_edit=True, order_id=order_id)


@transfer_order_pages_bp.route('/<int:order_id>')
@login_required
def detail_page(order_id):
    """调拨单详情"""
    return render_template('transfer_order/detail.html', order_id=order_id)
