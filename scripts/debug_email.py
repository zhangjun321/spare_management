#!/usr/bin/env python
"""
调试邮件发送问题
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.system import EmailConfig
from app.utils.email_service import EmailService

app = create_app()

with app.app_context():
    print("=" * 70)
    print("调试邮件发送")
    print("=" * 70)
    
    # 获取配置
    config = EmailConfig.query.filter_by(is_active=True).first()
    
    if not config:
        print("✗ 未找到配置")
        sys.exit(1)
    
    print("\n配置信息:")
    print(f"  SMTP: {config.smtp_server}:{config.smtp_port}")
    print(f"  用户名：{config.username}")
    print(f"  发件人：{config.sender_email}")
    print(f"  密码长度：{len(config.password)}")
    print(f"  SSL: {config.use_tls}")
    
    # 手动测试
    print("\n手动测试连接...")
    try:
        import smtplib
        
        if config.use_tls:
            print(f"  使用 SSL 连接到 {config.smtp_server}:{config.smtp_port}")
            server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, timeout=10)
        else:
            print(f"  连接到 {config.smtp_server}:{config.smtp_port}")
            server = smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=10)
        
        print("  ✓ 连接成功")
        
        print(f"  尝试登录...")
        server.login(config.username, config.password)
        print("  ✓ 登录成功")
        
        # 尝试发送邮件
        print("  尝试发送邮件...")
        from email.mime.text import MIMEText
        from email.header import Header
        from datetime import datetime
        
        test_html = f"""
        <html>
        <body>
            <h2>测试邮件</h2>
            <p>这是一封测试邮件</p>
            <p>发送时间：{datetime.now()}</p>
        </body>
        </html>
        """
        
        msg = MIMEText(test_html, 'html', 'utf-8')
        msg['Subject'] = Header('备件管理系统 - 测试', 'utf-8')
        msg['From'] = f"{config.sender_name} <{config.sender_email}>"
        msg['To'] = config.sender_email
        
        server.sendmail(config.sender_email, [config.sender_email], msg.as_string())
        print("  ✓ 发送成功")
        
        server.quit()
        print("  ✓ 连接已关闭")
        
        print("\n✓ 所有步骤成功！")
        
    except Exception as e:
        print(f"\n✗ 错误：{type(e).__name__}: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
    
    print("=" * 70)
