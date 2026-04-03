#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试百度文心一言 API Key 是否有效
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

print('=' * 60)
print('百度文心一言 API 简单测试')
print('=' * 60)
print()

print('当前配置状态:')
print(f'  BAIDU_API_KEY: {"已配置" if API_KEY else "未配置"}')
print(f'  BAIDU_SECRET_KEY: {"已配置" if SECRET_KEY else "未配置"}')
print()

if not API_KEY:
    print('错误: BAIDU_API_KEY 未配置')
    sys.exit(1)

print('正在获取 Access Token...')
print()

# 尝试获取 access token
url = "https://aip.baidubce.com/oauth/2.0/token"

# 如果没有 SECRET_KEY，尝试使用 API_KEY 作为 SECRET_KEY
if not SECRET_KEY:
    print('提示: BAIDU_SECRET_KEY 未配置，尝试使用 API_KEY 作为 Secret Key')
    SECRET_KEY = API_KEY
    print()

params = {
    "grant_type": "client_credentials",
    "client_id": API_KEY,
    "client_secret": SECRET_KEY
}

try:
    response = requests.post(url, params=params, timeout=10)
    result = response.json()
    
    print('API 响应:')
    print(f'  状态码: {response.status_code}')
    print(f'  响应内容: {result}')
    print()
    
    if "access_token" in result:
        print('成功: Access Token 获取成功!')
        print(f'  Access Token: {result["access_token"][:20]}...')
        print()
        print('API Key 有效!')
        sys.exit(0)
    else:
        print('失败: 无法获取 Access Token')
        if "error" in result:
            print(f'  错误: {result.get("error")}')
        if "error_description" in result:
            print(f'  描述: {result.get("error_description")}')
        print()
        print('提示: 可能需要配对的 Secret Key')
        print('请在百度智能云控制台 - 应用管理中查看完整的凭证')
        sys.exit(1)
        
except Exception as e:
    print(f'发生错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
