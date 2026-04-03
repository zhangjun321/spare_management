#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试百度千帆新格式 API Key 的多种使用方式
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')

print('=' * 60)
print('百度千帆新格式 API Key 测试')
print('=' * 60)
print()

print('当前配置:')
print(f'  BAIDU_API_KEY: {"已配置" if API_KEY else "未配置"}')
if API_KEY:
    print(f'  Key 格式: {API_KEY[:30]}...')
print()

if not API_KEY:
    print('错误: BAIDU_API_KEY 未配置')
    sys.exit(1)

# 测试方式 1: 老方式 - 获取 access_token
print('测试方式 1: 老方式 - 获取 access_token')
print('-' * 60)

url1 = "https://aip.baidubce.com/oauth/2.0/token"
params1 = {
    "grant_type": "client_credentials",
    "client_id": API_KEY,
    "client_secret": API_KEY
}

try:
    response1 = requests.post(url1, params=params1, timeout=10)
    result1 = response1.json()
    
    print(f'状态码: {response1.status_code}')
    if "access_token" in result1:
        print('成功: 获取到 access_token!')
        print(f'  Access Token: {result1["access_token"][:20]}...')
    else:
        print(f'失败: {result1}')
except Exception as e:
    print(f'错误: {e}')
print()

# 测试方式 2: 新 API 端点 - 直接使用 Bearer token
print('测试方式 2: 新 API 端点 - 直接使用 Bearer token')
print('-' * 60)

url2 = "https://qianfan.baidubce.com/v2/chat/completions"

headers2 = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload2 = {
    "model": "ernie-4.0-turbo-8k",
    "messages": [
        {
            "role": "user",
            "content": "你好，请用一句话介绍自己"
        }
    ],
    "max_completion_tokens": 100
}

try:
    response2 = requests.post(url2, headers=headers2, json=payload2, timeout=30)
    
    print(f'状态码: {response2.status_code}')
    if response2.status_code == 200:
        result2 = response2.json()
        print('成功!')
        content = result2.get('choices', [{}])[0].get('message', {}).get('content', '')
        if content:
            print(f'  回复: {content}')
    else:
        print(f'失败: {response2.text}')
except Exception as e:
    print(f'错误: {e}')
print()

# 测试方式 3: 尝试文生图 API
print('测试方式 3: 尝试文生图 API')
print('-' * 60)

# 文心一格文生图 API
url3 = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl"

# 先尝试获取 access_token
print('先获取 access_token...')
try:
    response_token = requests.post(url1, params=params1, timeout=10)
    result_token = response_token.json()
    
    if "access_token" in result_token:
        access_token = result_token["access_token"]
        print(f'成功获取 access_token')
        
        # 测试文生图
        url3_with_token = f"{url3}?access_token={access_token}"
        
        headers3 = {
            "Content-Type": "application/json"
        }
        
        payload3 = {
            "prompt": "一个工业轴承，金属材质，白色背景，专业摄影",
            "size": "1024x1024",
            "num": 1,
            "style": "photographic"
        }
        
        print('正在调用文生图 API...')
        response3 = requests.post(url3_with_token, headers=headers3, json=payload3, timeout=60)
        
        print(f'状态码: {response3.status_code}')
        if response3.status_code == 200:
            result3 = response3.json()
            print(f'响应: {result3}')
            if 'data' in result3 and len(result3['data']) > 0:
                print('成功! 图片已生成')
                image_url = result3['data'][0].get('image', '')
                if image_url:
                    print(f'图片 URL: {image_url}')
        else:
            print(f'失败: {response3.text}')
    else:
        print(f'无法获取 access_token: {result_token}')
        
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('测试完成')
print('=' * 60)
