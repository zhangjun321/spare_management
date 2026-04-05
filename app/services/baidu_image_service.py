"""
百度文心一格图像生成服务
用于生成仓库实景图
使用 OpenAI SDK 方式调用百度千帆 API
"""

import os
import json
import base64
from datetime import datetime
from flask import current_app
from app.extensions import db

# 使用 OpenAI SDK 调用百度千帆
try:
    from openai import OpenAI
except ImportError:
    print("警告：未安装 openai 库，请运行：pip install openai")
    OpenAI = None


class BaiduImageGenerationService:
    """百度文心一格图像生成服务"""
    
    def __init__(self):
        self.api_key = os.getenv("BAIDU_API_KEY", "")
        self.client = None
        
        # 初始化 OpenAI 客户端（用于百度千帆）
        if OpenAI and self.api_key:
            self.client = OpenAI(
                base_url='https://qianfan.baidubce.com/v2',
                api_key=self.api_key
            )
            print("[INFO] 百度千帆 OpenAI 客户端初始化成功")
        elif not self.api_key:
            print("[WARNING] 未配置 BAIDU_API_KEY")
        else:
            print("[WARNING] 未安装 openai 库，图像生成功能不可用")
    
    def generate_warehouse_image(self, prompt, negative_prompt="", style="photorealistic", 
                                resolution="1024x768", steps=50):
        """
        生成仓库图像（使用 OpenAI SDK）
        
        Args:
            prompt: 提示词
            negative_prompt: 负面提示词
            style: 风格 (photorealistic/anime/artistic)
            resolution: 分辨率
            steps: 生成步数
        
        Returns:
            dict: 生成结果
        """
        if not self.client:
            return {"success": False, "error": "客户端未初始化"}
        
        # 根据风格调整参数
        guidance_map = {
            "photorealistic": 4,
            "anime": 7,
            "artistic": 5
        }
        guidance = guidance_map.get(style, 4)
        
        try:
            # 调用百度千帆图像生成 API（使用 SD-XL 模型）
            response = self.client.images.generate(
                model="stable-diffusion-xl",
                prompt=prompt,
                size=resolution,
                n=1,
                extra_body={
                    "steps": steps,
                    "guidance": guidance,
                    "negative_prompt": negative_prompt
                }
            )
            
            # 提取图像数据
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                return {
                    "success": True,
                    "images": [image_url] if image_url else [],
                    "response": str(response)
                }
            else:
                return {"success": False, "error": "无图像数据返回"}
                
        except Exception as e:
            try:
                current_app.logger.error(f"生成图像异常：{str(e)}")
            except RuntimeError:
                print(f"[ERROR] Exception generating image: {str(e)}")
            return {"success": False, "error": str(e)}
    

    
    def generate_warehouse_realistic_image(self, warehouse_data):
        """
        生成仓库实景图
        
        Args:
            warehouse_data: 仓库数据字典
        
        Returns:
            dict: 生成结果
        """
        # 将仓库数据转换为提示词
        prompt = self._build_warehouse_prompt(warehouse_data)
        negative_prompt = self._build_negative_prompt()
        
        # 生成图像
        result = self.generate_warehouse_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            style="photorealistic",
            resolution="1024x768",
            steps=25
        )
        
        return result
    
    def _build_warehouse_prompt(self, warehouse_data):
        """
        构建仓库提示词
        
        Args:
            warehouse_data: 仓库数据
        
        Returns:
            str: 提示词
        """
        # 基础描述
        base_prompt = "专业的现代化仓库内部，高清摄影，真实场景"
        
        # 仓库类型
        warehouse_type = warehouse_data.get("type", "general")
        type_descriptions = {
            "general": "普通干货仓库",
            "cold": "冷链冷藏仓库",
            "hazardous": "危险品专用仓库",
            "valuable": "贵重物品仓库"
        }
        type_desc = type_descriptions.get(warehouse_type, "普通仓库")
        
        # 库区信息
        zones = warehouse_data.get("zones", [])
        zone_desc = ""
        if zones:
            zone_names = [z.get("name", "") for z in zones if z.get("name")]
            if zone_names:
                zone_desc = f"包含{','.join(zone_names)}等功能区域"
        
        # 货架信息
        racks = warehouse_data.get("racks", [])
        rack_desc = ""
        if racks:
            rack_types = set()
            for rack in racks:
                rack_type = rack.get("type", "")
                if rack_type:
                    rack_types.add(rack_type)
            
            if rack_types:
                rack_desc = f"配置{'、'.join(rack_types)}等多种货架"
            else:
                rack_desc = "配置多层重型货架"
        
        # 备件信息
        parts = warehouse_data.get("parts", [])
        parts_desc = ""
        if parts:
            part_categories = set()
            for part in parts:
                category = part.get("category", "")
                if category:
                    part_categories.add(category)
            
            if part_categories:
                parts_desc = f"存储{'、'.join(part_categories)}等工业备件"
            else:
                parts_desc = "存储各类工业备件和配件"
        
        # 环境描述
        environment = [
            "宽敞明亮",
            "整洁有序",
            "专业照明",
            "环氧树脂地面",
            "清晰的区域标识",
            "消防通道畅通",
            "安全标识完善"
        ]
        
        # 摄影参数
        photography = [
            "专业摄影",
            "超高清 8K",
            "广角镜头",
            "景深效果",
            "自然光照",
            "细节清晰",
            "色彩真实"
        ]
        
        # 组合提示词
        prompt_parts = [
            base_prompt,
            type_desc,
            zone_desc,
            rack_desc,
            parts_desc,
            ",".join(environment),
            ",".join(photography)
        ]
        
        # 过滤空值并组合
        prompt = "，".join([p for p in prompt_parts if p and p.strip()])
        
        return prompt
    
    def _build_negative_prompt(self):
        """构建负面提示词"""
        negative_elements = [
            "模糊", "低质量", "失真", "变形",
            "卡通", "动漫", "手绘", "插画",
            "过暗", "过曝", "噪点", "水印",
            "文字", "标志", "品牌",
            "杂乱", "脏乱", "破旧"
        ]
        
        return ",".join(negative_elements)
    
    def save_image(self, image_data, save_path):
        """
        保存图像到本地
        
        Args:
            image_data: 图像数据（base64 或 URL）
            save_path: 保存路径
        """
        try:
            import requests
            # 如果是 base64 数据
            if image_data.startswith("data:image"):
                # 提取 base64 部分
                base64_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(base64_data)
                
                with open(save_path, "wb") as f:
                    f.write(image_bytes)
                
                return {"success": True, "path": save_path}
            
            # 如果是 URL，下载图像
            else:
                response = requests.get(image_data)
                if response.status_code == 200:
                    with open(save_path, "wb") as f:
                        f.write(response.content)
                    return {"success": True, "path": save_path}
                else:
                    return {"success": False, "error": "下载失败"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局服务实例
baidu_image_service = BaiduImageGenerationService()
