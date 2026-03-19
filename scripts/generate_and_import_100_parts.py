# -*- coding: utf-8 -*-
"""
使用 AI 生成 100 条备件数据并导入 MySQL 数据库
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 加载环境变量
load_dotenv()

# 硅基流动 API 配置
API_KEY = os.getenv('SILICONFLOW_API_KEY', 'sk-ojhphrjqyigzgskcackiaixmsznscynmhydoiayelgpmmitn')
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

# Flask 应用配置
os.environ['FLASK_ENV'] = 'development'


def generate_parts_with_ai():
    """使用 AI 生成 100 条备件数据"""
    print("="*80)
    print("硅基流动 AI - 生成 100 条备件数据")
    print("="*80)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    all_parts = []
    
    # 分 6 个大类生成
    categories = [
        ("A", "机械传动件", 25),
        ("B", "液压气动件", 20),
        ("C", "电气元件", 20),
        ("D", "紧固件", 15),
        ("E", "润滑密封件", 10),
        ("F", "过滤净化件", 10),
    ]
    
    for category_code, category_name, count in categories:
        print(f"\n{'='*80}")
        print(f"正在生成：{category_name} ({category_code}类) - {count}条")
        print(f"{'='*80}")
        
        parts = generate_category_parts(category_code, category_name, count)
        all_parts.extend(parts)
        print(f"✓ 已生成 {len(parts)} 条数据")
        
        # 延迟避免 API 限流
        import time
        time.sleep(3)
    
    print("\n" + "="*80)
    print(f"AI 数据生成完成！总计：{len(all_parts)} 条")
    print("="*80)
    
    return all_parts


def generate_category_parts(category_code, category_name, count):
    """生成指定分类的备件数据"""
    
    # 各分类的子类和品牌
    category_details = {
        "A": {
            "subcategories": ["轴承类", "齿轮类", "皮带链条类", "联轴器类", "导轨丝杆类"],
            "brands": ["SKF", "FAG", "NSK", "TIMKEN", "INA", "HRB", "ZWZ"]
        },
        "B": {
            "subcategories": ["液压泵", "液压阀", "液压缸", "气缸", "密封件"],
            "brands": ["SMC", "FESTO", "PARKER", "REXROTH", "YUKEN"]
        },
        "C": {
            "subcategories": ["开关", "继电器", "传感器", "变频器", "电线电缆"],
            "brands": ["SIEMENS", "ABB", "SCHNEIDER", "OMRON", "MITSUBISHI"]
        },
        "D": {
            "subcategories": ["螺栓", "螺母", "螺钉", "垫圈", "挡圈"],
            "brands": ["PEM", "SOUTHCO", "WD", "通用件"]
        },
        "E": {
            "subcategories": ["润滑油", "润滑脂", "润滑装置", "机械密封", "密封垫片"],
            "brands": ["SHELL", "MOBIL", "CASTROL", "TOTAL"]
        },
        "F": {
            "subcategories": ["过滤器", "滤芯", "滤网", "除尘器", "净化装置"],
            "brands": ["PALL", "PARKER", "Donaldson", "MANN"]
        }
    }
    
    details = category_details.get(category_code, {"subcategories": [], "brands": []})
    
    prompt = f"""
请生成{count}条{category_name}类工业备件数据。

## 分类信息
- 大类代码：{category_code}
- 子类范围：{', '.join(details['subcategories'])}
- 主要品牌：{', '.join(details['brands'])}

## 每条数据包含字段
1. part_name: 备件名称（品牌 + 品类 + 型号）
2. specification: 规格型号（具体型号）
3. category_name: 分类名称（从子类中选择）
4. unit: 单位（个/套/米/千克）
5. unit_price: 单价（人民币，保留 2 位小数）
6. supplier_name: 供应商名称（真实供应商）
7. brand: 品牌
8. current_stock: 当前库存（10-200）
9. min_stock: 最低库存（5-50）
10. location: 存放位置（如"A-01-02"）
11. remark: 备注（可选）

## 价格分布
- 低价件 (<100 元): 40%
- 中价件 (100-500 元): 40%
- 高价件 (500-2000 元): 15%
- 超高价件 (>2000 元): 5%

## 输出格式
纯 JSON 数组，不要其他说明文字。

示例：
[
  {{
    "part_name": "SKF 深沟球轴承 6205-2RS",
    "specification": "6205-2RS",
    "category_name": "轴承类",
    "unit": "个",
    "unit_price": 45.00,
    "supplier_name": "上海 SKF 授权经销商",
    "brand": "SKF",
    "current_stock": 50,
    "min_stock": 20,
    "location": "A-01-02",
    "remark": "常用备件"
  }}
]

现在请生成{count}条数据：
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
                "content": "你是工业备件数据专家，负责生成准确、规范、真实的备件数据。熟悉各类工业备件的品牌、型号、供应商、市场价格等信息。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        print("  🔄 调用 AI API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 提取 JSON
        parts_data = extract_json(content)
        
        if not parts_data:
            print("  ✗ JSON 解析失败")
            return []
        
        # 处理数据
        processed_parts = []
        for i, part in enumerate(parts_data, 1):
            try:
                # 生成备件代码
                part['part_code'] = generate_part_code(
                    part.get('brand', ''),
                    category_code,
                    part.get('unit_price', 0),
                    len(processed_parts) + 1
                )
                
                # 添加默认值
                part.setdefault('remark', '')
                part.setdefault('location', f"{category_code}-{len(processed_parts)+1:02d}-01")
                
                processed_parts.append(part)
                
            except Exception as e:
                print(f"  ⚠ 第{i}条数据处理失败：{e}")
                continue
        
        return processed_parts
        
    except requests.exceptions.Timeout:
        print("  ✗ 请求超时")
        return []
    except Exception as e:
        print(f"  ✗ 生成失败：{e}")
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
                return []
        else:
            return []


def generate_part_code(brand, category_code, price, index):
    """生成标准化备件代码"""
    brand_codes = {
        'SKF': 'SKF0', 'FAG': 'FAG0', 'NSK': 'NSK0', 'TIMKEN': 'TIMK',
        'INA': 'INAF', 'SIEMENS': 'SIME', 'ABB': 'ABBC', 'SCHNEIDER': 'SCHN',
        'OMRON': 'OMRN', 'MITSUBISHI': 'MITS', 'SMC': 'SMC0', 'FESTO': 'FEST',
        'PARKER': 'PARK', 'REXROTH': 'REXR', 'SHELL': 'SHEL', 'MOBIL': 'MOBI',
        'HRB': 'HRB0', 'ZWZ': 'ZWZ0', 'LYC': 'LYC0',
    }
    
    brand_code = brand_codes.get(brand.upper(), 'GEN0')
    
    # 规格代码
    if price < 100:
        spec_code = '001'
    elif price < 500:
        spec_code = '002'
    elif price < 2000:
        spec_code = '003'
    else:
        spec_code = '004'
    
    serial = f'{index:03d}'
    
    return f"{brand_code}-{category_code}.01.01-{spec_code}-{serial}"


def import_to_database(parts_data):
    """导入数据到 MySQL 数据库"""
    print("\n" + "="*80)
    print("正在导入数据到 MySQL 数据库...")
    print("="*80)
    
    try:
        # 导入 Flask 和 SQLAlchemy
        from app import create_app, db
        from app.models.spare_part import SparePart
        from app.models.category import Category
        from app.models.supplier import Supplier
        from datetime import datetime
        
        app = create_app()
        
        with app.app_context():
            success_count = 0
            fail_count = 0
            
            for i, part in enumerate(parts_data, 1):
                try:
                    print(f"[{i}/{len(parts_data)}] 导入：{part['part_name']}", end=" ")
                    
                    # 检查备件代码是否已存在
                    existing = SparePart.query.filter_by(part_code=part['part_code']).first()
                    if existing:
                        print("⚠ 已存在，跳过")
                        fail_count += 1
                        continue
                    
                    # 查找或创建分类
                    category = Category.query.filter_by(name=part['category_name']).first()
                    if not category:
                        # 创建新分类
                        category = Category(
                            name=part['category_name'],
                            code=f"{part['part_code'].split('-')[1][:8]}",  # 提取分类代码
                            parent_id=None,
                            level=2,
                            is_active=True
                        )
                        db.session.add(category)
                        db.session.flush()
                    
                    # 查找或创建供应商
                    supplier = Supplier.query.filter_by(name=part['supplier_name']).first()
                    if not supplier:
                        # 创建新供应商
                        supplier = Supplier(
                            name=part['supplier_name'],
                            code=f"SUP{len(parts_data)+i:04d}",
                            contact_person='',
                            contact_phone='',
                            contact_email='',
                            address='',
                            credit_level='B',
                            is_active=True
                        )
                        db.session.add(supplier)
                        db.session.flush()
                    
                    # 创建备件
                    spare_part = SparePart(
                        part_code=part['part_code'],
                        name=part['part_name'],
                        specification=part.get('specification', ''),
                        category_id=category.id,
                        supplier_id=supplier.id,
                        current_stock=part.get('current_stock', 0),
                        stock_status='normal',
                        min_stock=part.get('min_stock', 0),
                        max_stock=part.get('max_stock', 0),
                        unit=part.get('unit', '个'),
                        unit_price=part.get('unit_price', 0),
                        location=part.get('location', ''),
                        remark=part.get('remark', ''),
                        is_active=True,
                        created_by=1  # 默认管理员
                    )
                    
                    db.session.add(spare_part)
                    db.session.commit()
                    
                    print("✓ 成功")
                    success_count += 1
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"✗ 失败：{str(e)[:50]}")
                    fail_count += 1
            
            print("\n" + "="*80)
            print("数据库导入完成！")
            print("="*80)
            print(f"成功：{success_count} 条")
            print(f"失败：{fail_count} 条")
            print(f"成功率：{success_count/len(parts_data)*100:.1f}%")
            print("="*80)
            
            return success_count, fail_count
            
    except Exception as e:
        print(f"\n✗ 数据库导入失败：{e}")
        import traceback
        traceback.print_exc()
        return 0, len(parts_data)


def main():
    """主函数"""
    print("="*80)
    print("硅基流动 AI - 备件数据生成与数据库导入")
    print("="*80)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 步骤 1：生成数据
    parts_data = generate_parts_with_ai()
    
    if not parts_data:
        print("\n✗ 数据生成失败")
        return
    
    # 保存为 JSON 文件
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'ai_generated_parts_100.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parts_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 数据已保存到：{output_file}")
    
    # 步骤 2：导入数据库
    import_to_database(parts_data)
    
    print("\n" + "="*80)
    print("全部完成！")
    print("="*80)
    print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    main()
