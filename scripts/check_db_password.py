import pymysql

conn = pymysql.connect(host='localhost', user='root', password='Kra@211314', database='spare_parts_db')
cur = conn.cursor()

# 获取配置
cur.execute('SELECT id, username, password, sender_email FROM email_config WHERE is_active=1')
r = cur.fetchone()

print("=" * 70)
print("数据库中的配置")
print("=" * 70)
print(f"ID: {r[0]}")
print(f"用户名：{r[1]}")
print(f"密码：'{r[2]}' (长度：{len(r[2])})")
print(f"发件人邮箱：{r[3]}")

# 测试登录
import smtplib
print("\n使用数据库密码测试登录...")
try:
    server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=30)
    server.login(r[1], r[2])
    print("✓ 登录成功")
    server.quit()
except Exception as e:
    print(f"✗ 登录失败：{e}")

conn.close()
print("=" * 70)
