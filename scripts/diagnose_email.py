#!/usr/bin/env python
"""
详细诊断 QQ 邮箱连接问题
"""

import smtplib
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# QQ 邮箱配置
smtp_server = 'smtp.qq.com'
smtp_port = 465
username = '41717654@qq.com'
password = 'sggalhiahadabggc'  # 授权码

print("=" * 70)
print("QQ 邮箱连接诊断")
print("=" * 70)

print(f"\n配置信息:")
print(f"  SMTP 服务器：{smtp_server}:{smtp_port}")
print(f"  用户名：{username}")
print(f"  密码：{'*' * len(password)}")

# 步骤 1: 测试基本连接
print("\n[步骤 1] 测试基本网络连接...")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex((smtp_server, smtp_port))
    if result == 0:
        print("  ✓ 网络连接成功")
    else:
        print(f"  ✗ 网络连接失败，错误码：{result}")
    sock.close()
except Exception as e:
    print(f"  ✗ 连接异常：{str(e)}")

# 步骤 2: 尝试 SMTP 连接
print("\n[步骤 2] 尝试 SMTP SSL 连接...")
try:
    server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
    print("  ✓ SMTP 连接建立成功")
    
    # 步骤 3: 尝试登录
    print("\n[步骤 3] 尝试登录...")
    try:
        server.login(username, password)
        print("  ✓ 登录成功！")
        
        # 尝试发送邮件
        print("\n[步骤 4] 尝试发送测试邮件...")
        try:
            from email.mime.text import MIMEText
            from email.header import Header
            
            msg = MIMEText('这是一封测试邮件', 'plain', 'utf-8')
            msg['Subject'] = Header('邮件测试', 'utf-8')
            msg['From'] = f'{username}'
            msg['To'] = username
            
            server.sendmail(username, [username], msg.as_string())
            print("  ✓ 邮件发送成功！")
            print("\n" + "=" * 70)
            print("恭喜！配置完全正确，请检查 QQ 邮箱收件箱")
            print("=" * 70)
        except Exception as e:
            print(f"  ✗ 邮件发送失败：{str(e)}")
        
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        print("  ✗ 登录失败：认证错误")
        print("\n可能原因:")
        print("  1. 授权码不正确")
        print("  2. 授权码已过期")
        print("  3. 需要重新获取授权码")
        print("\n解决方法:")
        print("  1. 登录 QQ 邮箱网页版")
        print("  2. 设置 → 账户")
        print("  3. 确保已开启 SMTP 服务")
        print("  4. 重新生成授权码")
    except smtplib.SMTPServerDisconnected:
        print("  ✗ 登录失败：服务器断开连接")
        print("\n可能原因:")
        print("  1. QQ 邮箱 SMTP 服务未开启")
        print("  2. 网络防火墙阻止")
        print("  3. SMTP 服务器临时故障")
    except Exception as e:
        print(f"  ✗ 登录异常：{str(e)}")
        
except smtplib.SMTPConnectError as e:
    print(f"  ✗ SMTP 连接失败：{str(e)}")
    print("\n可能原因:")
    print("  1. 防火墙阻止了 465 端口")
    print("  2. SMTP 服务器地址错误")
    print("  3. 网络问题")
except Exception as e:
    print(f"  ✗ 连接异常：{str(e)}")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
