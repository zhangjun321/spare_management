# -*- coding: utf-8 -*-
"""
测试解析实际的 debug 文件
"""

import json
import re

def parse_json_response(content):
    """解析 AI 返回的 JSON 内容"""
    # 清理 markdown 代码块标记
    content = content.strip()
    if content.startswith('```'):
        content = content.split('```')[1]
        if content.startswith('json'):
            content = content[4:]
        content = content.strip()
    if content.endswith('```'):
        content = content[:-3].strip()
    
    print(f"清理后内容长度：{len(content)}")
    print(f"前 50 字符：{content[:50]}")
    print(f"后 50 字符：{content[-50:]}")
    
    try:
        # 尝试直接解析
        data = json.loads(content)
        if isinstance(data, list):
            print(f"✓ 直接解析成功，共 {len(data)} 条")
            return data
    except Exception as e:
        print(f"✗ 直接解析失败：{e}")
    
    # 尝试提取 JSON 部分
    json_pattern = r'\[[\s\S]*\]'
    match = re.search(json_pattern, content)
    
    if match:
        json_str = match.group()
        print(f"提取的 JSON 长度：{len(json_str)}")
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                print(f"✓ 提取解析成功，共 {len(data)} 条")
                return data
        except Exception as e:
            print(f"✗ 提取解析失败：{e}")
    else:
        print("✗ 未找到 JSON 数组")
    
    return []


# 读取 debug 文件
with open('d:/Trae/spare_management/data/debug_A_205153.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("="*70)
print("测试解析实际文件")
print("="*70)
print(f"原始内容长度：{len(content)}")

result = parse_json_response(content)

if result:
    print(f"\n✓ 解析成功！共 {len(result)} 条数据")
    for i, item in enumerate(result[:3], 1):
        print(f"  {i}. {item['part_name']}: ¥{item['unit_price']}")
else:
    print("\n✗ 解析失败")
