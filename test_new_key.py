#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新的百度千帆 API Key
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')

print('=' * 60)
print('New Baidu Qianfan API Key Test')
print('=' * 60)
print()

if not API_KEY:
    print('Error: BAIDU_API_KEY not configured')
    sys.exit(1)

print('API Key configured')
print()

# 测试 1: 文本对话
print('Test 1: Chat Completion')
print('-' * 40)

chat_url = "https://qianfan.baidubce.com/v2/chat/completions"

chat_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

chat_payload = {
    "model": "ernie-4.0-turbo-8k",
    "messages": [
        {
            "role": "user",
            "content": "你好，请介绍一下自己"
        }
    ],
    "max_completion_tokens": 100
}

try:
    chat_response = requests.post(chat_url, headers=chat_headers, json=chat_payload, timeout=30)
    
    if chat_response.status_code == 200:
        chat_result = chat_response.json()
        print('Chat Success!')
        content = chat_result.get('choices', [{}])[0].get('message', {}).get('content', '')
        if content:
            print(f'Response: {content}')
    else:
        print(f'Chat Error: {chat_response.status_code}')
        print(f'Response: {chat_response.text}')
        
except Exception as e:
    print(f'Chat Error: {e}')

print()

# 测试 2: 文生图
print('Test 2: Image Generation (irag-1.0)')
print('-' * 40)

image_url = "https://qianfan.baidubce.com/v2/images/generations"

image_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

image_payload = {
    "model": "irag-1.0",
    "prompt": "一个工业轴承，白色背景"
}

try:
    image_response = requests.post(image_url, headers=image_headers, json=image_payload, timeout=120)
    
    print(f'Image Status: {image_response.status_code}')
    
    if image_response.status_code == 200:
        image_result = image_response.json()
        print(f'Image Response: {image_result}')
        
        if "data" in image_result and len(image_result["data"]) > 0:
            print('Image Generation Success!')
            
            image_data = image_result["data"][0]
            
            if "url" in image_data:
                print()
                print('=' * 60)
                print('Image URL:')
                print(image_data["url"])
                print('=' * 60)
                print()
                print('Open this URL in browser to see the image!')
    else:
        print(f'Image Error: {image_response.text}')
        
except Exception as e:
    print(f'Image Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('Test completed')
print('=' * 60)
