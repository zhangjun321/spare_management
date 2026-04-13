# -*- coding: utf-8 -*-
"""
React 仓库管理模块路由
提供 React 前端页面的服务 - 完全独立版本
"""

from flask import Blueprint, Response
import os

# 创建蓝图，使用独立的URL前缀，完全隔离
react_warehouse_bp = Blueprint('react_warehouse', __name__)

# React 应用目录
REACT_APP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'react')


def serve_react_html():
    """
    服务 React 应用的 HTML 文件
    直接返回完整的 HTML 内容，不被 Flask 模板包裹
    """
    html_path = os.path.join(REACT_APP_DIR, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return Response(
        html_content,
        mimetype='text/html',
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'X-Content-Type-Options': 'nosniff'
        }
    )


# 使用独立的 URL 前缀 /warehouse-react/，完全避免和 Flask 的 /warehouses/ 冲突
@react_warehouse_bp.route('/warehouse-react/<path:path>')
def serve_react_app(path):
    """
    服务 React 应用的所有路由
    所有 /warehouse-react/* 路径都返回 React 的完整 HTML，由 React Router 处理前端路由
    """
    return serve_react_html()


@react_warehouse_bp.route('/warehouse-react/')
def warehouse_index():
    """
    仓库管理模块首页
    """
    return serve_react_html()


@react_warehouse_bp.route('/warehouse-react/dashboard')
def dashboard():
    """
    仓库管理驾驶舱
    """
    return serve_react_html()


@react_warehouse_bp.route('/warehouse-react/inbound')
def inbound():
    """
    入库管理页面
    """
    return serve_react_html()


@react_warehouse_bp.route('/warehouse-react/outbound')
def outbound():
    """
    出库管理页面
    """
    return serve_react_html()


@react_warehouse_bp.route('/warehouse-react/inventory')
def inventory():
    """
    库存管理页面
    """
    return serve_react_html()


@react_warehouse_bp.route('/warehouse-react/analysis')
def analysis():
    """
    仓库分析页面
    """
    return serve_react_html()
