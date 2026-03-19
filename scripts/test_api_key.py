# -*- coding: utf-8 -*-
"""
测试 API 密钥是否有效
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('SILICONFLOW_API_KEY', 'sk-ojhphrjqyigzgskcackiaixmsznscynmhydoiayelgpmmitn')

print(f"API Key: {API_KEY[:10]}...")
print(f"API Key 长度：{len(API_KEY)}")

# 测试 API 调用
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "Qwen/Qwen2.5-72B-Instruct",
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 10
}

response = requests.post(
    "https://api.siliconflow.cn/v1/chat/completions",
    headers=headers,
    json=payload
)

print(f"\n响应状态码：{response.status_code}")
print(f"响应内容：{response.text[:500]}")

if response.status_code == 200:
    print("\n✓ API 密钥有效！")
else:
    print(f"\n✗ API 调用失败：{response.status_code}")
    print(f"错误信息：{response.json()}")
