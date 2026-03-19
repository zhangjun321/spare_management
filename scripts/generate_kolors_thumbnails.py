# -*- coding: utf-8 -*-
"""
使用快手 Kolors 模型生成备件缩略图
通过硅基流动 API 调用，无需 GPU，有免费额度
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
import io

# 加载环境变量
load_dotenv()

# 硅基流动 API 配置
API_KEY = os.getenv('SILICONFLOW_API_KEY', '')
API_URL = "https://api.siliconflow.cn/v1/images/generations"

# 图片存储路径
BASE_DIR = r'D:\Trae\spare_management\uploads\images'

# Flask 应用配置
os.environ['FLASK_ENV'] = 'development'

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.spare_part import SparePart

# 创建 Flask 应用
app = create_app()


def generate_kolors_image(prompt, output_path):
    """调用硅基流动 Kolors API 生成图片"""
    print(f"  🔄 正在生成图片...")
    
    if not API_KEY:
        print(f"  ✗ 未配置 SILICONFLOW_API_KEY")
        return False
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Kwai-Kolors/Kolors",
        "prompt": prompt,
        "image_size": "1024x1024",
        "num_inference_steps": 28,
        "seed": int(datetime.now().timestamp()) % 1000000,
        "batch_size": 1
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                # 获取图片 URL
                image_url = result['data'][0].get('url', '')
                
                if image_url:
                    # 下载图片
                    img_response = requests.get(image_url, timeout=30)
                    
                    if img_response.status_code == 200:
                        # 保存图片
                        with open(output_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        print(f"  ✓ 图片生成成功：{output_path}")
                        return True
                    else:
                        print(f"  ✗ 下载图片失败")
                        return False
                else:
                    print(f"  ✗ 未获取到图片 URL")
                    return False
            else:
                print(f"  ✗ API 返回数据格式错误：{result}")
                return False
        elif response.status_code == 402:
            print(f"  ✗ 余额不足或免费额度用尽")
            return False
        else:
            print(f"  ✗ API 调用失败：{response.status_code}")
            print(f"  错误信息：{response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ 发生错误：{str(e)}")
        return False


def generate_image_prompt(part):
    """根据备件信息生成图片提示词"""
    name = part.name or ''
    spec = part.specification or ''
    remark = part.remark or ''
    
    # 分析备件类型
    if '轴承' in name or 'bearing' in name.lower():
        category = '工业轴承'
        features = '金属材质，精密机械零件，圆形结构，滚珠，光滑表面，银色金属光泽'
    elif '液压' in name or '气缸' in name:
        category = '液压气动元件'
        features = '金属圆柱体，工业设备，液压系统，精密加工，蓝色或银色'
    elif '传感器' in name or 'sensor' in name.lower():
        category = '电子传感器'
        features = '电子设备，精密仪器，连接线，金属外壳，黑色或灰色'
    elif '螺栓' in name or '螺母' in name or '螺钉' in name:
        category = '紧固件'
        features = '金属螺纹件，标准件，六角头部，银色镀锌'
    elif '开关' in name or '继电器' in name or '断路器' in name:
        category = '电气元件'
        features = '电气开关设备，塑料外壳，接线端子，工业级'
    elif '滤芯' in name or '过滤器' in name:
        category = '过滤设备'
        features = '圆柱形滤芯，白色滤纸，金属端盖，工业净化'
    elif '润滑油' in name or '润滑脂' in name:
        category = '工业油品'
        features = '工业润滑油桶，金属容器，蓝色或红色标签'
    else:
        category = '工业备件'
        features = '工业零部件，机械设备，精密制造，金属材质'
    
    # 生成提示词
    prompt = f"""专业工业产品摄影，{category}，{name}，{spec}，{features}，
高清实拍图，专业布光，纯白色背景，产品细节清晰，
工业级品质，现代科技感，8K 超高清，商业摄影级别"""
    
    return prompt


def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    """从原图生成缩略图"""
    try:
        with Image.open(image_path) as img:
            # 转换为 RGB 模式
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # 生成缩略图
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 保存缩略图
            img.save(thumbnail_path, 'JPEG', quality=95)
            
            print(f"  ✓ 缩略图已生成：{thumbnail_path}")
            return True
    except Exception as e:
        print(f"  ✗ 缩略图生成失败：{str(e)}")
        return False


def generate_images_for_part(part):
    """为单个备件生成图片和缩略图"""
    print(f"\n{'='*80}")
    print(f"处理：{part.part_code} - {part.name}")
    print(f"{'='*80}")
    
    # 创建备件图片文件夹
    part_dir = os.path.join(BASE_DIR, part.part_code)
    os.makedirs(part_dir, exist_ok=True)
    
    # 生成正面图
    print(f"\n  生成正面图...")
    base_prompt = generate_image_prompt(part)
    front_path = os.path.join(part_dir, 'front.jpg')
    
    success = generate_kolors_image(base_prompt, front_path)
    
    if success:
        # 生成缩略图
        thumbnail_path = os.path.join(part_dir, 'thumbnail.jpg')
        print(f"\n  生成缩略图...")
        create_thumbnail(front_path, thumbnail_path)
        
        # 返回缩略图路径
        relative_path = os.path.join(part.part_code, 'thumbnail.jpg')
        return relative_path
    else:
        print(f"\n  ✗ 图片生成失败")
        return None


def update_database(part, thumbnail_path):
    """更新数据库中的缩略图路径"""
    if thumbnail_path:
        # 构建完整的 URL 路径
        image_url = f"/uploads/images/{thumbnail_path.replace(os.sep, '/')}"
        
        part.image_url = image_url
        db.session.commit()
        print(f"  ✓ 数据库已更新：{image_url}")
        return True
    return False


def generate_thumbnails_for_all(batch_size=10):
    """为所有备件生成缩略图（分批处理）"""
    print("="*80)
    print("快手 Kolors AI - 备件缩略图批量生成")
    print("="*80)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if not API_KEY:
        print("\n✗ 错误：请先配置 SILICONFLOW_API_KEY")
        print("\n获取方式：")
        print("1. 访问 https://cloud.siliconflow.cn/")
        print("2. 注册账号并创建 API Key")
        print("3. 添加到 .env 文件：SILICONFLOW_API_KEY=your_key")
        return
    
    # 确保图片目录存在
    os.makedirs(BASE_DIR, exist_ok=True)
    
    with app.app_context():
        # 获取所有备件
        all_parts = SparePart.query.all()
        total = len(all_parts)
        
        print(f"\n共有 {total} 条备件记录")
        print(f"每批处理 {batch_size} 条")
        
        # 分批处理
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_parts = all_parts[batch_start:batch_end]
            
            print(f"\n{'='*80}")
            print(f"处理批次：{batch_start//batch_size + 1} ({batch_start+1}-{batch_end}/{total})")
            print(f"{'='*80}")
            
            for i, part in enumerate(batch_parts, 1):
                print(f"\n[{i}/{len(batch_parts)}] 处理：{part.part_code}")
                
                # 如果已经有缩略图，跳过
                if part.image_url:
                    print(f"  ⚠️ 已有缩略图，跳过")
                    continue
                
                # 生成图片
                thumbnail_path = generate_images_for_part(part)
                
                # 更新数据库
                if thumbnail_path:
                    update_database(part, thumbnail_path)
                
                # 延迟避免 API 限流
                import time
                time.sleep(2)
    
    print("\n" + "="*80)
    print("生成完成！")
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    # 测试：只生成前 3 条记录
    print("="*80)
    print("测试模式：生成前 3 条备件的缩略图（使用快手 Kolors 模型）")
    print("="*80)
    
    if not API_KEY:
        print("\n⚠️ 未配置 SILICONFLOW_API_KEY")
        print("\n请先配置 API Key：")
        print("1. 访问 https://cloud.siliconflow.cn/")
        print("2. 注册账号，创建 API Key")
        print("3. 编辑 .env 文件，添加：SILICONFLOW_API_KEY=your_key")
        print("="*80)
    else:
        print(f"\n✅ API Key 已配置：{API_KEY[:20]}...")
        
        with app.app_context():
            parts = SparePart.query.limit(3).all()
            
            for part in parts:
                if not part.image_url:
                    thumbnail_path = generate_images_for_part(part)
                    if thumbnail_path:
                        update_database(part, thumbnail_path)
                else:
                    print(f"\n跳过 {part.part_code} - 已有缩略图")
        
        print("\n" + "="*80)
        print("测试完成！")
        print("="*80)
        print("\n提示：")
        print("1. 检查图片是否生成：D:\\Trae\\spare_management\\uploads\\images\\")
        print("2. 检查数据库是否更新")
        print("3. 如果测试成功，运行 generate_thumbnails_for_all() 生成所有备件")
        print("="*80)
