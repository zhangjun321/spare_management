# -*- coding: utf-8 -*-
"""
测试脚本 - 生成 10 条备件数据验证功能
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 硅基流动 API 配置
API_KEY = os.getenv('SILICONFLOW_API_KEY', 'sk-ojhphrjqyigzgskcackiaixmsznscynmhydoiayelgpmmitn')
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_test_data():
    """生成 10 条测试数据"""
    print("="*70)
    print("硅基流动 AI - 备件数据生成测试（10 条）")
    print("="*70)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    prompt = """
请生成 10 条工业备件数据用于测试，要求：

## 数据分布
- 机械传动件：3 条（轴承、齿轮、皮带）
- 电气元件：3 条（开关、继电器、传感器）
- 液压气动：2 条（气缸、液压阀）
- 紧固件：2 条（螺栓、螺母）

## 每条数据包含字段
1. part_name: 备件名称（品牌 + 品类 + 型号）
2. spec_model: 规格型号
3. category_code: 三级分类代码（格式：A.01.01）
4. category_name: 分类名称
5. unit: 单位（个/套等）
6. unit_price: 单价（人民币，保留 2 位小数）
7. supplier: 供应商（真实供应商名称）
8. brand: 品牌
9. material: 材质
10. weight: 重量（kg，保留 3 位小数）
11. safety_stock: 安全库存

## 输出格式
纯 JSON 数组，不要其他说明文字。

示例：
[
  {
    "part_name": "SKF 深沟球轴承",
    "spec_model": "6205-2RS",
    "category_code": "A.01.01",
    "category_name": "深沟球轴承",
    "unit": "个",
    "unit_price": 45.00,
    "supplier": "上海 SKF 授权经销商",
    "brand": "SKF",
    "material": "GCr15 轴承钢",
    "weight": 0.150,
    "safety_stock": 20
  }
]

现在请生成 10 条测试数据：
"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是工业备件数据专家，负责生成准确、规范、真实的备件数据。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }
    
    try:
        print("\n🔄 正在调用 AI API 生成数据...")
        print("⏳ 这可能需要 20-40 秒，请耐心等待...\n")
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 提取 JSON 数据
        print("✓ AI 响应接收成功")
        print("📝 正在解析 JSON 数据...\n")
        
        parts_data = extract_json(content)
        
        if not parts_data:
            print("✗ JSON 解析失败")
            return []
        
        # 生成备件编码
        print("🔧 正在生成标准化编码...")
        for i, part in enumerate(parts_data, 1):
            part['part_code'] = generate_part_code(part, i)
            print(f"  [{i}/{len(parts_data)}] {part['part_name']} -> {part['part_code']}")
        
        # 保存数据
        save_to_json(parts_data)
        save_to_csv(parts_data)
        
        print("\n" + "="*70)
        print("✅ 测试数据生成成功！")
        print("="*70)
        print(f"生成数量：{len(parts_data)} 条")
        print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        return parts_data
        
    except requests.exceptions.Timeout:
        print("\n✗ 请求超时，请检查网络连接")
        return []
    except Exception as e:
        print(f"\n✗ 生成失败：{str(e)}")
        return []


def extract_json(content):
    """从 AI 响应中提取 JSON"""
    import re
    
    try:
        # 尝试直接解析
        return json.loads(content)
    except:
        # 查找 JSON 数组
        json_pattern = r'\[\s*\{.*?\}\s*\]'
        matches = re.findall(json_pattern, content, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except:
                print("⚠ JSON 解析失败")
                return []
        else:
            print("⚠ 未找到 JSON 数据")
            return []


def generate_part_code(part, index):
    """生成标准化备件编码"""
    brand_codes = {
        'SKF': 'SKF0', 'FAG': 'FAG0', 'NSK': 'NSK0', 'TIMKEN': 'TIMK',
        'INA': 'INAF', 'SIEMENS': 'SIME', 'ABB': 'ABBC', 'SCHNEIDER': 'SCHN',
        'OMRON': 'OMRN', 'MITSUBISHI': 'MITS', 'SMC': 'SMC0', 'FESTO': 'FEST',
        'PARKER': 'PARK', 'REXROTH': 'REXR', 'SHELL': 'SHEL', 'MOBIL': 'MOBI',
        'HRB': 'HRB0', 'ZWZ': 'ZWZ0', 'LYC': 'LYC0', 'CHNT': 'CHNT',
    }
    
    brand_code = brand_codes.get(part.get('brand', '').upper(), 'GEN0')
    category_code = part.get('category_code', 'A.01.01')
    spec_code = '001' if part.get('unit_price', 0) < 100 else '002'
    serial = f'{index:03d}'
    
    return f"{brand_code}-{category_code}-{spec_code}-{serial}"


def save_to_json(parts_data):
    """保存 JSON 格式"""
    filepath = os.path.join(OUTPUT_DIR, 'test_parts_data.json')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(parts_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ JSON 数据已保存：{filepath}")


def save_to_csv(parts_data):
    """保存 CSV 格式"""
    import csv
    
    filepath = os.path.join(OUTPUT_DIR, 'test_parts_data.csv')
    
    fieldnames = ['part_code', 'part_name', 'spec_model', 'category_code', 
                  'category_name', 'unit', 'unit_price', 'supplier', 'brand',
                  'material', 'weight', 'safety_stock']
    
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parts_data)
    
    print(f"✓ CSV 数据已保存：{filepath}")


def main():
    """主函数"""
    parts_data = generate_test_data()
    
    if parts_data:
        print("\n📊 数据预览：")
        print("-" * 70)
        for i, part in enumerate(parts_data, 1):
            print(f"{i:2d}. {part['part_code']} | {part['part_name']:20s} | {part['brand']:8s} | ¥{part['unit_price']:8.2f}")
        print("-" * 70)
        
        print("\n💡 下一步操作：")
        print("1. 检查生成的数据是否正确")
        print("2. 运行 AI 检测：python scripts/ai_parts_checker.py")
        print("3. 查看检测报告：data/test_parts_data.json")
        print("\n✅ 如果测试成功，可以运行完整脚本生成 100 条数据：")
        print("   python scripts/generate_spare_parts_data.py")


if __name__ == "__main__":
    main()
