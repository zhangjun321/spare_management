#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试百度千帆 irag-1.0 文生图模型
"""

import os
import sys
import requests
import base64
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')

print('=' * 60)
print('Baidu Qianfan irag-1.0 Image Generation Test')
print('=' * 60)
print()

if not API_KEY:
    print('Error: BAIDU_API_KEY not configured')
    sys.exit(1)

print('API Key configured')
print()

url = "https://qianfan.baidubce.com/v2/images/generations"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

prompt = "一个工业轴承，金属材质，精密机械零件，圆形结构，滚珠，白色背景，专业工业产品摄影，8K高清"

print(f'Prompt: {prompt}')
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
                print(f'Image URL: {image_url}')
                print()
                print('You can open this URL in browser to see the image!')
                
                # 尝试下载图片
                output_dir = os.path.join(os.path.dirname(__file__), 'test_images')
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(output_dir, f'irag_test_{timestamp}.png')
                
                print()
                print('Downloading image...')
                img_response = requests.get(image_url, timeout=30)
                
                if img_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    print(f'Image saved to: {output_path}')
                else:
                    print(f'Failed to download: {img_response.status_code}')
            
            elif "b64_json" in image_data:
                print('Base64 encoded image found')
                
                output_dir = os.path.join(os.path.dirname(__file__), 'test_images')
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(output_dir, f'irag_test_{timestamp}.png')
                
                img_bytes = base64.b64decode(image_data["b64_json"])
                with open(output_path, 'wb') as f:
                    f.write(img_bytes)
                
                print(f'Image saved to: {output_path}')
            
            else:
                print('No image data found')
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
