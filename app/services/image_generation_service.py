import os
import requests
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class ImageGenerationService:
    """文生图服务类"""
    
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("BAIDU_API_KEY")
        self.client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key=api_key
        )
        self.base_upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'images')
        self._ensure_base_dir()
    
    def _ensure_base_dir(self):
        """确保基础目录存在"""
        if not os.path.exists(self.base_upload_dir):
            os.makedirs(self.base_upload_dir, exist_ok=True)
    
    def _get_part_dir(self, part_code):
        """获取备件目录路径"""
        part_dir = os.path.join(self.base_upload_dir, part_code)
        if not os.path.exists(part_dir):
            os.makedirs(part_dir, exist_ok=True)
        return part_dir
    
    def _generate_prompt(self, part_name, supplier_name, image_type):
        """根据图片类型生成简洁提示词"""
        prompts = {
            'front': f"{part_name} 正面图",
            'side': f"{part_name} 侧面图",
            'detail': f"{part_name} 细节图",
            'circuit': f"{part_name} 内部结构图",
            'perspective': f"{part_name} 3D视图"
        }
        
        return prompts.get(image_type, part_name)
    
    def _generate_single_image(self, prompt, image_path, size="1024x768"):
        """生成单张图片 - 优化速度版本"""
        try:
            response = self.client.images.generate(
                model="qwen-image",
                prompt=prompt,
                size=size,
                n=1,
                extra_body={
                    "steps": 20,
                    "guidance": 2,
                    "negative_prompt": "",
                    "prompt_extend": False
                }
            )
            
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                if image_url:
                    # 下载图片
                    image_response = requests.get(image_url)
                    with open(image_path, 'wb') as f:
                        f.write(image_response.content)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"生成图片失败: {str(e)}")
            return False
    
    def _generate_thumbnail(self, original_path, thumbnail_path, max_width=200, max_height=150):
        """生成缩略图"""
        try:
            with Image.open(original_path) as img:
                # 计算缩略图尺寸，保持4:3比例
                img.thumbnail((max_width, max_height))
                img.save(thumbnail_path)
            return True
        except Exception as e:
            logger.error(f"生成缩略图失败: {str(e)}")
            return False
    
    def generate_spare_part_images(self, part_code, part_name, supplier_name):
        """
        生成备件的所有图片
        
        Args:
            part_code: 备件代码
            part_name: 备件名称
            supplier_name: 供应商名称
            
        Returns:
            dict: 包含生成的图片路径信息
        """
        part_dir = self._get_part_dir(part_code)
        
        image_types = [
            ('front', '正面图'),
            ('side', '侧面图'),
            ('detail', '详细图'),
            ('circuit', '电路图'),
            ('perspective', '透视图')
        ]
        
        results = {
            'success': True,
            'images': {},
            'thumbnail_url': None
        }
        
        front_image_path = None
        
        # 生成5张图片
        for image_type, image_name in image_types:
            image_filename = f"{image_type}.jpg"
            image_path = os.path.join(part_dir, image_filename)
            prompt = self._generate_prompt(part_name, supplier_name, image_type)
            
            if self._generate_single_image(prompt, image_path):
                # 保存相对路径（使用正斜杠，带前导斜杠）
                relative_path = f"/uploads/images/{part_code}/{image_filename}"
                results['images'][image_type] = relative_path
                
                if image_type == 'front':
                    front_image_path = image_path
            else:
                results['success'] = False
                results['images'][image_type] = None
        
        # 生成缩略图
        if front_image_path and os.path.exists(front_image_path):
            logger.info(f"正在生成缩略图，front_image_path: {front_image_path}")
            thumbnail_filename = 'thumbnail.jpg'
            thumbnail_path = os.path.join(part_dir, thumbnail_filename)
            if self._generate_thumbnail(front_image_path, thumbnail_path):
                results['thumbnail_url'] = f"/uploads/images/{part_code}/{thumbnail_filename}"
                logger.info(f"缩略图生成成功: {results['thumbnail_url']}")
            else:
                logger.error("缩略图生成失败")
        else:
            logger.warning(f"无法生成缩略图：front_image_path不存在或为None，front_image_path: {front_image_path}")
        
        logger.info(f"图片生成完成，results: {results}")
        return results
    
    def get_image_types(self):
        """获取图片类型列表"""
        return [
            ('front', '正面图'),
            ('side', '侧面图'),
            ('detail', '详细图'),
            ('circuit', '电路图'),
            ('perspective', '透视图'),
            ('thumbnail', '缩略图')
        ]
    
    def generate_single_image_by_type(self, part_code, part_name, supplier_name, image_type):
        """
        根据图片类型生成单张图片
        
        Args:
            part_code: 备件代码
            part_name: 备件名称
            supplier_name: 供应商名称
            image_type: 图片类型
        
        Returns:
            dict: 包含生成的图片路径信息
        """
        part_dir = self._get_part_dir(part_code)
        
        if image_type == 'thumbnail':
            # 生成缩略图
            front_path = os.path.join(part_dir, 'front.jpg')
            if not os.path.exists(front_path):
                return {
                    'success': False,
                    'message': '正面图不存在，无法生成缩略图'
                }
            
            thumbnail_filename = 'thumbnail.jpg'
            thumbnail_path = os.path.join(part_dir, thumbnail_filename)
            if self._generate_thumbnail(front_path, thumbnail_path):
                return {
                    'success': True,
                    'image_url': f"/uploads/images/{part_code}/{thumbnail_filename}"
                }
            else:
                return {
                    'success': False,
                    'message': '缩略图生成失败'
                }
        else:
            # 生成普通图片
            image_filename = f"{image_type}.jpg"
            image_path = os.path.join(part_dir, image_filename)
            prompt = self._generate_prompt(part_name, supplier_name, image_type)
            
            if self._generate_single_image(prompt, image_path):
                return {
                    'success': True,
                    'image_url': f"/uploads/images/{part_code}/{image_filename}"
                }
            else:
                return {
                    'success': False,
                    'message': '图片生成失败'
                }
