import smtplib
from email.mime.text import MIMEText
from email.header import Header

print("测试 QQ 邮箱...")

config = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 465,
    'username': '41717654@qq.com',
    'password': 'sggalhiahadabggc'
}

try:
    print(f"连接 {config['smtp_server']}:{config['smtp_port']}...")
    server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], timeout=10)
    print("✓ 连接成功")
    
    print(f"登录 {config['username']}...")
    server.login(config['username'], config['password'])
    print("✓ 登录成功")
    
    print("发送测试邮件...")
    msg = MIMEText('测试邮件', 'plain', 'utf-8')
    msg['Subject'] = Header('测试', 'utf-8')
    msg['From'] = config['username']
    msg['To'] = config['username']
    
    server.sendmail(config['username'], [config['username']], msg.as_string())
    print("✓ 发送成功")
    
    server.quit()
    print("完成")
    
except Exception as e:
    print(f"✗ 错误：{type(e).__name__}: {e}")
