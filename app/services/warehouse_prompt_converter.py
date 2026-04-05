"""
仓库布局数据转换器
将仓库数据转换为图像生成提示词
优化版本 - 使用更简洁有效的提示词
"""

from typing import Dict, List, Optional


class WarehousePromptConverter:
    """仓库布局数据到提示词的转换器"""
    
    @staticmethod
    def convert(warehouse_data: Dict) -> str:
        """
        将仓库数据转换为提示词（优化版本）
        
        Args:
            warehouse_data: 仓库数据字典
        
        Returns:
            str: 生成的提示词
        """
        warehouse_name = warehouse_data.get("name", "Warehouse")
        
        # 使用简洁但明确的英文提示词
        prompt_parts = [
            f"Modern warehouse interior, {warehouse_name}",
            "industrial storage facility",
            "metal shelving units",
            "pallet racks with boxes",
            "clean and organized",
            "bright overhead lighting",
            "concrete floor",
            "wide aisles between shelves",
            "realistic photography",
            "high detail",
            "8k resolution"
        ]
        
        return ", ".join(prompt_parts)
    
    @staticmethod
    def build_negative_prompt() -> str:
        """构建负面提示词（简化版本）"""
        negative_elements = [
            "blurry",
            "low quality",
            "cartoon",
            "anime",
            "illustration",
            "painting",
            "drawing",
            "3d render",
            "text",
            "watermark",
            "people",
            "animals",
            "outdoor",
            "windows"
        ]
        
        return ", ".join(negative_elements)
    
    @staticmethod
    def generate_variation_prompt(base_prompt: str, focus: str = "") -> str:
        """
        生成变体提示词
        
        Args:
            base_prompt: 基础提示词
            focus: 焦点
        
        Returns:
            str: 变体提示词
        """
        variations = {
            "entrance": "view from the entrance",
            "center": "wide angle view from center",
            "shelves": "close up of shelves",
            "path": "view down the main aisle",
            "aerial": "high angle overview"
        }
        
        variation = variations.get(focus, "")
        
        if variation:
            return f"{base_prompt}, {variation}"
        return base_prompt


# 全局转换器实例
warehouse_prompt_converter = WarehousePromptConverter()
