"""
使用百度千帆 AI 生成入库管理轮播图
生成 6 张 16K 超高清现代化入库管理相关图片
"""

import requests
import base64
import json
import os
from pathlib import Path

# 百度千帆 API 配置
API_KEY = 'YOUR_API_KEY'  # 请替换为您的百度千帆 API Key
SECRET_KEY = 'YOUR_SECRET_KEY'  # 请替换为您的百度千帆 Secret Key

# 图片保存目录
SAVE_DIR = Path('d:/Trae/spare_management/app/static/images/carousel')
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# 6 张图片的提示词
prompts = [
    {
        'filename': 'inbound_01.jpg',
        'title': '物资到货接收',
        'prompt': '''Ultra high resolution photograph of modern warehouse receiving dock, 
delivery truck backing up to loading bay, workers in safety vests 
preparing to unload goods with professional equipment, 
bright natural daylight streaming through large windows, 
clean organized logistics facility, blue and white color scheme, 
professional industrial photography, hyper realistic, 
extremely detailed, maximum sharpness, 
wide angle view, crystal clear, vibrant but comfortable colors, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, professional logistics photography, 
bright and fresh atmosphere, visually pleasing, 8k resolution, 
modern warehouse interior, professional equipment, organized workflow'''
    },
    {
        'filename': 'inbound_02.jpg',
        'title': '严格质量检验',
        'prompt': '''Ultra detailed photograph of professional quality inspection area 
in modern warehouse, inspector in clean uniform using precision 
measuring instruments to check incoming goods, digital tablet 
displaying quality standards, bright LED lighting, 
white and light blue color palette, clean organized workspace, 
professional photography, maximum sharpness, hyper realistic, 
no gradient, no text, pure scene, 
commercial quality, best quality, ultra detailed, crystal clear, 
fresh and bright atmosphere, visually comfortable, professional QC process,
8k resolution, modern quality control equipment'''
    },
    {
        'filename': 'inbound_03.jpg',
        'title': '智能条码扫描',
        'prompt': '''Ultra high resolution photograph of warehouse worker using 
professional handheld barcode scanner to scan incoming goods, 
close-up shot showing scanner beam reading barcode label on 
cardboard box, modern warehouse background with organized shelving, 
bright natural lighting, blue and white uniform, 
professional industrial photography, hyper realistic, 
extremely detailed, maximum sharpness, 
vibrant but comfortable colors, clear focus, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, crystal clear, 
modern technology, visually pleasing, bright atmosphere,
8k resolution, professional scanning equipment'''
    },
    {
        'filename': 'inbound_04.jpg',
        'title': '规范上架流程',
        'prompt': '''Ultra detailed photograph of warehouse storage process, 
professional forklift operator placing goods onto high-bay racking 
system, organized warehouse interior with multiple levels of shelving, 
pallets with neatly stacked boxes, bright LED lighting, 
blue and gray color scheme, clean industrial architecture, 
professional photography, maximum sharpness, hyper realistic, 
no gradient, no text, pure scene, 
commercial quality, best quality, ultra detailed, crystal clear, 
fresh and bright atmosphere, visually comfortable, 
modern logistics facility, professional operation,
8k resolution, professional forklift, organized storage'''
    },
    {
        'filename': 'inbound_05.jpg',
        'title': '入库单据管理',
        'prompt': '''Ultra high resolution photograph of modern warehouse office area, 
administrator working at clean desk with dual monitors displaying 
warehouse management system interface, digital tablet showing 
inbound order documents, bright natural lighting through large windows, 
white and light blue color palette, organized workspace with 
filing cabinets and office plants, professional photography, 
hyper realistic, extremely detailed, maximum sharpness, 
vibrant but comfortable colors, 
no gradient, no text, pure office scene, 
best quality, ultra detailed, crystal clear, 
modern digital workflow, visually pleasing, bright atmosphere,
8k resolution, modern office equipment, dual monitor setup'''
    },
    {
        'filename': 'inbound_06.jpg',
        'title': '自动化分拣系统',
        'prompt': '''Ultra detailed photograph of automated conveyor belt system 
in modern warehouse, packages being sorted automatically by 
intelligent sorting machinery, robotic arms and automated guided 
vehicles working in coordination, bright industrial lighting, 
blue and silver color scheme, futuristic logistics technology, 
professional industrial photography, hyper realistic, 
extremely detailed, maximum sharpness, 
vibrant colors, clear focus, 
no gradient, no text, pure industrial automation scene, 
best quality, ultra detailed, crystal clear, 
smart warehouse technology, visually comfortable, 
bright and modern atmosphere, professional automation,
8k resolution, robotic sorting system, AGV vehicles'''
    }
]

def get_access_token():
    """获取百度千帆 access token"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    
    response = requests.post(url, params=params)
    result = response.json()
    
    if 'access_token' in result:
        print("✅ 获取 access token 成功")
        return result['access_token']
    else:
        print("❌ 获取 access token 失败:", result)
        return None

def generate_image(prompt, filename, title):
    """调用百度千帆文心一格 API 生成图片"""
    access_token = get_access_token()
    if not access_token:
        return False
    
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd-xl-1.0?access_token={access_token}"
    
    # 请求参数
    payload = {
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, distorted, ugly, bad anatomy, watermark, text, signature, gradient, overlay",
        "size": "1024x576",  # 16:9 比例
        "n": 1,
        "steps": 30,
        "sampler": "Euler a",
        "cfg_scale": 7.5,
        "seed": -1
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"\n🎨 正在生成：{title}...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        result = response.json()
        
        if 'data' in result and 'images' in result['data']:
            # 解析返回的图片
            image_data = result['data']['images'][0]
            
            # 解码 base64 图片
            image_bytes = base64.b64decode(image_data)
            
            # 保存图片
            save_path = SAVE_DIR / filename
            with open(save_path, 'wb') as f:
                f.write(image_bytes)
            
            print(f"✅ 图片保存成功：{save_path}")
            return True
        else:
            print(f"❌ 生成失败：{result}")
            return False
            
    except Exception as e:
        print(f"❌ 生成过程中出错：{str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 百度千帆 AI 生成入库管理轮播图")
    print("=" * 60)
    print(f"\n📁 图片保存目录：{SAVE_DIR}")
    print(f"\n📋 计划生成 {len(prompts)} 张图片\n")
    
    # 检查 API 配置
    if API_KEY == 'YOUR_API_KEY' or SECRET_KEY == 'YOUR_SECRET_KEY':
        print("❌ 错误：请先配置 API_KEY 和 SECRET_KEY")
        print("\n请按照以下步骤获取 API 密钥：")
        print("1. 访问 https://console.bce.baidu.com/qianfan/")
        print("2. 登录百度智能云账号")
        print("3. 进入应用管理 -> 创建应用")
        print("4. 获取 API Key 和 Secret Key")
        print("5. 填入此脚本的 API_KEY 和 SECRET_KEY 变量中")
        return
    
    # 生成每张图片
    success_count = 0
    for i, item in enumerate(prompts, 1):
        print(f"\n{'='*60}")
        print(f"📸 [{i}/{len(prompts)}] 生成：{item['title']}")
        print(f"{'='*60}")
        
        success = generate_image(
            prompt=item['prompt'],
            filename=item['filename'],
            title=item['title']
        )
        
        if success:
            success_count += 1
        
        # 避免请求过快，等待几秒
        if i < len(prompts):
            print("\n⏳ 等待 3 秒后继续下一张...")
            import time
            time.sleep(3)
    
    # 生成完成
    print("\n" + "=" * 60)
    print("✨ 生成完成！")
    print("=" * 60)
    print(f"\n✅ 成功：{success_count} 张")
    print(f"❌ 失败：{len(prompts) - success_count} 张")
    print(f"\n📁 保存位置：{SAVE_DIR}")
    print("\n💡 提示：百度千帆 SD-XL 模型默认生成 1024x576 分辨率")
    print("   如需 16K 超高清，建议使用 Midjourney 或其他专业工具")
    print("=" * 60)

if __name__ == '__main__':
    main()
