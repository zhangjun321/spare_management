# -*- coding: utf-8 -*-
"""
测试百度千帆 API 是否免费可用
"""

import os
import sys
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_qianfan_api():
    """测试百度千帆 API"""
    print("=" * 80)
    print("百度千帆 API 免费测试")
    print("=" * 80)
    
    # 检查是否有 API Key
    api_key = os.getenv('BAIDU_API_KEY', '')
    secret_key = os.getenv('BAIDU_SECRET_KEY', '')
    
    print(f"\n当前配置状态：")
    print(f"  BAIDU_API_KEY: {'已配置' if api_key else '未配置'}")
    print(f"  BAIDU_SECRET_KEY: {'已配置' if secret_key else '未配置'}")
    
    if not api_key:
        print("\n⚠️  未配置 BAIDU_API_KEY")
        print("\n如何获取百度千帆 API Key：")
        print("1. 访问百度千帆平台：https://console.bce.baidu.com/qianfan/")
        print("2. 注册/登录百度智能云账号")
        print("3. 进入应用管理，创建应用")
        print("4. 获取 API Key 和 Secret Key")
        print("5. 配置到 .env 文件中")
        return False
    
    # 尝试获取 Access Token
    print("\n正在获取 Access Token...")
    try:
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key or api_key
        }
        
        response = requests.post(token_url, params=params, timeout=10)
        result = response.json()
        
        if "access_token" in result:
            print("✓ Access Token 获取成功！")
            access_token = result["access_token"]
            print(f"  Token: {access_token[:50]}...")
            
            # 检查免费额度信息
            if "expires_in" in result:
                expires_in = result["expires_in"]
                print(f"  有效期: {expires_in} 秒 ({expires_in/3600:.1f} 小时)")
            
            # 尝试一个简单的 API 调用来测试是否免费
            print("\n正在测试简单的 API 调用...")
            test_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-128k?access_token={access_token}"
            
            test_payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": "你好"
                    }
                ]
            }
            
            test_response = requests.post(
                test_url, 
                json=test_payload, 
                timeout=10
            )
            
            test_result = test_response.json()
            
            if "error_code" in test_result:
                print(f"✗ API 调用失败")
                print(f"  错误码: {test_result.get('error_code')}")
                print(f"  错误信息: {test_result.get('error_msg')}")
                
                if test_result.get("error_code") == 18:
                    print("\n⚠️  可能是配额不足或需要付费")
                    print("\n百度千帆免费政策：")
                    print("- 新用户通常有免费额度")
                    print("- 部分模型提供永久免费调用")
                    print("- 建议访问控制台查看具体配额：https://console.bce.baidu.com/qianfan/")
                elif test_result.get("error_code") == 110:
                    print("\n⚠️  Access Token 无效或已过期")
            else:
                print("✓ API 调用成功！")
                if "result" in test_result:
                    print(f"  响应: {test_result['result'][:100]}...")
                print("\n🎉 百度千帆 API 可以正常使用！")
                return True
        
        else:
            print(f"✗ 获取 Access Token 失败")
            print(f"  错误信息: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 网络请求失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 发生错误: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_qianfan_api()
    
    print("\n" + "=" * 80)
    print("测试总结：")
    print("=" * 80)
    
    if success:
        print("✓ 百度千帆 API 可以正常使用")
    else:
        print("✗ 需要配置或检查 API Key")
        print("\n替代方案：")
        print("1. 硅基流动 API - 已配置在项目中")
        print("2. 通义万相（阿里云）")
        print("3. 腾讯混元")
        print("4. Stable Diffusion（本地部署）")
    
    print("=" * 80)
