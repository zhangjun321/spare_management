#!/usr/bin/env python
"""
测试库存预警和邮件通知系统
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.spare_part import SparePart
from app.models.system import Alert, Notification, EmailConfig
from app.models.user import User
from app.extensions import db

app = create_app()

with app.app_context():
    print("=" * 70)
    print("库存预警和邮件通知系统测试")
    print("=" * 70)
    
    # 1. 检查邮件配置
    print("\n1. 检查邮件配置")
    print("-" * 70)
    email_config = EmailConfig.query.filter_by(is_active=True).first()
    if email_config:
        print(f"✓ 邮件配置已设置")
        print(f"  SMTP 服务器：{email_config.smtp_server}:{email_config.smtp_port}")
        print(f"  发件人邮箱：{email_config.sender_email}")
        print(f"  发件人名称：{email_config.sender_name}")
        print(f"  SSL/TLS: {'是' if email_config.use_tls else '否'}")
    else:
        print("✗ 未配置邮件服务器")
        print("  请先在 系统管理 -> 邮件配置 中配置 SMTP 服务器")
    
    # 2. 检查管理员邮箱
    print("\n2. 检查管理员邮箱")
    print("-" * 70)
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    if admins:
        print(f"✓ 找到 {len(admins)} 个管理员账户")
        for admin in admins:
            if admin.email:
                print(f"  - {admin.real_name or admin.username}: {admin.email}")
            else:
                print(f"  - {admin.real_name or admin.username}: (未设置邮箱) ✗")
    else:
        print("✗ 未找到管理员账户")
    
    # 3. 检查库存预警记录
    print("\n3. 检查库存预警记录")
    print("-" * 70)
    alerts = Alert.query.filter_by(alert_type='stock').order_by(Alert.created_at.desc()).limit(10).all()
    if alerts:
        print(f"✓ 找到 {len(alerts)} 条库存预警记录")
        for alert in alerts[:5]:
            print(f"  - [{alert.triggered_at.strftime('%Y-%m-%d %H:%M')}] {alert.title}")
            print(f"    级别：{alert.level}, 状态：{alert.status}")
        if len(alerts) > 5:
            print(f"  ... 还有 {len(alerts) - 5} 条记录")
    else:
        print("  暂无库存预警记录")
    
    # 4. 检查通知记录
    print("\n4. 检查通知记录")
    print("-" * 70)
    notifications = Notification.query.filter_by(type='stock_alert').order_by(Notification.created_at.desc()).limit(10).all()
    if notifications:
        print(f"✓ 找到 {len(notifications)} 条库存预警通知")
        for notification in notifications[:5]:
            user = User.query.get(notification.user_id)
            status = "已读" if notification.is_read else "未读"
            print(f"  - 用户：{user.real_name if user else 'Unknown'}")
            print(f"    标题：{notification.title}")
            print(f"    状态：{status}, 时间：{notification.created_at.strftime('%Y-%m-%d %H:%M')}")
        if len(notifications) > 5:
            print(f"  ... 还有 {len(notifications) - 5} 条记录")
    else:
        print("  暂无库存预警通知记录")
    
    # 5. 当前库存预警状态
    print("\n5. 当前库存预警状态")
    print("-" * 70)
    low_stock = SparePart.query.filter_by(stock_status='low').count()
    out_stock = SparePart.query.filter_by(stock_status='out').count()
    overstocked = SparePart.query.filter_by(stock_status='overstocked').count()
    
    print(f"  低库存备件：{low_stock} 个")
    print(f"  缺货备件：{out_stock} 个")
    print(f"  超储备件：{overstocked} 个")
    
    # 显示预警备件详情
    warning_parts = SparePart.query.filter(
        SparePart.stock_status.in_(['low', 'out', 'overstocked'])
    ).limit(10).all()
    
    if warning_parts:
        print(f"\n  预警备件列表:")
        for part in warning_parts:
            status_map = {
                'low': '低库存',
                'out': '缺货',
                'overstocked': '超储'
            }
            status = status_map.get(part.stock_status, '未知')
            print(f"    - {part.part_code}: {part.name}")
            print(f"      状态：{status}, 当前库存：{part.current_stock}, "
                  f"最低：{part.min_stock}, 最高：{part.max_stock or '-'}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    
    print("\n使用说明:")
    print("1. 配置邮件服务器：访问 /system/email-config")
    print("2. 设置预警参数：访问 /system/settings")
    print("3. 查看通知：点击右上角铃铛图标或访问 /notification")
    print("4. 触发预警：修改备件库存数量，使其低于最低库存或高于最高库存")
    print("\n预警触发条件:")
    print("  - 缺货：当前库存 = 0")
    print("  - 低库存：0 < 当前库存 ≤ 最低库存")
    print("  - 超储：当前库存 ≥ 最高库存")
    print("=" * 70)
