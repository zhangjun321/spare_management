"""
使用文心一言（百度千帆）API 生成出库、库存、AI 分析轮播图
生成 18 张高质量现代化工业场景图片（每个页面 6 张）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.baidu_image_service import BaiduImageGenerationService

# 图片保存目录
SAVE_DIR = Path('d:/Trae/spare_management/app/static/images/carousel')
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 出库管理 6 张图片 ====================
outbound_prompts = [
    {
        'filename': 'outbound_01.jpg',
        'title': '出库订单处理',
        'prompt': '''Ultra high resolution 8K photograph of modern warehouse outbound order processing center, 
professional administrator working at desk with dual monitors displaying order management system, 
digital tablet showing outbound order list, bright natural lighting through large windows, 
white and light blue color scheme, organized office environment, 
professional photography, hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
wide angle view, crystal clear, vibrant but comfortable colors, 
no gradient, no text, pure office scene, 
best quality, ultra detailed, professional warehouse management photography, 
bright and fresh atmosphere, visually pleasing, modern logistics technology'''
    },
    {
        'filename': 'outbound_02.jpg',
        'title': '智能拣货系统',
        'prompt': '''8K ultra detailed photograph of intelligent warehouse picking system, 
professional picker using handheld device to collect items from high-bay racking, 
digital picking list on screen, organized warehouse aisles with barcode labels, 
bright LED lighting, blue and gray color palette, clean industrial environment, 
professional photography, maximum sharpness, hyper realistic, 8K resolution,
no gradient, no text, pure industrial scene, 
commercial quality, best quality, ultra detailed, crystal clear, 
fresh and bright atmosphere, visually comfortable, smart picking technology,
detailed handheld device and racking system, photorealistic'''
    },
    {
        'filename': 'outbound_03.jpg',
        'title': '精准配货复核',
        'prompt': '''Ultra high resolution 8K photograph of warehouse order verification station, 
quality inspector double-checking picked items against order list, 
organized packing table with barcode scanner and computer, 
bright lighting, white and blue uniform, professional QC process, 
professional industrial photography, hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
vibrant but comfortable colors, clear focus, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, crystal clear, 
modern quality control, visually pleasing, bright atmosphere,
detailed verification equipment and workflow, photorealistic, cinematic composition'''
    },
    {
        'filename': 'outbound_04.jpg',
        'title': '自动化包装线',
        'prompt': '''8K ultra detailed photograph of automated packaging line in modern warehouse, 
workers packaging goods into cartons, automated taping and labeling machines, 
conveyor belt system, bright industrial lighting, blue and silver color scheme, 
futuristic packaging technology, professional industrial photography, 
hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
vibrant colors, clear focus, 
no gradient, no text, pure industrial automation scene, 
best quality, ultra detailed, crystal clear, 
smart packaging technology, visually comfortable, 
bright and modern atmosphere, professional automation,
detailed packaging equipment and workflow, photorealistic, cinematic lighting'''
    },
    {
        'filename': 'outbound_05.jpg',
        'title': '出库扫码核验',
        'prompt': '''Ultra high resolution 8K photograph of warehouse outbound scanning process, 
professional worker using industrial barcode scanner to verify outgoing goods, 
shipping dock area with stacked pallets ready for dispatch, 
bright natural lighting, blue and white uniform, modern logistics technology, 
professional industrial photography, hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
vibrant colors, clear focus, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, crystal clear, 
modern scanning technology, visually pleasing, bright atmosphere,
detailed scanner device and shipping area, photorealistic, professional logistics'''
    },
    {
        'filename': 'outbound_06.jpg',
        'title': '物流配送管理',
        'prompt': '''8K ultra detailed photograph of warehouse shipping and distribution area, 
loaded delivery trucks at loading docks ready for dispatch, 
logistics coordinator with clipboard directing operations, 
organized parking bays, bright daylight, blue and white color scheme, 
professional logistics facility, professional photography, 
hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
vibrant colors, wide angle view, 
no gradient, no text, pure logistics scene, 
best quality, ultra detailed, crystal clear, 
modern distribution center, visually comfortable, 
bright and professional atmosphere, cinematic composition,
detailed trucks and loading operations, photorealistic'''
    }
]

# ==================== 库存管理 6 张图片 ====================
inventory_prompts = [
    {
        'filename': 'inventory_01.jpg',
        'title': '实时库存监控',
        'prompt': '''Ultra high resolution 8K photograph of modern warehouse inventory monitoring center, 
large video wall displaying real-time stock levels and analytics dashboards, 
professional operators at control desks with multiple monitors, 
bright professional lighting, blue and white technology theme, 
futuristic control room environment, professional photography, 
hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
wide angle view, crystal clear, vibrant but comfortable colors, 
no gradient, no text, pure technology scene, 
best quality, ultra detailed, crystal clear, 
modern inventory management technology, visually pleasing, bright atmosphere,
detailed monitoring screens and control room, photorealistic, cinematic lighting'''
    },
    {
        'filename': 'inventory_02.jpg',
        'title': '智能库存预警',
        'prompt': '''8K ultra detailed photograph of warehouse manager reviewing inventory alerts 
on tablet computer, low stock warning notifications on screen, 
modern warehouse office background, bright natural lighting, 
white and light blue color palette, professional work environment, 
professional photography, maximum sharpness, hyper realistic, 8K resolution,
no gradient, no text, pure scene, 
commercial quality, best quality, ultra detailed, crystal clear, 
fresh and bright atmosphere, visually comfortable, 
digital tablet with clear interface, photorealistic, detailed workspace'''
    },
    {
        'filename': 'inventory_03.jpg',
        'title': '定期库存盘点',
        'prompt': '''Ultra high resolution 8K photograph of warehouse inventory counting process, 
professional workers with handheld devices conducting stocktake, 
organized warehouse aisles with barcode-labeled shelves, 
bright LED lighting, blue and white uniforms, systematic workflow, 
professional industrial photography, hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
vibrant but comfortable colors, clear focus, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, crystal clear, 
modern inventory management, visually pleasing, bright atmosphere,
detailed counting devices and organized shelves, photorealistic'''
    },
    {
        'filename': 'inventory_04.jpg',
        'title': '货位优化管理',
        'prompt': '''8K ultra detailed aerial photograph of optimized warehouse racking system, 
color-coded storage zones with clear aisle markings, 
automated guided vehicles moving in organized pathways, 
symmetrical layout, bright overhead lighting, blue and gray color scheme, 
modern logistics facility, professional architectural photography, 
hyper realistic, maximum sharpness, 8K resolution,
wide angle view from above, vibrant colors, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, crystal clear, 
smart warehouse layout, visually comfortable, 
bright and organized atmosphere, cinematic composition,
detailed racking and AGV vehicles, photorealistic'''
    },
    {
        'filename': 'inventory_05.jpg',
        'title': '批次追溯管理',
        'prompt': '''Ultra high resolution 8K photograph of warehouse batch tracking system, 
close-up of barcode labels on shelves with batch numbers and dates, 
organized storage bins with clear identification tags, 
bright lighting, white and blue color scheme, systematic organization, 
professional industrial photography, hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
macro shot with clear focus, vibrant but comfortable colors, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, crystal clear, 
modern traceability system, visually pleasing, bright atmosphere,
detailed labels and organized storage, photorealistic, professional warehouse management'''
    },
    {
        'filename': 'inventory_06.jpg',
        'title': '库存调拨管理',
        'prompt': '''8K ultra detailed photograph of warehouse stock transfer process, 
professional forklift operator moving pallets between storage zones, 
inventory redistribution in organized warehouse aisles, 
bright industrial lighting, blue and yellow color scheme, 
modern logistics center, professional photography, 
hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
action shot with clear focus, vibrant colors, 
no gradient, no text, pure industrial scene, 
best quality, ultra detailed, crystal clear, 
efficient stock management, visually comfortable, 
bright and professional atmosphere, cinematic composition,
detailed forklift operations and storage zones, photorealistic'''
    }
]

# ==================== AI 分析 6 张图片 ====================
analysis_prompts = [
    {
        'filename': 'analysis_01.jpg',
        'title': 'AI 智能分析',
        'prompt': '''Ultra high resolution 8K photograph of AI-powered warehouse analytics center, 
large curved display wall showing machine learning algorithms and predictive models, 
data visualization with neural network graphics, 
futuristic control room with blue and purple ambient lighting, 
professional technology environment, professional photography, 
hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
wide angle view, crystal clear, vibrant but comfortable colors, 
no gradient, no text, pure technology scene, 
best quality, ultra detailed, crystal clear, 
modern AI analytics technology, visually pleasing, bright atmosphere,
detailed data visualizations and control room, photorealistic, cinematic lighting'''
    },
    {
        'filename': 'analysis_02.jpg',
        'title': '库存周转分析',
        'prompt': '''8K ultra detailed photograph of business analytics dashboard, 
multiple monitors displaying inventory turnover charts and graphs, 
KPI metrics and trend analysis visualizations, 
modern office environment, bright natural lighting, 
white and blue color palette, professional workspace, 
professional photography, maximum sharpness, hyper realistic, 8K resolution,
no gradient, no text, pure business analytics scene, 
commercial quality, best quality, ultra detailed, crystal clear, 
fresh and bright atmosphere, visually comfortable, 
detailed charts and graphs on screens, photorealistic, data-driven decision making'''
    },
    {
        'filename': 'analysis_03.jpg',
        'title': '需求预测模型',
        'prompt': '''Ultra high resolution 8K photograph of predictive analytics visualization, 
holographic-style charts and forecasting models floating in air, 
AI-powered demand prediction interface with trend lines, 
futuristic data science lab environment, bright blue and white lighting, 
professional technology setting, professional photography, 
hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
wide angle view, crystal clear, vibrant colors, 
no gradient, no text, pure technology scene, 
best quality, ultra detailed, crystal clear, 
modern predictive AI technology, visually pleasing, bright atmosphere,
detailed forecasting models and visualizations, photorealistic, futuristic interface'''
    },
    {
        'filename': 'analysis_04.jpg',
        'title': '成本效益分析',
        'prompt': '''8K ultra detailed photograph of financial analytics workspace, 
triple monitor setup displaying cost-benefit analysis charts, 
ROI metrics and budget optimization visualizations, 
modern business intelligence center, bright professional lighting, 
white and gold color scheme, sophisticated environment, 
professional photography, hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
clear focus on screens, vibrant but professional colors, 
no gradient, no text, pure business scene, 
best quality, ultra detailed, crystal clear, 
financial analytics technology, visually comfortable, 
bright and professional atmosphere, cinematic composition,
detailed financial charts and metrics, photorealistic'''
    },
    {
        'filename': 'analysis_05.jpg',
        'title': '数据可视化',
        'prompt': '''Ultra high resolution 8K photograph of advanced data visualization center, 
massive video wall displaying colorful interactive charts and KPIs, 
real-time warehouse management metrics and performance indicators, 
modern analytics command center, bright professional lighting, 
blue and purple color scheme with vibrant accents, 
professional technology environment, professional photography, 
hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
wide angle view, crystal clear, vibrant colors, 
no gradient, no text, pure technology scene, 
best quality, ultra detailed, crystal clear, 
modern data visualization technology, visually pleasing, bright atmosphere,
detailed charts and command center, photorealistic, cinematic lighting'''
    },
    {
        'filename': 'analysis_06.jpg',
        'title': '智能决策支持',
        'prompt': '''8K ultra detailed photograph of executive decision support system, 
interactive touchscreen table displaying AI recommendations and insights, 
modern boardroom with smart displays on walls, 
data-driven decision making interface, bright professional lighting, 
sophisticated blue and wood color scheme, executive environment, 
professional photography, hyper realistic, extremely detailed, maximum sharpness, 8K resolution,
clear focus on interactive displays, vibrant but professional colors, 
no gradient, no text, pure business technology scene, 
best quality, ultra detailed, crystal clear, 
executive decision support technology, visually comfortable, 
bright and sophisticated atmosphere, cinematic composition,
detailed interactive displays and boardroom, photorealistic'''
    }
]

def generate_image_set(service, prompts, category_name):
    """生成一组图片"""
    print(f"\n{'='*80}")
    print(f"开始生成：{category_name}")
    print(f"{'='*80}")
    
    # 负面提示词
    negative_prompt = "blurry, low quality, distorted, ugly, watermark, text, signature, gradient, overlay, cartoon, anime, drawing, illustration, dark, messy"
    
    success_count = 0
    for i, item in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] 生成：{item['title']}")
        
        try:
            # 调用服务生成图片
            result = service.generate_warehouse_image(
                prompt=item['prompt'],
                negative_prompt=negative_prompt,
                style="photorealistic",
                resolution="1024x576",
                steps=50
            )
            
            if result.get('success') and result.get('images'):
                image_url = result['images'][0]
                print(f"图片生成成功")
                
                # 保存图片
                save_path = SAVE_DIR / item['filename']
                save_result = service.save_image(image_url, str(save_path))
                
                if save_result.get('success'):
                    print(f"图片保存成功：{item['filename']}")
                    success_count += 1
                else:
                    print(f"图片保存失败：{save_result.get('error')}")
            else:
                print(f"生成失败：{result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"生成过程中出错：{str(e)}")
        
        # 避免请求过快
        if i < len(prompts):
            print("等待 3 秒后继续...")
            import time
            time.sleep(3)
    
    return success_count

def main():
    """主函数"""
    print("="*80)
    print("使用文心一言（百度千帆）生成出库、库存、AI 分析轮播图")
    print("="*80)
    print(f"\n图片保存目录：{SAVE_DIR}\n")
    
    # 初始化服务
    service = BaiduImageGenerationService()
    
    if not service.client:
        print("错误：百度千帆客户端未初始化")
        print("\n请检查是否配置了 BAIDU_API_KEY 环境变量")
        return False
    
    print("百度千帆服务初始化成功\n")
    
    total_success = 0
    
    # 生成出库管理图片
    success = generate_image_set(service, outbound_prompts, "出库管理（6 张）")
    total_success += success
    print(f"\n[OK] 出库管理完成：{success}/6 张")
    
    # 生成库存管理图片
    success = generate_image_set(service, inventory_prompts, "库存管理（6 张）")
    total_success += success
    print(f"\n[OK] 库存管理完成：{success}/6 张")
    
    # 生成 AI 分析图片
    success = generate_image_set(service, analysis_prompts, "AI 分析（6 张）")
    total_success += success
    print(f"\n[OK] AI 分析完成：{success}/6 张")
    
    # 生成完成
    print("\n" + "="*80)
    print("全部生成完成！")
    print("="*80)
    print(f"\n总计成功：{total_success}/18 张")
    print(f"\n保存位置：{SAVE_DIR}")
    print("\n提示：文心一格 SD-XL 模型生成 1024x576 分辨率（8K 质量优化）")
    print("="*80)
    
    return total_success > 0

if __name__ == '__main__':
    main()
