"""
AI 图像生成路由 - 百度文心一格集成
"""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from app.extensions import db
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation
from app.services.baidu_image_service import baidu_image_service
from app.services.warehouse_prompt_converter import warehouse_prompt_converter
from app.services.visualization_service import warehouse_visualization_service

ai_image_bp = Blueprint('ai_image', __name__, url_prefix='/ai-image')


def save_image_from_url(image_url, warehouse_id, warehouse_name):
    """
    从URL下载图片并保存到本地
    
    Args:
        image_url: 图片URL
        warehouse_id: 仓库ID
        warehouse_name: 仓库名称
    
    Returns:
        str: 保存的相对路径
    """
    import requests
    from datetime import datetime
    
    try:
        # 创建保存目录
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'uploads', 'images', 'warehouse')
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = ''.join(c if c.isalnum() else '_' for c in warehouse_name)
        filename = f"warehouse_{warehouse_id}_{safe_name}_{timestamp}.png"
        save_path = os.path.join(save_dir, filename)
        
        # 下载图片
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # 返回相对路径
            return f"/uploads/images/warehouse/{filename}"
        else:
            print(f"下载图片失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"保存图片异常: {e}")
        import traceback
        traceback.print_exc()
        return None


@ai_image_bp.route('/')
@login_required
def index():
    """AI 图像生成首页"""
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return render_template('ai_image/index.html', warehouses=warehouses)


@ai_image_bp.route('/generate/<int:warehouse_id>', methods=['POST'])
@login_required
def generate_warehouse_image(warehouse_id):
    """
    生成仓库实景图
    
    Args:
        warehouse_id: 仓库 ID
    
    Returns:
        JSON 响应
    """
    from flask import current_app
    
    # 检查仓库是否存在
    warehouse = Warehouse.query.get(warehouse_id)
    if not warehouse:
        current_app.logger.error(f"Warehouse ID {warehouse_id} not found")
        return jsonify({
            'success': False,
            'error': f'仓库不存在 (ID: {warehouse_id})'
        }), 404
    
    # 获取生成参数
    try:
        data = request.get_json() or {}
    except Exception:
        data = {}
    
    style = data.get('style', 'photorealistic')
    focus = data.get('focus', '')
    resolution = data.get('resolution', '1024x768')
    
    current_app.logger.info(f"Generating image for warehouse {warehouse.name}, style={style}, resolution={resolution}")
    
    # 获取仓库布局数据
    try:
        layout_data = warehouse_visualization_service.get_warehouse_layout(warehouse_id)
    except Exception as e:
        current_app.logger.error(f"Failed to get layout data: {e}")
        layout_data = {'zones': [], 'racks': [], 'statistics': {}}
    
    # 获取备件信息（简化版本）
    # 实际应该查询真实的备件数据
    parts_data = []
    
    # 构建完整的仓库数据
    statistics = layout_data.get('statistics', {})
    warehouse_data = {
        'id': warehouse.id,
        'name': warehouse.name,
        'code': warehouse.code,
        'type': warehouse.type,
        'zones': layout_data.get('zones', []),
        'racks': layout_data.get('racks', []),
        'parts': parts_data,
        'inventory': {
            'total_quantity': statistics.get('occupied_locations', 0),
            'usage_rate': statistics.get('usage_rate', 0)
        }
    }
    
    # 生成提示词
    prompt = warehouse_prompt_converter.convert(warehouse_data)
    negative_prompt = warehouse_prompt_converter.build_negative_prompt()
    
    # 如果有焦点，生成变体提示词
    if focus:
        prompt = warehouse_prompt_converter.generate_variation_prompt(prompt, focus)
    
    # 调用百度 API 生成图像
    result = baidu_image_service.generate_warehouse_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        style=style,
        resolution=resolution,
        steps=25
    )
    
    # 保存图片到本地
    local_images = []
    if result.get('success') and result.get('images'):
        current_app.logger.info("保存图片到本地...")
        for image_url in result['images']:
            local_path = save_image_from_url(image_url, warehouse_id, warehouse.name)
            if local_path:
                local_images.append(local_path)
                current_app.logger.info(f"图片已保存: {local_path}")
    
    if result.get('success'):
        # 保存生成记录
        image_record = {
            'warehouse_id': warehouse_id,
            'warehouse_name': warehouse.name,
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'style': style,
            'focus': focus,
            'resolution': resolution,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': current_user.id,
            'images': result.get('images', []),
            'local_images': local_images,
            'parameters': result.get('parameters', {})
        }
        
        return jsonify({
            'success': True,
            'warehouse_id': warehouse_id,
            'warehouse_name': warehouse.name,
            'prompt': prompt,
            'images': result.get('images', []),
            'local_images': local_images,
            'record': image_record
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', '生成失败'),
            'message': '百度文心一格 API 调用失败，请检查配置'
        }), 500


@ai_image_bp.route('/generate-batch', methods=['POST'])
@login_required
def generate_batch_images():
    """批量生成多个角度的仓库图像"""
    data = request.get_json()
    warehouse_id = data.get('warehouse_id')
    
    if not warehouse_id:
        return jsonify({'success': False, 'error': '缺少仓库 ID'}), 400
    
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    # 获取仓库布局数据
    layout_data = warehouse_visualization_service.get_warehouse_layout(warehouse_id)
    
    # 构建仓库数据
    statistics = layout_data.get('statistics', {})
    warehouse_data = {
        'id': warehouse.id,
        'name': warehouse.name,
        'code': warehouse.code,
        'type': warehouse.type,
        'zones': layout_data.get('zones', []),
        'racks': layout_data.get('racks', []),
        'parts': [],
        'inventory': {
            'total_quantity': statistics.get('occupied_locations', 0),
            'usage_rate': statistics.get('usage_rate', 0)
        }
    }
    
    # 基础提示词
    base_prompt = warehouse_prompt_converter.convert(warehouse_data)
    negative_prompt = warehouse_prompt_converter.build_negative_prompt()
    
    # 生成不同角度的图像
    focuses = ['entrance', 'center', 'shelves', 'path', 'aerial']
    results = []
    
    for focus in focuses:
        prompt = warehouse_prompt_converter.generate_variation_prompt(base_prompt, focus)
        
        result = baidu_image_service.generate_warehouse_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            style='photorealistic',
            resolution='1024x768',
            steps=25
        )
        
        results.append({
            'focus': focus,
            'prompt': prompt,
            'success': result.get('success', False),
            'images': result.get('images', []) if result.get('success') else []
        })
    
    # 返回所有结果
    success_count = sum(1 for r in results if r['success'])
    
    return jsonify({
        'success': success_count > 0,
        'warehouse_id': warehouse_id,
        'warehouse_name': warehouse.name,
        'total_count': len(focuses),
        'success_count': success_count,
        'results': results
    })


@ai_image_bp.route('/update-prompt/', methods=['POST'])
@login_required
def update_prompt():
    """
    手动调整提示词并重新生成
    
    允许用户自定义提示词，获得更符合需求的图像
    """
    data = request.get_json()
    warehouse_id = data.get('warehouse_id')
    custom_prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    style = data.get('style', 'photorealistic')
    
    if not warehouse_id or not custom_prompt:
        return jsonify({'success': False, 'error': '参数不完整'}), 400
    
    # 使用自定义提示词生成图像
    result = baidu_image_service.generate_warehouse_image(
        prompt=custom_prompt,
        negative_prompt=negative_prompt,
        style=style,
        resolution='1024x768',
        steps=25
    )
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'images': result.get('images', []),
            'message': '图像生成成功'
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', '生成失败')
        }), 500


@ai_image_bp.route('/history/<int:warehouse_id>/')
@login_required
def get_generation_history(warehouse_id):
    """获取仓库图像生成历史"""
    # 这里应该从数据库查询历史记录
    # 简化版本，返回空列表
    return jsonify({
        'success': True,
        'warehouse_id': warehouse_id,
        'history': []
    })


@ai_image_bp.route('/demo/')
@login_required
def demo():
    """演示页面 - 展示生成效果"""
    return render_template('ai_image/demo.html')


@ai_image_bp.route('/api/test', methods=['GET'])
@login_required
def test_api():
    """测试百度 API 连接"""
    # 简单的测试提示词
    test_prompt = "现代化仓库内部，整洁有序，高清摄影"
    test_negative = "模糊，低质量"
    
    result = baidu_image_service.generate_warehouse_image(
        prompt=test_prompt,
        negative_prompt=test_negative,
        style='photorealistic',
        resolution='512x512',
        steps=20
    )
    
    return jsonify(result)


@ai_image_bp.route('/api/test-no-login', methods=['GET'])
def test_api_no_login():
    """测试百度 API 连接（不需要登录）"""
    from flask import current_app
    
    current_app.logger.info("Testing API (no login required)...")
    
    # 简单的测试提示词
    test_prompt = "现代化仓库内部，整洁有序，高清摄影"
    test_negative = "模糊，低质量"
    
    result = baidu_image_service.generate_warehouse_image(
        prompt=test_prompt,
        negative_prompt=test_negative,
        style='photorealistic',
        resolution='512x512',
        steps=20
    )
    
    return jsonify(result)


@ai_image_bp.route('/generate-no-login/<int:warehouse_id>', methods=['POST'])
def generate_warehouse_image_no_login(warehouse_id):
    """
    生成仓库实景图（不需要登录 - 仅用于测试）
    
    Args:
        warehouse_id: 仓库 ID
    
    Returns:
        JSON 响应
    """
    from flask import current_app
    
    current_app.logger.info(f"Generating image for warehouse {warehouse_id} (no login)...")
    
    # 检查仓库是否存在
    warehouse = Warehouse.query.get(warehouse_id)
    if not warehouse:
        current_app.logger.error(f"Warehouse ID {warehouse_id} not found")
        return jsonify({
            'success': False,
            'error': f'仓库不存在 (ID: {warehouse_id})'
        }), 404
    
    # 获取生成参数
    try:
        data = request.get_json() or {}
    except Exception:
        data = {}
    
    style = data.get('style', 'photorealistic')
    focus = data.get('focus', '')
    resolution = data.get('resolution', '1024x768')
    
    current_app.logger.info(f"Params: style={style}, resolution={resolution}")
    
    # 获取仓库布局数据
    try:
        layout_data = warehouse_visualization_service.get_warehouse_layout(warehouse_id)
    except Exception as e:
        current_app.logger.error(f"Failed to get layout data: {e}")
        layout_data = {'zones': [], 'racks': [], 'statistics': {}}
    
    # 获取备件信息（简化版本）
    parts_data = []
    
    # 构建完整的仓库数据
    statistics = layout_data.get('statistics', {})
    warehouse_data = {
        'id': warehouse.id,
        'name': warehouse.name,
        'code': warehouse.code,
        'type': warehouse.type,
        'zones': layout_data.get('zones', []),
        'racks': layout_data.get('racks', []),
        'parts': parts_data,
        'inventory': {
            'total_quantity': statistics.get('occupied_locations', 0),
            'usage_rate': statistics.get('usage_rate', 0)
        }
    }
    
    # 生成提示词
    prompt = warehouse_prompt_converter.convert(warehouse_data)
    negative_prompt = warehouse_prompt_converter.build_negative_prompt()
    
    # 如果有焦点，生成变体提示词
    if focus:
        prompt = warehouse_prompt_converter.generate_variation_prompt(prompt, focus)
    
    current_app.logger.info(f"Calling Baidu API...")
    
    # 调用百度 API 生成图像
    result = baidu_image_service.generate_warehouse_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        style=style,
        resolution=resolution,
        steps=25
    )
    
    current_app.logger.info(f"Baidu API result: {result.get('success')}")
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'warehouse_id': warehouse_id,
            'warehouse_name': warehouse.name,
            'prompt': prompt,
            'images': result.get('images', [])
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', '生成失败'),
            'message': '百度文心一格 API 调用失败'
        }), 500


@ai_image_bp.route('/hello')
def hello():
    """最简单的测试"""
    from flask import current_app
    current_app.logger.info("Hello route called!")
    return jsonify({
        'success': True,
        'message': 'Hello from AI Image!'
    })


@ai_image_bp.route('/test-super-easy')
def test_super_easy():
    """超级简单测试页面"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test_super_easy.html')


@ai_image_bp.route('/test-new')
def test_new():
    """全新测试页面（无缓存）"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test_new.html')


@ai_image_bp.route('/ultimate-test')
def ultimate_test():
    """最终测试页面"""
    from flask import send_from_directory
    import os
    return send_from_directory(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ultimate_test.html')


@ai_image_bp.route('/generate-super-simple/<int:warehouse_id>', methods=['POST'])
def generate_super_simple(warehouse_id):
    """
    超级简化版 - 直接生成图像，不依赖其他服务
    
    Args:
        warehouse_id: 仓库 ID
    
    Returns:
        JSON 响应
    """
    from flask import current_app
    
    current_app.logger.info("=" * 80)
    current_app.logger.info(f"超级简化版生成: warehouse_id={warehouse_id}")
    current_app.logger.info("=" * 80)
    
    try:
        # 1. 检查仓库是否存在
        current_app.logger.info("步骤 1: 检查仓库...")
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            current_app.logger.error(f"仓库 ID {warehouse_id} 不存在")
            return jsonify({
                'success': False,
                'error': f'仓库不存在 (ID: {warehouse_id})'
            }), 404
        current_app.logger.info(f"仓库找到: {warehouse.name}")
        
        # 2. 获取生成参数
        current_app.logger.info("步骤 2: 获取请求数据...")
        try:
            data = request.get_json(force=True, silent=True) or {}
        except Exception as e:
            current_app.logger.error(f"JSON 解析错误: {e}")
            data = {}
        
        current_app.logger.info(f"请求数据: {data}")
        
        style = data.get('style', 'photorealistic')
        resolution = data.get('resolution', '1024x768')
        current_app.logger.info(f"参数: style={style}, resolution={resolution}")
        
        # 3. 简单提示词（使用英文更准确）
        current_app.logger.info("步骤 3: 构建提示词...")
        prompt = f"Modern warehouse interior, {warehouse.name}, industrial storage facility, metal shelving units, pallet racks with boxes, clean and organized, bright overhead lighting, concrete floor, wide aisles, realistic photography, high detail, 8k resolution"
        negative_prompt = "blurry, low quality, cartoon, anime, illustration, painting, drawing, 3d render, text, watermark, people, animals, outdoor, windows"
        current_app.logger.info(f"提示词: {prompt[:80]}...")
        
        # 4. 调用百度 API
        current_app.logger.info("步骤 4: 调用百度 API...")
        result = baidu_image_service.generate_warehouse_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            style=style,
            resolution=resolution,
            steps=20
        )
        
        current_app.logger.info(f"百度 API 结果: {result.get('success')}")
        
        # 5. 保存图片到本地
        local_images = []
        if result.get('success') and result.get('images'):
            current_app.logger.info("步骤 5: 保存图片到本地...")
            for image_url in result['images']:
                local_path = save_image_from_url(image_url, warehouse_id, warehouse.name)
                if local_path:
                    local_images.append(local_path)
                    current_app.logger.info(f"图片已保存: {local_path}")
        
        # 6. 返回结果（同时返回百度URL和本地路径）
        current_app.logger.info("步骤 6: 返回结果...")
        if result.get('success'):
            return jsonify({
                'success': True,
                'warehouse_id': warehouse_id,
                'warehouse_name': warehouse.name,
                'prompt': prompt,
                'images': result.get('images', []),
                'local_images': local_images
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '生成失败')
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"异常: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
