# -*- coding: utf-8 -*-
"""
批量更新所有轮播图组件，使用本地 AI 生成的图片
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
    
    # 使用正则表达式替换所有图片标签
    # 匹配 <img 开头到 > 结束的所有内容
    img_pattern = r'<img\s+[^>]*>'
    
    # 计数器
    img_count = [0]
    
    def replace_img(match):
        img_count[0] += 1
        if img_count[0] <= 6:  # 只替换前 6 个图片
            return f'<img src="/static/images/carousel/{page_prefix}_{img_count[0]:02d}.jpg" alt="{page_prefix} 图片{img_count[0]}" loading="lazy">'
        return match.group(0)
    
    # 替换所有图片标签
    new_content = re.sub(img_pattern, replace_img, content)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ 已更新：{filename} (6 张图片)")
    return True

def main():
    """
    主函数
    """
    print("=" * 70)
    print("批量更新轮播图组件 - 使用本地 AI 图片")
    print("=" * 70)
    print(f"模板目录：{TEMPLATES_DIR}")
    print()
    
    success = 0
    for filename, page_prefix in PAGE_MAPPING.items():
        print(f"[{success + 1}/{len(PAGE_MAPPING)}] 处理：{filename}", end=" -> ")
        if update_carousel_file(filename, page_prefix):
            success += 1
    
    print()
    print("=" * 70)
    print(f"完成！已更新 {success}/{len(PAGE_MAPPING)} 个文件")
    print("=" * 70)
    print()
    print("已更新的轮播图：")
    for filename in PAGE_MAPPING.keys():
        print(f"  ✓ {filename}")
    print()

if __name__ == "__main__":
    main()
