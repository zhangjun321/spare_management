#!/usr/bin/env python
"""
测试 QQ 邮箱配置
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.system import EmailConfig
from app.utils.email_service import EmailService

app = create_app()

with app.app_context():
    print("=" * 70)
    print("测试 QQ 邮箱配置")
    print("=" * 70)
    
    # 检查数据库中的配置
    config = EmailConfig.query.filter_by(is_active=True).first()
    
    if config:
        print("\n当前配置信息:")
        print(f"  SMTP 服务器：{config.smtp_server}")
        print(f"  SMTP 端口：{config.smtp_port}")
        print(f"  用户名：{config.username}")
        print(f"  发件人邮箱：{config.sender_email}")
        print(f"  发件人名称：{config.sender_name}")
        print(f"  SSL/TLS: {'是' if config.use_tls else '否'}")
        
        # 测试连接
        print("\n正在测试连接...")
        email_service = EmailService()
        email_service.config = config
        success, message = email_service.test_connection()
        
        if success:
            print(f"✓ 连接成功：{message}")
            
            # 测试发送邮件
            print("\n正在发送测试邮件...")
            success2, message2 = email_service.test_connection(send_test_email=True)
            
            if success2:
                print(f"✓ {message2}")
            else:
                print(f"✗ 发送失败：{message2}")
        else:
            print(f"✗ 连接失败：{message}")
            print("\n建议:")
            print("1. 检查用户名是否为完整的 QQ 邮箱地址（如：41717654@qq.com）")
            print("2. 检查授权码是否正确（授权码不是登录密码）")
            print("3. 确认 QQ 邮箱已开启 SMTP 服务")
    else:
        print("✗ 未找到邮件配置，请先保存配置")
    
    print("\n" + "=" * 70)
