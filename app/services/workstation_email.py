# -*- coding: utf-8 -*-
"""
工作台邮件通知服务
提供每日待办汇总邮件和紧急事项即时通知
"""
from app.utils.email_service import email_service
from app.models.spare_part import SparePart
from app.models.spare_part_advanced import (
    SparePartQualityInspection, SparePartFaultRecord,
    SparePartLifecycleTransition
)
from app.models.user import User
from app.extensions import db
from datetime import datetime


def get_todos_data():
    """获取待办事项数据"""
    todos = []
    
    # 库存预警
    out_parts = SparePart.query.filter_by(stock_status='out').limit(10).all()
    for sp in out_parts:
        todos.append({
            'type': 'out_of_stock',
            'priority': 'danger',
            'title': f'{sp.name} 已缺货',
            'description': f'当前库存: 0，最低库存: {sp.min_stock}，请尽快补货',
            'part_code': sp.part_code
        })
    
    low_parts = SparePart.query.filter_by(stock_status='low').limit(10).all()
    for sp in low_parts:
        todos.append({
            'type': 'low_stock',
            'priority': 'warning',
            'title': f'{sp.name} 库存不足',
            'description': f'当前库存: {sp.current_stock}，最低库存: {sp.min_stock}',
            'part_code': sp.part_code
        })
    
    # 待检验
    pending_inspections = SparePartQualityInspection.query.filter_by(
        inspection_result='pending'
    ).order_by(SparePartQualityInspection.created_at.desc()).limit(10).all()
    for insp in pending_inspections:
        part_name = insp.spare_part.name if insp.spare_part else '未知备件'
        todos.append({
            'type': 'pending_inspection',
            'priority': 'warning',
            'title': f'待质量检验: {part_name}',
            'description': f'检验单号: {insp.inspection_code or "未设置"}，检验日期: {insp.inspection_date.strftime("%Y-%m-%d") if insp.inspection_date else "待安排"}',
        })
    
    # 待处理故障
    open_faults = SparePartFaultRecord.query.filter_by(status='open').order_by(
        SparePartFaultRecord.fault_time.desc()
    ).limit(10).all()
    for fault in open_faults:
        priority_text = '高优先级' if fault.priority >= 7 else '中优先级' if fault.priority >= 4 else '低优先级'
        equipment_name = fault.equipment.equipment_name if fault.equipment else '未知设备'
        todos.append({
            'type': 'open_fault',
            'priority': 'danger' if fault.priority >= 7 else 'warning',
            'title': f'{priority_text}故障: {fault.fault_description or "未知故障"}',
            'description': f'设备: {equipment_name}，发生时间: {fault.fault_time.strftime("%Y-%m-%d %H:%M") if fault.fault_time else "-"}',
        })
    
    return todos


def generate_summary_email_html(todos):
    """生成汇总邮件HTML"""
    today = datetime.now().strftime('%Y年%m月%d日')
    
    # 分类统计
    out_count = sum(1 for t in todos if t['type'] == 'out_of_stock')
    low_count = sum(1 for t in todos if t['type'] == 'low_stock')
    inspection_count = sum(1 for t in todos if t['type'] == 'pending_inspection')
    fault_count = sum(1 for t in todos if t['type'] == 'open_fault')
    
    high_priority_count = sum(1 for t in todos if t['priority'] == 'danger')
    
    items_html = ''
    for t in todos[:20]:  # 最多显示20条
        color = '#e74c3c' if t['priority'] == 'danger' else '#f39c12'
        items_html += f'''
        <div style="padding: 12px; margin-bottom: 8px; background-color: #f8f9fa; border-radius: 6px; border-left: 3px solid {color};">
            <div style="font-weight: 600; color: #2d3748; margin-bottom: 4px;">{t['title']}</div>
            <div style="font-size: 13px; color: #718096;">{t['description']}</div>
        </div>
        '''
    
    if not items_html:
        items_html = '<div style="text-align: center; padding: 30px; color: #718096;"><p>暂无待办事项，一切正常！</p></div>'
    
    return f'''
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; background-color: #f5f7fa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto;">
            <!-- 头部 -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 12px 12px 0 0; color: white;">
                <h2 style="margin: 0; font-size: 20px;">备件管理系统 - 每日待办汇总</h2>
                <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">{today}</p>
            </div>
            
            <!-- 统计卡片 -->
            <div style="background: white; padding: 20px;">
                <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #2d3748;">待办概览</h3>
                <div style="display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 120px; background: #fde8e8; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 700; color: #e74c3c;">{out_count}</div>
                        <div style="font-size: 12px; color: #718096;">缺货备件</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background: #fef3e2; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 700; color: #f39c12;">{low_count}</div>
                        <div style="font-size: 12px; color: #718096;">低库存</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background: #e8f4fd; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 700; color: #3498db;">{inspection_count}</div>
                        <div style="font-size: 12px; color: #718096;">待检验</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background: #fde8e8; padding: 12px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 700; color: #e74c3c;">{fault_count}</div>
                        <div style="font-size: 12px; color: #718096;">待处理故障</div>
                    </div>
                </div>
                
                {f'<div style="background: #fde8e8; padding: 10px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; color: #e74c3c;"><strong>注意：</strong>有 {high_priority_count} 个高优先级待办事项需要尽快处理！</div>' if high_priority_count > 0 else ''}
                
                <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #2d3748;">待办详情</h3>
                {items_html}
            </div>
            
            <!-- 快捷操作 -->
            <div style="background: white; padding: 20px; margin-top: 1px;">
                <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #2d3748;">快捷操作</h3>
                <p style="font-size: 14px; color: #718096;">请登录系统处理待办事项</p>
                <p style="font-size: 13px; color: #a0aec0;">系统地址: http://localhost:5000</p>
            </div>
            
            <!-- 底部 -->
            <div style="background: #f8f9fa; padding: 16px 20px; border-radius: 0 0 12px 12px; text-align: center;">
                <p style="margin: 0; font-size: 12px; color: #a0aec0;">
                    此邮件由备件管理系统自动发送，请勿直接回复。<br>
                    发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </div>
    </body>
    </html>
    '''


def send_daily_todo_summary():
    """发送每日待办汇总邮件"""
    try:
        todos = get_todos_data()
        
        if not todos:
            print('暂无待办事项，跳过邮件发送')
            return True
        
        users = User.query.filter_by(is_active=True).all()
        
        success_count = 0
        for user in users:
            if user.email:
                html = generate_summary_email_html(todos)
                success = email_service.send_email(
                    to_email=user.email,
                    to_name=user.real_name or user.username,
                    subject=f'备件管理系统 - 每日待办汇总 ({len(todos)} 项待办)',
                    html_content=html
                )
                if success:
                    success_count += 1
                    print(f'汇总邮件发送成功: {user.email}')
                else:
                    print(f'汇总邮件发送失败: {user.email}')
        
        print(f'每日待办汇总邮件发送完成: 成功 {success_count}/{len(users)}')
        return success_count > 0
        
    except Exception as e:
        print(f'发送每日待办汇总邮件失败: {e}')
        return False


def send_urgent_notification(todo_type, todo_data):
    """发送紧急事项即时通知"""
    try:
        users = User.query.filter_by(is_active=True).all()
        
        # 根据不同类型设置邮件内容
        if todo_type == 'out_of_stock':
            subject = f'紧急通知: {todo_data.get("name", "备件")} 已缺货'
            priority = 'danger'
            body = f'''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 500px; margin: 0 auto; padding: 20px;">
                    <div style="background: #e74c3c; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="margin: 0;">紧急通知 - 备件缺货</h2>
                    </div>
                    <div style="background: #fde8e8; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                        <p style="margin: 0 0 8px 0; font-weight: 600;">{todo_data.get("name", "未知备件")}</p>
                        <p style="margin: 0; color: #718096;">当前库存: 0</p>
                        <p style="margin: 0; color: #718096;">最低库存: {todo_data.get("min_stock", "-")}</p>
                    </div>
                    <p style="color: #e74c3c; font-weight: 500;">请尽快安排补货，避免影响生产！</p>
                    <p style="font-size: 12px; color: #a0aec0; margin-top: 20px;">
                        发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        此邮件由系统自动发送
                    </p>
                </div>
            </body>
            </html>
            '''
        elif todo_type == 'high_priority_fault':
            subject = f'紧急通知: 高优先级故障待处理'
            priority = 'danger'
            body = f'''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 500px; margin: 0 auto; padding: 20px;">
                    <div style="background: #e74c3c; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="margin: 0;">紧急通知 - 高优先级故障</h2>
                    </div>
                    <div style="background: #fde8e8; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                        <p style="margin: 0 0 8px 0; font-weight: 600;">{todo_data.get("description", "未知故障")}</p>
                        <p style="margin: 0; color: #718096;">设备: {todo_data.get("equipment", "未知设备")}</p>
                    </div>
                    <p style="color: #e74c3c; font-weight: 500;">请尽快处理故障，避免影响设备运行！</p>
                    <p style="font-size: 12px; color: #a0aec0; margin-top: 20px;">
                        发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        此邮件由系统自动发送
                    </p>
                </div>
            </body>
            </html>
            '''
        else:
            return True
        
        success_count = 0
        for user in users:
            if user.email:
                success = email_service.send_email(
                    to_email=user.email,
                    to_name=user.real_name or user.username,
                    subject=subject,
                    html_content=body
                )
                if success:
                    success_count += 1
        
        print(f'紧急通知发送完成: {subject}, 成功 {success_count}/{len(users)}')
        return success_count > 0
        
    except Exception as e:
        print(f'发送紧急通知失败: {e}')
        return False
