#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试百度千帆 irag-1.0 文生图模型 - 短提示词
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')

print('=' * 60)
print('Baidu Qianfan irag-1.0 Image Test (Short Prompt)')
print('=' * 60)
print()

if not API_KEY:
    print('Error: BAIDU_API_KEY not configured')
    sys.exit(1)

url = "https://qianfan.baidubce.com/v2/images/generations"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 短提示词 - 不超过 220 字符
prompt = "一个工业轴承，白色背景"

print(f'Prompt: {prompt}')
print(f'Length: {len(prompt)} chars')
print()

payload = {
    "model": "irag-1.0",
    "prompt": prompt
}

print('Calling API...')
print()

try:
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print(f'Response: {result}')
        print()
        
        if "data" in result and len(result["data"]) > 0:
            print('Success! Image generated!')
            
            image_data = result["data"][0]
            
            if "url" in image_data:
                image_url = image_data["url"]
                print()
                print('=' * 60)
                print('Image URL:')
                print(image_url)
                print('=' * 60)
                print()
                print('Open this URL in browser to see the image!')
            else:
                print('No URL found')
        else:
            print('No data in response')
    else:
        print(f'Error: {response.text}')
        
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('Test completed')
print('=' * 60)
