# -*- coding: utf-8 -*-
"""
更新轮播图组件，使用本地 AI 生成的图片
"""

import os
import re

# 模板目录
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'components')

# 页面映射关系
PAGE_MAPPING = {
    'carousel_spare_parts.html': 'spare_parts',
    'carousel_dashboard.html': 'dashboard',
    'carousel_warehouse.html': 'warehouse',
    'carousel_equipment.html': 'equipment',
    'carousel_maintenance.html': 'maintenance',
    'carousel_transaction.html': 'transaction',
    'carousel_purchase.html': 'purchase',
    'carousel_report.html': 'report'
}

def update_carousel_file(filename, page_prefix):
    """
    更新单个轮播图文件
    """
    filepath = os.path.join(TEMPLATES_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"✗ 文件不存在：{filename}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有图片链接
    for i in range(1, 7):
        # 匹配旧的图片标签（包含 onerror 的）
        old_pattern = rf'<img src="[^"]*"(?:\s+alt="[^"]*")?(?:\s+onerror="[^"]*")?'
        
        # 构建新的图片标签
        new_img = f'<img src="/static/images/carousel/{page_prefix}_{i:02d}.jpg" alt="{page_prefix} 图片{i}" loading="lazy">'
        
        # 找到第 i 个图片并替换
        count = 0
        def replace_func(match):
            nonlocal count
            count += 1
            if count == i:
                return new_img
            return match.group(0)
        
        # 更精确的替换：只替换 carousel-item 内的第一个 img 标签
        content = re.sub(
            rf'(<div class="carousel-item[^>]*>\s*<img )([^>]*)(.*?>)',
            lambda m: m.group(1) + f'src="/static/images/carousel/{page_prefix}_{i:02d}.jpg" alt="{page_prefix} 图片{i}" loading="lazy"' + m.group(3),
            content,
            count=1,
            flags=re.DOTALL
        )
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ 已更新：{filename}")
    return True

def main():
    """
    主函数
    """
    print("=" * 60)
    print("更新轮播图组件 - 使用本地 AI 图片")
    print("=" * 60)
    
    success = 0
    for filename, page_prefix in PAGE_MAPPING.items():
        if update_carousel_file(filename, page_prefix):
            success += 1
    
    print("=" * 60)
    print(f"完成！已更新 {success}/{len(PAGE_MAPPING)} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
