# -*- coding: utf-8 -*-
"""
使用文心一言 AI 为备件生成缩略图
分析备件信息，生成 6 张高清图（正面、侧面、俯视、结构、电路、细节），然后生成缩略图
"""

import os
import sys
import json
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
import io

# 加载环境变量
load_dotenv()

# 百度文心一言 API 配置
API_KEY = os.getenv('BAIDU_API_KEY', '')

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


def get_access_token():
    """获取文心一言 API 的 access token"""
    # 注意：图片生成需要使用专门的 API Key 和 Secret Key
    # 在百度智能云控制台 - 应用列表 - 创建应用时选择"文心一言"服务
    # 获取的 API Key 和 Secret Key 必须是配对的
    
    # 从环境变量获取 Secret Key
    SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')
    
    if not SECRET_KEY:
        print("  ⚠️ 未配置 BAIDU_SECRET_KEY，使用 API_KEY 作为 Secret Key 尝试")
        SECRET_KEY = API_KEY
    
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
            return result["access_token"]
        else:
            print(f"  获取 access_token 失败：{result}")
            return None
    except Exception as e:
        print(f"  获取 access_token 异常：{str(e)}")
        return None


def generate_image_prompt(part):
    """根据备件信息生成图片提示词"""
    name = part.name or ''
    spec = part.specification or ''
    remark = part.remark or ''
    
    # 分析备件类型
    if '轴承' in name or 'bearing' in name.lower():
        category = '工业轴承'
        features = '金属材质，精密机械零件，圆形结构，滚珠或滚子，光滑表面'
    elif '液压' in name or '气缸' in name:
        category = '液压/气动元件'
        features = '金属圆柱体，工业设备，液压系统，精密加工'
    elif '传感器' in name or 'sensor' in name.lower():
        category = '电子传感器'
        features = '电子设备，精密仪器，连接线，金属或塑料外壳'
    elif '螺栓' in name or '螺母' in name or '螺钉' in name:
        category = '紧固件'
        features = '金属螺纹件，标准件，六角或圆形头部'
    elif '开关' in name or '继电器' in name or '断路器' in name:
        category = '电气元件'
        features = '电气开关设备，塑料或金属外壳，接线端子'
    elif '滤芯' in name or '过滤器' in name:
        category = '过滤设备'
        features = '圆柱形滤芯，过滤材料，工业净化设备'
    elif '润滑油' in name or '润滑脂' in name:
        category = '工业油品'
        features = '工业润滑油桶或油壶，液体容器'
    else:
        category = '工业备件'
        features = '工业零部件，机械设备，精密制造'
    
    # 生成提示词模板
    prompt_template = f"""专业工业产品摄影，{category}，{name}，{spec}，{features}，
高清实拍图，专业布光，白色渐变背景，产品细节清晰，
工业级品质，现代科技感，8K 超高清"""
    
    return prompt_template


def generate_wenxin_image(prompt, output_path):
    """调用文心一言图片生成 API"""
    print(f"  🔄 正在生成图片...")
    
    # 文心一言图片生成 API
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl"
    
    # 获取 access token
    access_token = get_access_token()
    if not access_token:
        print("  ✗ 获取 access token 失败")
        return False
    
    url = f"{url}?access_token={access_token}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "size": "1024x1024",
        "num": 1,
        "style": "photographic"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                # 获取图片 URL
                image_url = result['data'][0].get('image', '')
                
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
        else:
            print(f"  ✗ API 调用失败：{response.status_code}")
            print(f"  错误信息：{response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ 发生错误：{str(e)}")
        return False


def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    """从原图生成缩略图"""
    try:
        with Image.open(image_path) as img:
            # 转换为 RGB 模式（处理 PNG 透明背景）
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
    """为单个备件生成 6 张图片和缩略图"""
    print(f"\n{'='*80}")
    print(f"处理：{part.part_code} - {part.name}")
    print(f"{'='*80}")
    
    # 创建备件图片文件夹
    part_dir = os.path.join(BASE_DIR, part.part_code)
    os.makedirs(part_dir, exist_ok=True)
    
    # 定义 6 种视角
    views = [
        ('front', '正面图', '专业产品正面摄影，清晰展示产品正面特征和结构'),
        ('side', '侧面图', '专业产品侧面摄影，展示产品侧面轮廓和细节'),
        ('top', '俯视图', '专业产品俯视摄影，展示产品顶部结构和布局'),
        ('structure', '结构图', '产品结构示意图，展示内部构造和组件关系，技术图纸风格'),
        ('detail', '细节图', '产品细节特写，展示关键部位和精密加工细节，微距摄影'),
    ]
    
    # 判断是否需要电路图
    need_circuit = any(keyword in part.name for keyword in ['传感器', '开关', '继电器', '断路器', '电气', '电路'])
    
    if need_circuit:
        views.insert(4, ('circuit', '电路图', '电路原理图，展示电气连接和电子元件布局，专业技术图纸'))
    
    generated_images = {}
    
    # 生成 6 张图
    for view_code, view_name, view_desc in views:
        print(f"\n  生成 {view_name}...")
        
        # 生成提示词
        base_prompt = generate_image_prompt(part)
        full_prompt = f"{base_prompt}，{view_desc}"
        
        # 输出路径
        output_path = os.path.join(part_dir, f"{view_code}.jpg")
        
        # 生成图片
        success = generate_wenxin_image(full_prompt, output_path)
        
        if success:
            generated_images[view_code] = output_path
    
    # 从正面图生成缩略图
    if 'front' in generated_images:
        front_image = generated_images['front']
        thumbnail_path = os.path.join(part_dir, 'thumbnail.jpg')
        
        print(f"\n  生成缩略图...")
        create_thumbnail(front_image, thumbnail_path)
        
        # 返回缩略图路径（相对于 uploads/images）
        relative_path = os.path.join(part.part_code, 'thumbnail.jpg')
        return relative_path
    else:
        print(f"\n  ⚠️ 未能生成正面图，无法创建缩略图")
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
    print("文心一言 AI - 备件缩略图批量生成")
    print("="*80)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if not API_KEY:
        print("\n✗ 错误：请先配置 BAIDU_API_KEY")
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
    print("测试模式：生成前 3 条备件的缩略图")
    print("="*80)
    
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
