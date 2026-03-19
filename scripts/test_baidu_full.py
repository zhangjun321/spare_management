# -*- coding: utf-8 -*-
"""
全面测试百度文心一言 API 文生图功能
尝试多种认证方式和 API 端点
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('BAIDU_API_KEY', '')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

print("="*80)
print("百度文心一言 API - 文生图功能全面测试")
print("="*80)
print(f"\nAPI Key: {API_KEY[:30]}...")
print(f"Secret Key: {SECRET_KEY if SECRET_KEY else '未配置'}")
print("="*80)


def try_auth_method(client_id, client_secret, method_name):
    """尝试认证方法"""
    print(f"\n【测试】{method_name}...")
    
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(url, params=params, timeout=10)
        result = response.json()
        
        if "access_token" in result:
            print(f"  ✅ 认证成功！Token: {result['access_token'][:30]}...")
            return result["access_token"]
        else:
            print(f"  ❌ 认证失败：{result}")
            return None
            
    except Exception as e:
        print(f"  ❌ 异常：{str(e)}")
        return None


def try_image_generation(access_token, api_type):
    """尝试文生图 API"""
    print(f"\n【测试】{api_type} 文生图...")
    
    # 不同的 API 端点
    endpoints = [
        # 方式 1: 标准文心一格
        f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl?access_token={access_token}",
        # 方式 2: ernie-vilg-v2
        f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/ernie_vilg_v2?access_token={access_token}",
        # 方式 3: 旧版 API
        f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/image_generation?access_token={access_token}",
    ]
    
    for endpoint in endpoints:
        print(f"  尝试端点：{endpoint.split('?')[0].split('/')[-1]}...")
        
        payload = {
            "prompt": "一个红色的苹果，高清实拍，白色背景",
            "size": "1024x1024",
            "num": 1
        }
        
        try:
            response = requests.post(endpoint, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and len(result.get('data', [])) > 0:
                    print(f"  ✅ 成功！获取到图片")
                    return True
                elif 'result' in result:
                    print(f"  ⚠️ 返回文本：{result['result'][:50]}...")
                else:
                    print(f"  ⚠️ 返回：{result}")
            elif response.status_code == 401:
                print(f"  ❌ 权限不足 (401)")
            elif response.status_code == 403:
                print(f"  ❌ 禁止访问 (403)")
            elif response.status_code == 402:
                print(f"  ❌ 余额不足 (402)")
            else:
                print(f"  ❌ 失败 ({response.status_code}): {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ 异常：{str(e)}")
    
    return False


# 测试 1: 使用 API Key 作为 Secret Key
print("\n" + "="*80)
print("【测试组 1】使用 API Key 作为 client_secret")
print("="*80)
token1 = try_auth_method(API_KEY, API_KEY, "API Key = Secret Key")
if token1:
    try_image_generation(token1, "方法1")

# 测试 2: 使用空 Secret Key
if SECRET_KEY:
    print("\n" + "="*80)
    print("【测试组 2】使用配置的 Secret Key")
    print("="*80)
    token2 = try_auth_method(API_KEY, SECRET_KEY, "配置 Secret Key")
    if token2:
        try_image_generation(token2, "方法2")
else:
    print("\n" + "="*80)
    print("【测试组 2】跳过（Secret Key 未配置）")
    print("="*80)

# 测试 3: 尝试不同的认证端点
print("\n" + "="*80)
print("【测试组 3】尝试千帆平台认证")
print("="*80)

auth_urls = [
    ("https://qianfan.baidubce.com/oauth/2.0/token", "千帆平台"),
    ("https://aip.baidubce.com/oauth/2.0/token", "标准平台"),
]

for auth_url, name in auth_urls:
    print(f"\n尝试 {name}...")
    
    # 使用 API Key 作为 client_id 和 client_secret
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": API_KEY
    }
    
    try:
        response = requests.post(auth_url, params=params, timeout=10)
        result = response.json()
        
        if "access_token" in result:
            print(f"  ✅ {name} 认证成功！")
            token = result["access_token"]
            
            # 尝试文生图
            success = try_image_generation(token, name)
            if success:
                print(f"\n🎉 恭喜！{name} 支持文生图！")
                break
        else:
            print(f"  ❌ {name} 认证失败：{result}")
            
    except Exception as e:
        print(f"  ❌ {name} 异常：{str(e)}")

# 测试 4: 检查是否有其他可用的文生图服务
print("\n" + "="*80)
print("【测试组 4】检查可用模型列表")
print("="*80)

# 先尝试获取 token
url = "https://aip.baidubce.com/oauth/2.0/token"
params = {
    "grant_type": "client_credentials",
    "client_id": API_KEY,
    "client_secret": API_KEY
}

try:
    response = requests.post(url, params=params, timeout=10)
    result = response.json()
    
    if "access_token" in result:
        token = result["access_token"]
        
        # 尝试获取模型列表
        models_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/models?access_token={token}"
        
        try:
            models_response = requests.get(models_url, timeout=10)
            
            if models_response.status_code == 200:
                models = models_response.json()
                print(f"\n可用服务/模型：")
                print(models)
            else:
                print(f"获取模型列表失败：{models_response.status_code}")
                
        except Exception as e:
            print(f"获取模型列表异常：{str(e)}")
            
except Exception as e:
    print(f"认证异常：{str(e)}")

print("\n" + "="*80)
print("测试完成！")
print("="*80)

print("\n📋 总结：")
print("-"*80)
print("如果以上测试都失败，可能的原因：")
print("1. API Key 没有开通文生图服务权限")
print("2. 需要在千帆平台单独开通文心一格服务")
print("3. 需要完成企业认证")
print("4. 账户状态异常")
print("\n建议解决方案：")
print("1. 访问 https://console.bce.baidu.com/qianfan/")
print("2. 检查应用是否开通了文心一格/SD-XL 服务")
print("3. 获取配对的 Secret Key")
print("4. 或者等待 4 月 1 日全面免费后重试")
print("="*80)
