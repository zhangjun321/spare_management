# -*- coding: utf-8 -*-
"""
盘点任务前端页面路由
"""
from flask import Blueprint, render_template
from flask_login import login_required

stock_take_pages_bp = Blueprint('stock_take_pages', __name__, url_prefix='/stock-takes')


@stock_take_pages_bp.route('/')
@login_required
def list_page():
    """盘点任务列表页"""
    return render_template('stock_take/list.html')


@stock_take_pages_bp.route('/new')
@login_required
def new_page():
    """新建盘点任务"""
    return render_template('stock_take/new.html')


@stock_take_pages_bp.route('/<int:task_id>/execute')
@login_required
def execute_page(task_id):
    """执行盘点"""
    return render_template('stock_take/execute.html', task_id=task_id)


@stock_take_pages_bp.route('/<int:task_id>')
@login_required
def detail_page(task_id):
    """盘点详情"""
    return render_template('stock_take/detail.html', task_id=task_id)


@stock_take_pages_bp.route('/adjustments')
@login_required
def adjustments_page():
    """调整单列表"""
    return render_template('stock_take/adjustments.html')
