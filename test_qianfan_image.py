#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试百度千帆新格式文生图 API
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
print('百度千帆新格式文生图 API 测试')
print('=' * 60)
print()

print('当前配置:')
print(f'  BAIDU_API_KEY: {"已配置" if API_KEY else "未配置"}')
print()

if not API_KEY:
    print('错误: BAIDU_API_KEY 未配置')
    sys.exit(1)

# 新的文生图 API 端点
url = "https://qianfan.baidubce.com/v2/images/generations"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 测试提示词 - 工业轴承
prompt = "一个工业轴承，金属材质，精密机械零件，圆形结构，滚珠，白色渐变背景，专业工业产品摄影，8K 高清，细节清晰"

payload = {
    "model": "Stable-Diffusion-XL",
    "prompt": prompt,
    "n": 1,
    "size": "1024x1024",
    "quality": "hd"
}

print('正在调用文生图 API...')
print(f'提示词: {prompt[:60]}...')
print()

try:
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    
    print(f'状态码: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print(f'响应: {result}')
        print()
        
        if "data" in result and len(result["data"]) > 0:
            print('成功! 图片已生成')
            
            # 获取图片数据
            image_data = result["data"][0]
            
            # 检查是否有 base64 编码的图片
            if "b64_json" in image_data:
                print('检测到 base64 编码的图片')
                
                # 保存图片
                output_dir = os.path.join(os.path.dirname(__file__), 'test_images')
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(output_dir, f'test_image_{timestamp}.png')
                
                # 解码 base64 并保存
                img_bytes = base64.b64decode(image_data["b64_json"])
                with open(output_path, 'wb') as f:
                    f.write(img_bytes)
                
                print(f'图片已保存到: {output_path}')
            
            # 检查是否有 URL
            elif "url" in image_data:
                print('检测到图片 URL')
                image_url = image_data["url"]
                print(f'图片 URL: {image_url}')
                
                # 下载图片
                output_dir = os.path.join(os.path.dirname(__file__), 'test_images')
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(output_dir, f'test_image_{timestamp}.png')
                
                print('正在下载图片...')
                img_response = requests.get(image_url, timeout=30)
                
                if img_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    print(f'图片已保存到: {output_path}')
                else:
                    print(f'下载图片失败: {img_response.status_code}')
            
            else:
                print('未找到图片数据')
                print(f'完整响应: {result}')
        else:
            print('API 返回数据格式不正确')
    else:
        print(f'失败: {response.text}')
        
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('测试完成')
print('=' * 60)
