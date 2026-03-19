import smtplib
import traceback

print("=" * 70)
print("测试 QQ 邮箱登录")
print("=" * 70)

config = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 465,
    'username': '41717654@qq.com',
    'password': 'sggalhiahadabggc'
}

print(f"\n配置:")
print(f"  服务器：{config['smtp_server']}:{config['smtp_port']}")
print(f"  用户名：{config['username']}")
print(f"  密码：{'*' * len(config['password'])} ({len(config['password'])} 位)")

# 测试 1: 直接登录
print("\n[测试 1] 尝试登录...")
try:
    server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], timeout=30)
    print("  ✓ 连接成功")
    
    server.login(config['username'], config['password'])
    print("  ✓ 登录成功")
    
    server.quit()
    print("  ✓ 测试完成")
    
except Exception as e:
    print(f"  ✗ 失败：{type(e).__name__}: {e}")
    print("\n详细错误:")
    traceback.print_exc()

# 测试 2: 使用 EHLO
print("\n[测试 2] 使用 EHLO 后登录...")
try:
    server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], timeout=30)
    print("  ✓ 连接成功")
    
    # 发送 EHLO
    code, msg = server.ehlo()
    print(f"  EHLO 响应：{code} {msg.decode()[:100]}")
    
    server.login(config['username'], config['password'])
    print("  ✓ 登录成功")
    
    server.quit()
    print("  ✓ 测试完成")
    
except Exception as e:
    print(f"  ✗ 失败：{type(e).__name__}: {e}")

print("\n" + "=" * 70)
