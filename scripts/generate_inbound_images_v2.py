"""
使用系统现有的百度千帆服务生成入库管理轮播图
直接复用系统中的 BaiduImageGenerationService
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.baidu_image_service import BaiduImageGenerationService
from datetime import datetime

# 图片保存目录
SAVE_DIR = Path('d:/Trae/spare_management/app/static/images/carousel')
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# 6 张图片的提示词（与文档中一致）
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
        'prompt': '''16K ultra detailed photograph of professional quality inspection area 
in modern warehouse, inspector in clean uniform using precision 
measuring instruments to check incoming goods, digital tablet 
displaying quality standards, bright LED lighting, 
white and light blue color palette, clean organized workspace, 
professional photography, maximum sharpness, hyper realistic, 
no gradient, no text, pure scene, 
commercial quality, best quality, ultra detailed, crystal clear, 
fresh and bright atmosphere, visually comfortable, professional QC process'''
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
modern technology, visually pleasing, bright atmosphere'''
    },
    {
        'filename': 'inbound_04.jpg',
        'title': '规范上架流程',
        'prompt': '''16K ultra detailed photograph of warehouse storage process, 
professional forklift operator placing goods onto high-bay racking 
system, organized warehouse interior with multiple levels of shelving, 
pallets with neatly stacked boxes, bright LED lighting, 
blue and gray color scheme, clean industrial architecture, 
professional photography, maximum sharpness, hyper realistic, 
no gradient, no text, pure scene, 
commercial quality, best quality, ultra detailed, crystal clear, 
fresh and bright atmosphere, visually comfortable, 
modern logistics facility, professional operation'''
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
modern digital workflow, visually pleasing, bright atmosphere'''
    },
    {
        'filename': 'inbound_06.jpg',
        'title': '自动化分拣系统',
        'prompt': '''16K ultra detailed photograph of automated conveyor belt system 
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
bright and modern atmosphere, professional automation'''
    }
]

def generate_images():
    """生成所有图片"""
    print("=" * 60)
    print("使用百度千帆生成入库管理轮播图")
    print("=" * 60)
    print(f"\n图片保存目录：{SAVE_DIR}\n")
    
    # 初始化服务
    service = BaiduImageGenerationService()
    
    if not service.client:
        print("错误：百度千帆客户端未初始化")
        print("\n请检查是否配置了 BAIDU_API_KEY 环境变量")
        print("配置方法：")
        print("1. 在 .env 文件中添加：BAIDU_API_KEY=your_api_key")
        print("2. 或者设置系统环境变量")
        return False
    
    print("百度千帆服务初始化成功\n")
    
    # 负面提示词
    negative_prompt = "blurry, low quality, distorted, ugly, watermark, text, signature, gradient, overlay, cartoon, anime, drawing"
    
    # 生成每张图片
    success_count = 0
    for i, item in enumerate(prompts, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(prompts)}] 生成：{item['title']}")
        print(f"{'='*60}")
        
        try:
            # 调用服务生成图片
            result = service.generate_warehouse_image(
                prompt=item['prompt'],
                negative_prompt=negative_prompt,
                style="photorealistic",
                resolution="1024x576",  # 16:9 比例
                steps=30
            )
            
            if result.get('success') and result.get('images'):
                image_url = result['images'][0]
                print(f"图片生成成功：{image_url}")
                
                # 保存图片
                save_path = SAVE_DIR / item['filename']
                save_result = service.save_image(image_url, str(save_path))
                
                if save_result.get('success'):
                    print(f"图片保存成功：{save_path}")
                    success_count += 1
                else:
                    print(f"图片保存失败：{save_result.get('error')}")
            else:
                print(f"生成失败：{result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"生成过程中出错：{str(e)}")
        
        # 避免请求过快，等待几秒
        if i < len(prompts):
            print("\n等待 3 秒后继续下一张...")
            import time
            time.sleep(3)
    
    # 生成完成
    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)
    print(f"\n成功：{success_count} 张")
    print(f"失败：{len(prompts) - success_count} 张")
    print(f"\n保存位置：{SAVE_DIR}")
    print("\n提示：百度千帆 SD-XL 模型默认生成 1024x576 分辨率")
    print("   如需 16K 超高清，建议使用 Midjourney 或其他专业工具")
    print("=" * 60)
    
    return success_count > 0

if __name__ == '__main__':
    generate_images()
