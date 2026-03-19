# -*- coding: utf-8 -*-
"""
测试文心一言 API 认证
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

print("="*80)
print("文心一言 API 认证测试")
print("="*80)

print(f"\nAPI Key: {API_KEY[:20]}...")
print(f"Secret Key: {SECRET_KEY[:20] + '...' if SECRET_KEY and len(SECRET_KEY) > 20 else '未配置'}")

if not SECRET_KEY:
    print("\n⚠️ 警告：BAIDU_SECRET_KEY 未配置")
    print("请在 .env 文件中添加 BAIDU_SECRET_KEY")
    print("\n获取方式：")
    print("1. 访问 https://console.bce.baidu.com/aiplatform/")
    print("2. 进入应用管理")
    print("3. 找到您的文心一言应用")
    print("4. 复制 Secret Key")
    exit()

print("\n正在获取 Access Token...")

url = "https://aip.baidubce.com/oauth/2.0/token"
params = {
    "grant_type": "client_credentials",
    "client_id": API_KEY,
    "client_secret": SECRET_KEY
}

try:
    response = requests.post(url, params=params, timeout=10)
    result = response.json()
    
    if "access_token" in result:
        print(f"\n✅ 认证成功！")
        print(f"Access Token: {result['access_token'][:30]}...")
        print(f"Expires In: {result.get('expires_in', 'N/A')} 秒")
        
        # 测试文本生成
        print("\n正在测试文本生成...")
        token = result['access_token']
        test_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={token}"
        
        test_payload = {
            "messages": [{"role": "user", "content": "你好"}],
            "max_output_tokens": 10
        }
        
        test_response = requests.post(test_url, json=test_payload)
        if test_response.status_code == 200:
            print("✅ 文本生成 API 正常")
        else:
            print(f"⚠️ 文本生成 API 异常：{test_response.status_code}")
        
        # 测试图片生成
        print("\n正在测试图片生成 API...")
        img_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl?access_token={token}"
        
        img_payload = {
            "prompt": "测试",
            "size": "1024x1024",
            "num": 1
        }
        
        img_response = requests.post(img_url, json=img_payload)
        if img_response.status_code == 200:
            img_result = img_response.json()
            if 'data' in img_result:
                print("✅ 图片生成 API 正常！可以开始生成备件图片")
            else:
                print(f"⚠️ 图片生成 API 返回数据异常：{img_result}")
        else:
            print(f"❌ 图片生成 API 异常：{img_response.status_code}")
            print(f"错误信息：{img_response.text[:200]}")
        
    else:
        print(f"\n❌ 认证失败！")
        print(f"错误：{result}")
        print("\n可能的原因：")
        print("1. Secret Key 不正确")
        print("2. API Key 和 Secret Key 不配对")
        print("3. 应用权限不足")
        
except Exception as e:
    print(f"\n❌ 发生异常：{str(e)}")

print("\n" + "="*80)
