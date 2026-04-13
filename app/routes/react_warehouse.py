# -*- coding: utf-8 -*-
"""
React 仓库管理模块路由
提供 React 前端页面的服务 - 完全独立版本
"""

from flask import Blueprint, Response, abort
import os

# 创建蓝图，使用独立的URL前缀，完全隔离
react_warehouse_bp = Blueprint('react_warehouse', __name__)

# React 应用目录（构建产物）
REACT_APP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'react')


def serve_react_html():
    """
    服务 React 应用的 HTML 文件
    直接返回完整的 HTML 内容，不被 Flask 模板包裹
    """
    html_path = os.path.join(REACT_APP_DIR, 'index.html')
    if not os.path.exists(html_path):
        abort(503, description='React 应用尚未构建，请先执行 npm run build')

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    return Response(
        html_content,
        mimetype='text/html',
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'X-Content-Type-Options': 'nosniff',
        }
    )


# ---------------------------------------------------------------
# 通配路由：所有 /warehouse-react/* 请求均返回 React index.html
# React Router (BrowserRouter) 在客户端接管后续路由解析
# 这样无论用户刷新哪个子路径都不会出现 404
# ---------------------------------------------------------------

@react_warehouse_bp.route('/warehouse-react/', defaults={'path': ''})
@react_warehouse_bp.route('/warehouse-react/<path:path>')
def serve_react_app(path):
    """
    React SPA 通配路由入口
    覆盖所有 /warehouse-react/ 下的路径，交由 React Router 处理
    """
    return serve_react_html()
