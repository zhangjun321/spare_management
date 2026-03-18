# -*- coding: utf-8 -*-
"""
使用硅基流动 API 生成 100 条真实备件数据
具备三级分类、标准化编码、AI 检测功能
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


class SparePartsDataGenerator:
    """备件数据生成器"""
    
    def __init__(self):
        self.api_key = API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.generated_parts = []
    
    def generate_by_category(self, category_name, category_code, count):
        """
        按分类生成备件数据
        
        Args:
            category_name: 大类名称（如"机械传动件"）
            category_code: 大类代码（如"A"）
            count: 生成数量
        """
        print(f"\n{'='*60}")
        print(f"正在生成 {category_name} ({category_code}类) - {count}条数据")
        print(f"{'='*60}")
        
        prompt = self._build_generation_prompt(category_name, category_code, count)
        
        try:
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
            
            response = requests.post(API_URL, headers=self.headers, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 提取 JSON 数据
            parts_data = self._extract_json(content)
            
            # 验证和补充数据
            validated_parts = self._validate_and_enrich(parts_data, category_code)
            
            self.generated_parts.extend(validated_parts)
            
            print(f"✓ 成功生成 {len(validated_parts)} 条数据")
            
            return validated_parts
            
        except Exception as e:
            print(f"✗ 生成失败：{str(e)}")
            return []
    
    def _build_generation_prompt(self, category_name, category_code, count):
        """构建生成提示词"""
        
        # 定义各分类的子类
        subcategories = {
            "A": ["轴承类", "齿轮类", "皮带链条类", "联轴器类", "导轨丝杆类"],
            "B": ["液压泵类", "液压阀类", "液压缸类", "气动元件", "密封件"],
            "C": ["开关类", "继电器类", "传感器类", "变频器类", "电线电缆"],
            "D": ["螺栓类", "螺母类", "螺钉类", "垫圈类", "挡圈销类"],
            "E": ["润滑油品", "润滑脂类", "润滑装置", "机械密封", "密封垫片"],
            "F": ["过滤器类", "滤芯类", "滤网类", "除尘器", "净化装置"]
        }
        
        brands = {
            "A": ["SKF", "FAG", "NSK", "TIMKEN", "INA", "HRB", "ZWZ", "LYC"],
            "B": ["SMC", "FESTO", "PARKER", "REXROTH", "YUKEN", "AirTAC"],
            "C": ["SIEMENS", "ABB", "SCHNEIDER", "OMRON", "MITSUBISHI", "CHNT"],
            "D": ["PEM", "SOUTHCO", "WD", "GEM", "BOSSARD"],
            "E": ["SHELL", "MOBIL", "CASTROL", "TOTAL", "GREATWALL"],
            "F": ["PALL", "PARKER", "Donaldson", "MANN", "WIX"]
        }
        
        return f"""
请生成{count}条{category_name}类（分类代码：{category_code}）的工业备件数据。

## 分类结构
{category_name}包含以下子类：
{', '.join(subcategories.get(category_code, []))}

## 品牌要求
主要使用以下品牌（可补充其他知名品牌）：
{', '.join(brands.get(category_code, ['知名品牌']))}

## 数据字段要求
每条数据必须包含以下字段：
1. part_name: 备件名称（格式：品牌 + 品类 + 关键参数）
2. spec_model: 规格型号（具体型号，符合行业标准）
3. category_code: 三级分类代码（格式：{category_code}.XX.XX）
4. category_name: 分类名称
5. unit: 单位（个/套/米/千克等标准单位）
6. unit_price: 单价（人民币，合理市场价，保留 2 位小数）
7. supplier: 供应商（真实的供应商名称，如"上海 SKF 授权经销商"）
8. brand: 品牌
9. material: 材质（如"轴承钢"、"不锈钢"、"碳钢"等）
10. weight: 重量（kg，保留 3 位小数）
11. safety_stock: 安全库存（根据价值和用量，10-100）

## 质量要求
1. 品牌分布：国际品牌 60%，国内品牌 30%，通用件 10%
2. 价格范围：
   - 低价件 (<100 元): 40%
   - 中价件 (100-1000 元): 40%
   - 高价件 (1000-5000 元): 15%
   - 超高价件 (>5000 元): 5%
3. 供应商必须为真实存在的正规供应商
4. 规格型号必须符合行业标准
5. 材质描述要准确专业

## 输出格式
输出纯 JSON 数组，不要任何其他说明文字。格式如下：
[
  {{
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
  }}
]

现在请生成{count}条数据：
"""
    
    def _extract_json(self, content):
        """从 AI 响应中提取 JSON"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except:
            # 查找 JSON 块
            import re
            json_pattern = r'\[\s*\{.*?\}\s*\]'
            matches = re.findall(json_pattern, content, re.DOTALL)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except:
                    print("⚠ JSON 解析失败，返回空列表")
                    return []
            else:
                print("⚠ 未找到 JSON 数据，返回空列表")
                return []
    
    def _validate_and_enrich(self, parts_data, category_code):
        """验证和补充数据"""
        validated = []
        
        for i, part in enumerate(parts_data):
            try:
                # 验证必填字段
                required_fields = ['part_name', 'spec_model', 'category_code', 
                                   'unit', 'unit_price', 'supplier', 'brand']
                
                if not all(field in part for field in required_fields):
                    print(f"  ⚠ 第{i+1}条数据缺少必填字段，跳过")
                    continue
                
                # 补充默认值
                part.setdefault('material', '未知材质')
                part.setdefault('weight', 0.000)
                part.setdefault('safety_stock', 10)
                part.setdefault('category_name', '')
                
                # 生成备件编码
                part['part_code'] = self._generate_part_code(part, category_code, len(validated) + 1)
                
                # 添加 AI 检测标记
                part['ai_checked'] = False
                part['ai_score'] = 0.0
                part['ai_issues'] = ''
                part['ai_suggestions'] = ''
                
                validated.append(part)
                
            except Exception as e:
                print(f"  ✗ 第{i+1}条数据处理失败：{e}")
                continue
        
        return validated
    
    def _generate_part_code(self, part, category_code, index):
        """
        生成标准化备件编码
        格式：品牌代码 (4 位) + 分类代码 (6 位) + 规格代码 (3 位) + 流水号 (3 位)
        """
        # 品牌代码映射
        brand_codes = {
            'SKF': 'SKF0', 'FAG': 'FAG0', 'NSK': 'NSK0', 'TIMKEN': 'TIMK',
            'INA': 'INAF', 'SIEMENS': 'SIME', 'ABB': 'ABBC', 'SCHNEIDER': 'SCHN',
            'OMRON': 'OMRN', 'MITSUBISHI': 'MITS', 'SMC': 'SMC0', 'FESTO': 'FEST',
            'PARKER': 'PARK', 'REXROTH': 'REXR', 'SHELL': 'SHEL', 'MOBIL': 'MOBI',
            'HRB': 'HRB0', 'ZWZ': 'ZWZ0', 'LYC': 'LYC0', 'CHNT': 'CHNT',
        }
        
        brand_code = brand_codes.get(part.get('brand', '').upper(), 'GEN0')
        
        # 规格代码（简化处理，按价格区间）
        price = part.get('unit_price', 0)
        if price < 100:
            spec_code = '001'
        elif price < 500:
            spec_code = '002'
        elif price < 1000:
            spec_code = '003'
        elif price < 5000:
            spec_code = '004'
        else:
            spec_code = '005'
        
        # 流水号
        serial = f'{index:03d}'
        
        # 组合编码
        part_code = f"{brand_code}-{category_code}-{spec_code}-{serial}"
        
        return part_code
    
    def save_to_json(self, filename='spare_parts_data.json'):
        """保存数据到 JSON 文件"""
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.generated_parts, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 数据已保存到：{filepath}")
        print(f"  总计：{len(self.generated_parts)} 条记录")
        
        return filepath
    
    def save_to_csv(self, filename='spare_parts_data.csv'):
        """保存数据到 CSV 文件"""
        import csv
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        if not self.generated_parts:
            print("✗ 没有数据可保存")
            return filepath
        
        fieldnames = ['part_code', 'part_name', 'spec_model', 'category_code', 
                      'category_name', 'unit', 'unit_price', 'supplier', 'brand',
                      'material', 'weight', 'safety_stock']
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.generated_parts)
        
        print(f"✓ CSV 数据已保存到：{filepath}")
        
        return filepath


def main():
    """主函数"""
    print("="*70)
    print("硅基流动 AI - 备件数据生成工具")
    print("="*70)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录：{OUTPUT_DIR}")
    print("="*70)
    
    generator = SparePartsDataGenerator()
    
    # 按分类生成数据（共 100 条）
    categories = [
        ("A", "机械传动件", 25),
        ("B", "液压气动件", 20),
        ("C", "电气元件", 20),
        ("D", "紧固件", 15),
        ("E", "润滑密封件", 10),
        ("F", "过滤净化件", 10),
    ]
    
    total_count = 0
    
    for category_code, category_name, count in categories:
        parts = generator.generate_by_category(category_name, category_code, count)
        total_count += len(parts)
        
        # 每生成一个分类，等待 5 秒避免 API 限流
        import time
        time.sleep(5)
    
    # 保存数据
    generator.save_to_json()
    generator.save_to_csv()
    
    print("\n" + "="*70)
    print("生成完成！")
    print("="*70)
    print(f"总记录数：{total_count}")
    print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    main()
