#!/usr/bin/env python
"""
检查并测试邮件配置
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.system import EmailConfig
from app.utils.email_service import EmailService

app = create_app()

with app.app_context():
    print("=" * 70)
    print("检查邮件配置并测试")
    print("=" * 70)
    
    # 获取配置
    config = EmailConfig.query.filter_by(is_active=True).first()
    
    if not config:
        print("✗ 未找到配置")
        sys.exit(1)
    
    print("\n当前配置:")
    print(f"  SMTP 服务器：{config.smtp_server}")
    print(f"  端口：{config.smtp_port}")
    print(f"  用户名：{config.username}")
    print(f"  发件人邮箱：{config.sender_email}")
    print(f"  密码长度：{len(config.password) if config.password else 0}")
    print(f"  SSL: {config.use_tls}")
    
    # 测试
    print("\n正在测试...")
    service = EmailService()
    service.config = config
    
    success, msg = service.test_connection()
    if success:
        print(f"✓ 成功：{msg}")
    else:
        print(f"✗ 失败：{msg}")
        
        # 尝试使用 587 端口
        print("\n尝试使用 587 端口...")
        config.smtp_port = 587
        config.use_tls = True
        success2, msg2 = service.test_connection()
        if success2:
            print(f"✓ 587 端口成功：{msg2}")
        else:
            print(f"✗ 587 端口也失败：{msg2}")
    
    print("=" * 70)
