# -*- coding: utf-8 -*-
"""
React 备件管理模块路由入口
所有 /spare-parts-react/* 请求均返回 React SPA index.html
"""

from flask import Blueprint, Response, abort, redirect, url_for, request
import os

react_spare_parts_bp = Blueprint('react_spare_parts', __name__)

REACT_APP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'react')


def serve_react_html():
    html_path = os.path.join(REACT_APP_DIR, 'index.html')
    if not os.path.exists(html_path):
        abort(503, description='React 应用尚未构建，请先执行 npm run build')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return Response(
        html_content,
        mimetype='text/html',
        headers={'Content-Type': 'text/html; charset=utf-8', 'X-Content-Type-Options': 'nosniff'},
    )


@react_spare_parts_bp.route('/spare-parts-react/', defaults={'path': ''})
@react_spare_parts_bp.route('/spare-parts-react/<path:path>')
@react_spare_parts_bp.route('/react/', defaults={'path': ''})
@react_spare_parts_bp.route('/react/<path:path>')
def serve_react_app(path):
    """React SPA 通配路由 — 备件管理/交易管理等前端入口"""
    return serve_react_html()


@react_spare_parts_bp.route('/react/transactions/', defaults={'path': ''})
@react_spare_parts_bp.route('/react/transactions/<path:path>')
def redirect_legacy_react_transactions(path):
    """
    兼容旧交易 React 路由：统一跳转到 Flask 交易页面
    避免浏览器后退进入旧壳子导致样式不一致或页面反复重渲染。
    """
    target_map = {
        '': 'transactions.list_page',
        'list': 'transactions.list_page',
        'inbound': 'transactions.inbound_page',
        'outbound': 'transactions.outbound_page',
        'transfer': 'transactions.transfer',
        'inventory': 'transactions.inventory_page',
    }
    endpoint = target_map.get(path, 'transactions.list_page')
    target = url_for(endpoint)
    qs = request.query_string.decode('utf-8')
    if qs:
        target = f'{target}?{qs}'
    return redirect(target, code=302)


