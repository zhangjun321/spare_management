# -*- coding: utf-8 -*-
"""
测试百度 API Key 是否支持文生图功能
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# 使用您提供的 API Key
API_KEY = "bce-v3/ALTAK-EVlLy1mZSq6rcJVi45qjo/ddb0f76edd018597420cfcee1dc32b50db3a1664"
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

print("="*80)
print("测试百度 API Key 文生图功能")
print("="*80)
print(f"\nAPI Key: {API_KEY[:30]}...")
print(f"Secret Key: {SECRET_KEY[:20] + '...' if SECRET_KEY and len(SECRET_KEY) > 20 else '未配置'}")
print("="*80)

# 步骤 1：获取 Access Token
print("\n【步骤 1】获取 Access Token...")

url = "https://aip.baidubce.com/oauth/2.0/token"
params = {
    "grant_type": "client_credentials",
    "client_id": API_KEY,
    "client_secret": SECRET_KEY if SECRET_KEY else API_KEY
}

try:
    response = requests.post(url, params=params, timeout=10)
    result = response.json()
    
    if "access_token" in result:
        access_token = result["access_token"]
        print(f"✅ Access Token 获取成功：{access_token[:30]}...")
    else:
        print(f"❌ Access Token 获取失败：{result}")
        print("\n可能原因：")
        print("1. Secret Key 未配置或不正确")
        print("2. API Key 和 Secret Key 不配对")
        print("3. API Key 权限不足")
        exit()
except Exception as e:
    print(f"❌ 发生异常：{str(e)}")
    exit()

# 步骤 2：测试文本生成 API
print("\n【步骤 2】测试文本生成 API...")

text_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
text_payload = {
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    "max_output_tokens": 50
}

try:
    text_response = requests.post(text_url, json=text_payload, timeout=30)
    
    if text_response.status_code == 200:
        text_result = text_response.json()
        if 'result' in text_result:
            print(f"✅ 文本生成 API 正常")
            print(f"   回复：{text_result['result'][:50]}...")
        else:
            print(f"⚠️ 文本生成 API 返回异常：{text_result}")
    else:
        print(f"❌ 文本生成 API 失败：{text_response.status_code}")
        print(f"   错误：{text_response.text[:200]}")
except Exception as e:
    print(f"❌ 文本生成测试异常：{str(e)}")

# 步骤 3：测试文心一格（文生图）API
print("\n【步骤 3】测试文心一格（文生图）API...")

# 文心一格 API 端点
image_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl?access_token={access_token}"

image_payload = {
    "prompt": "一个红色的苹果，高清实拍，白色背景",
    "size": "1024x1024",
    "num": 1
}

try:
    image_response = requests.post(image_url, json=image_payload, timeout=60)
    
    print(f"\n响应状态码：{image_response.status_code}")
    
    if image_response.status_code == 200:
        image_result = image_response.json()
        
        if 'data' in image_result and len(image_result['data']) > 0:
            print(f"✅ 文心一格 API 支持！")
            print(f"   图片数量：{len(image_result['data'])}")
            if 'image' in image_result['data'][0]:
                print(f"   图片 URL: {image_result['data'][0]['image'][:50]}...")
            print(f"\n🎉 恭喜！您的 API Key 支持文生图功能！")
        else:
            print(f"⚠️ API 返回数据异常：{image_result}")
            print(f"\n可能原因：")
            print("1. 该 API Key 没有文生图权限")
            print("2. 需要单独开通文心一格服务")
            
    elif image_response.status_code == 400:
        error_result = image_response.json()
        print(f"❌ 请求参数错误：{error_result}")
        
    elif image_response.status_code == 401:
        print(f"❌ 认证失败：权限不足")
        print(f"\n可能原因：")
        print("1. API Key 没有文生图权限")
        print("2. 需要开通文心一格服务")
        print("3. 免费额度已用尽")
        
    elif image_response.status_code == 402:
        print(f"❌ 余额不足或免费额度用尽")
        print(f"\n建议：")
        print("1. 检查账户余额")
        print("2. 查看免费额度使用情况")
        print("3. 4 月 1 日后全面免费")
        
    elif image_response.status_code == 403:
        print(f"❌ 禁止访问：权限不足")
        print(f"\n可能原因：")
        print("1. API Key 没有文生图权限")
        print("2. 需要企业认证")
        print("3. 服务未开通")
        
    else:
        print(f"❌ 文心一格 API 失败：{image_response.status_code}")
        print(f"   错误信息：{image_response.text[:300]}")
        
except Exception as e:
    print(f"❌ 文生图测试异常：{str(e)}")

# 步骤 4：检查服务权限
print("\n【步骤 4】检查服务权限...")

check_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/models?access_token={access_token}"

try:
    check_response = requests.get(check_url, timeout=10)
    
    if check_response.status_code == 200:
        services = check_response.json()
        print(f"✅ 可用服务列表：")
        
        if isinstance(services, list):
            for service in services:
                service_name = service.get('name', 'Unknown')
                if 'text2image' in service_name or 'image' in service_name.lower():
                    print(f"   - {service_name} ✅")
        else:
            print(f"   服务信息：{services}")
    else:
        print(f"⚠️ 无法获取服务列表：{check_response.status_code}")
        
except Exception as e:
    print(f"⚠️ 服务检查异常：{str(e)}")

print("\n" + "="*80)
print("测试完成！")
print("="*80)

# 总结
print("\n📊 测试结果总结：")
print("-" * 80)
if 'text_result' in locals() and text_result:
    print("✅ 文本生成：支持")
else:
    print("❌ 文本生成：不支持")

if 'image_result' in locals() and image_result and 'data' in image_result:
    print("✅ 文生图功能：支持")
    print("\n🎉 您的 API Key 支持文生图功能！可以用于生成备件图片！")
else:
    print("❌ 文生图功能：不支持或权限不足")
    print("\n💡 建议：")
    print("1. 访问千帆平台检查服务开通情况")
    print("2. 确认是否需要单独开通文心一格服务")
    print("3. 4 月 1 日后全面免费，届时权限会更宽松")
    print("4. 或者使用快手 Kolors 作为替代方案")

print("="*80)
