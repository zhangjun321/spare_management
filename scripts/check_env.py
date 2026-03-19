#!/usr/bin/env python
"""
检查环境变量和数据库连接
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

print("=" * 70)
print("环境变量检查")
print("=" * 70)
print(f"MYSQL_USER: {os.environ.get('MYSQL_USER')}")
print(f"MYSQL_PASSWORD: {os.environ.get('MYSQL_PASSWORD')}")
print(f"MYSQL_HOST: {os.environ.get('MYSQL_HOST')}")
print(f"MYSQL_DATABASE: {os.environ.get('MYSQL_DATABASE')}")

# 测试数据库连接
import pymysql

try:
    conn = pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'spare_parts_db')
    )
    print("\n✓ 数据库连接成功")
    
    cur = conn.cursor()
    cur.execute('SELECT username, password FROM email_config WHERE id=6')
    r = cur.fetchone()
    print(f"\n数据库中的配置:")
    print(f"  用户名：{r[0]}")
    print(f"  密码：{r[1]}")
    
    # 测试邮件登录
    import smtplib
    server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=30)
    server.login(r[0], r[1])
    print("\n✓ 邮件登录成功")
    server.quit()
    
    conn.close()
    
except Exception as e:
    print(f"\n✗ 错误：{e}")

print("=" * 70)
