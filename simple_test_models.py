#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试百度千帆文生图模型
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')

print('=' * 60)
print('Baidu Qianfan Image Model Test')
print('=' * 60)
print()

if not API_KEY:
    print('Error: BAIDU_API_KEY not configured')
    sys.exit(1)

models_to_test = [
    "Stable-Diffusion-XL",
    "stable-diffusion-xl",
    "SDXL",
]

url = "https://qianfan.baidubce.com/v2/images/generations"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

prompt = "a simple industrial bearing, white background"

print('Testing multiple models...')
print()

for model in models_to_test:
    print(f'Testing model: {model}')
    print('-' * 40)
    
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": "512x512"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f'Success: Model "{model}" works!')
            result = response.json()
            print(f'Response: {result}')
            print()
            print('Found working model!')
            print()
            sys.exit(0)
        else:
            print(f'Status: {response.status_code}')
            print(f'Response: {response.text}')
        
    except Exception as e:
        print(f'Error: {e}')
    
    print()

print('All models tested, no working image model found')
