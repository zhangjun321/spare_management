# -*- coding: utf-8 -*-
"""
测试百度文心一言 API
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 文心一言 API 配置
# 需要先在百度智能云创建应用获取 API Key 和 Secret Key
API_KEY = os.getenv('BAIDU_API_KEY', '')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

# 获取 access token
def get_access_token():
    """获取文心一言 API 的 access token"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    
    response = requests.post(url, params=params)
    return response.json().get("access_token")


def test_wenxin_api():
    """测试文心一言 API"""
    print("="*70)
    print("百度文心一言 API 测试")
    print("="*70)
    
    if not API_KEY or not SECRET_KEY:
        print("\n✗ 错误：请先配置 BAIDU_API_KEY 和 BAIDU_SECRET_KEY")
        print("\n获取方式：")
        print("1. 访问 https://console.bce.baidu.com/")
        print("2. 创建文心一言应用")
        print("3. 获取 API Key 和 Secret Key")
        print("4. 添加到 .env 文件：")
        print("   BAIDU_API_KEY=your_api_key")
        print("   BAIDU_SECRET_KEY=your_secret_key")
        return False
    
    try:
        # 获取 access token
        print("\n正在获取 access token...")
        access_token = get_access_token()
        
        if not access_token:
            print("✗ 获取 access token 失败")
            return False
        
        print(f"✓ 获取 access token 成功：{access_token[:20]}...")
        
        # 调用文心一言 API
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "你好，请介绍一下你自己"
                }
            ],
            "max_output_tokens": 100
        }
        
        print("\n正在调用文心一言 API...")
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ API 调用成功！")
            print(f"\n回复内容：{result.get('result', '')}")
            return True
        else:
            print(f"\n✗ API 调用失败：{response.text}")
            return False
            
    except Exception as e:
        print(f"\n✗ 发生错误：{str(e)}")
        return False


if __name__ == "__main__":
    success = test_wenxin_api()
    if success:
        print("\n" + "="*70)
        print("测试通过！可以开始使用文心一言生成备件数据")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("测试失败，请检查 API 密钥配置")
        print("="*70)
