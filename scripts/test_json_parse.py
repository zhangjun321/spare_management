# -*- coding: utf-8 -*-
"""
测试 JSON 解析逻辑
"""

import json
import re

def parse_json_response(content):
    """解析 AI 返回的 JSON 内容"""
    print(f"原始内容长度：{len(content)}")
    print(f"前 100 字符：{content[:100]}")
    
    # 清理 markdown 代码块标记
    content = content.strip()
    if content.startswith('```'):
        content = content.split('```')[1]
        if content.startswith('json'):
            content = content[4:]
        content = content.strip()
    if content.endswith('```'):
        content = content[:-3].strip()
    
    print(f"清理后长度：{len(content)}")
    print(f"前 100 字符：{content[:100]}")
    
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


# 测试数据
test_content = """```json
[
    {
        "part_name": "SKF 6204-2RS1 深沟球轴承",
        "specification": "6204-2RS1, 内径 20mm, 外径 47mm, 宽度 14mm",
        "category_name": "轴承",
        "category_code": "A.01.01",
        "brand": "SKF",
        "material": "高碳铬轴承钢",
        "unit_price": 45,
        "supplier": "上海轴承贸易有限公司",
        "stock_status": "充足"
    },
    {
        "part_name": "FAG NU2206-E-TVP2 圆柱滚子轴承",
        "specification": "NU2206-E-TVP2, 内径 30mm, 外径 62mm, 宽度 20mm",
        "category_name": "轴承",
        "category_code": "A.01.01",
        "brand": "FAG",
        "material": "GCr15",
        "unit_price": 85,
        "supplier": "FAG 工业公司",
        "stock_status": "充足"
    }
]
```"""

print("="*70)
print("测试 JSON 解析")
print("="*70)

result = parse_json_response(test_content)

if result:
    print(f"\n✓ 解析成功！共 {len(result)} 条数据")
    for item in result:
        print(f"  - {item['part_name']}: ¥{item['unit_price']}")
else:
    print("\n✗ 解析失败")
