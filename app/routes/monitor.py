# -*- coding: utf-8 -*-
"""
系统监控路由
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.utils.decorators import permission_required
from app.services.system_monitor_service import SystemMonitorService

monitor_bp = Blueprint('monitor', __name__, template_folder='../templates/monitor')


@monitor_bp.route('/')
@login_required
@permission_required('system', 'read')
def monitor_index():
    """系统监控首页"""
    return render_template('monitor/index.html')


@monitor_bp.route('/api/server')
@login_required
@permission_required('system', 'read')
def get_server_status():
    """获取服务器状态"""
    return jsonify(SystemMonitorService.get_server_status())


@monitor_bp.route('/api/database')
@login_required
@permission_required('system', 'read')
def get_database_status():
    """获取数据库状态"""
    return jsonify(SystemMonitorService.get_database_status())


@monitor_bp.route('/api/redis')
@login_required
@permission_required('system', 'read')
def get_redis_status():
    """获取 Redis 状态"""
    return jsonify(SystemMonitorService.get_redis_status())


@monitor_bp.route('/api/service')
@login_required
@permission_required('system', 'read')
def get_service_status():
    """获取服务状态"""
    return jsonify(SystemMonitorService.get_service_status())


@monitor_bp.route('/api/overview')
@login_required
@permission_required('system', 'read')
def get_monitor_overview():
    """获取监控概览"""
    server_status = SystemMonitorService.get_server_status()
    database_status = SystemMonitorService.get_database_status()
    redis_status = SystemMonitorService.get_redis_status()
    service_status = SystemMonitorService.get_service_status()
    
    # 计算总体健康度
    health_score = 100
    issues = []
    
    if server_status['status'] == 'success':
        cpu_status = server_status['data']['cpu']['status']
        memory_status = server_status['data']['memory']['status']
        disk_status = server_status['data']['disk']['status']
        
        if cpu_status == 'critical' or memory_status == 'critical' or disk_status == 'critical':
            health_score -= 30
            issues.append('严重资源告警')
        elif cpu_status == 'warning' or memory_status == 'warning' or disk_status == 'warning':
            health_score -= 15
            issues.append('资源使用率偏高')
    
    if database_status['status'] == 'error':
        health_score -= 30
        issues.append('数据库连接异常')
    
    if redis_status['status'] == 'error':
        health_score -= 20
        issues.append('Redis 连接异常')
    
    return jsonify({
        'status': 'success',
        'data': {
            'health_score': health_score,
            'health_level': '优秀' if health_score >= 90 else '良好' if health_score >= 70 else '一般' if health_score >= 50 else '较差',
            'issues': issues,
            'server': server_status,
            'database': database_status,
            'redis': redis_status,
            'service': service_status
        }
    })
