#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试百度千帆多个文生图模型
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')

print('=' * 60)
print('百度千帆文生图模型测试')
print('=' * 60)
print()

print('当前配置:')
print(f'  BAIDU_API_KEY: {"已配置" if API_KEY else "未配置"}')
print()

if not API_KEY:
    print('错误: BAIDU_API_KEY 未配置')
    sys.exit(1)

# 要测试的模型列表
models_to_test = [
    "Stable-Diffusion-XL",
    "Stable-Diffusion-XL「体验」",
    "Stable-Diffusion-XL体验",
    "stable-diffusion-xl",
    "SDXL",
    "sdxl",
    "ERNIE-ViLG",
    "ernie-vilg",
    "Fuyu-8B",
    "fuyu-8b",
]

# 新的文生图 API 端点
url = "https://qianfan.baidubce.com/v2/images/generations"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 简单的测试提示词
prompt = "一个简单的工业轴承，白色背景"

print('开始测试多个模型...')
print()

for model in models_to_test:
    print(f'测试模型: {model}')
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
            print(f'✓ 模型 "{model}" 可用!')
            result = response.json()
            print(f'  响应: {result}')
            print()
            print('找到可用模型了!')
            print()
            sys.exit(0)
        elif response.status_code == 401:
            result = response.json()
            error_msg = result.get('error', {}).get('message', '未知错误')
            if 'invalid_model' in error_msg:
                print(f'✗ 模型 "{model}" 不可用')
            else:
                print(f'✗ 错误: {error_msg}')
        else:
            print(f'✗ 状态码: {response.status_code}')
            print(f'  响应: {response.text}')
        
    except Exception as e:
        print(f'✗ 异常: {e}')
    
    print()

print('所有模型测试完成，未找到可用的文生图模型')
print()
print('可能的原因:')
print('1. 需要在控制台开通文生图服务')
print('2. 需要使用不同的 API 端点')
print('3. 需要使用老版本的 API (access_token 方式)')
