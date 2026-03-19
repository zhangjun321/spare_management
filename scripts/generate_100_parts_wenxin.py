# -*- coding: utf-8 -*-
"""
使用百度文心一言 AI 生成 100 条备件数据并导入 MySQL 数据库
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 百度文心一言 API 配置
API_KEY = os.getenv('BAIDU_API_KEY', '')

# Flask 应用配置
os.environ['FLASK_ENV'] = 'development'


def get_access_token():
    """获取文心一言 API 的 access token"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": API_KEY  # 千帆平台使用相同的 key
    }
    
    response = requests.post(url, params=params)
    result = response.json()
    
    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"获取 access_token 失败：{result}")
        return None


def generate_parts_with_wenxin():
    """使用文心一言生成 100 条备件数据"""
    print("="*80)
    print("百度文心一言 AI - 生成 100 条备件数据")
    print("="*80)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if not API_KEY:
        print("\n✗ 错误：请先配置 BAIDU_API_KEY")
        return []
    
    print(f"\n✓ API Key 已配置：{API_KEY[:20]}...")
    
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
        
        # 分批生成，每批 5 条，避免超出 token 限制
        batch_size = 5
        category_parts = []
        
        for batch in range(0, count, batch_size):
            current_batch = min(batch_size, count - batch)
            print(f"\n  生成批次 {batch//batch_size + 1}/{(count + batch_size - 1)//batch_size}...")
            batch_parts = generate_category_parts(category_code, category_name, current_batch, API_KEY)
            category_parts.extend(batch_parts)
        
        print(f"✓ 本类已生成 {len(category_parts)} 条数据")
        all_parts.extend(category_parts)
    
    print(f"\n{'='*80}")
    print(f"生成完成！共生成 {len(all_parts)} 条备件数据")
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    return all_parts


def generate_category_parts(category_code, category_name, count, access_token):
    """生成指定分类的备件数据"""
    
    # 输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备分类子类和品牌信息
    subcategories = get_subcategories(category_code)
    brands = get_brands(category_code)
    
    # 构建 prompt
    prompt = f"""你是一位专业的工业备件数据专家。请生成{count}条{category_name}的备件数据。

要求：
1. 备件名称要专业、准确，包含品牌、型号、规格
2. 型号必须是真实存在的工业备件型号
3. 品牌从以下选择：{', '.join(brands)}
4. 分类代码：{category_code}，子类从以下选择：{subcategories}
5. 价格要符合市场行情（人民币元）
6. 供应商名称要真实可信
7. 材质、规格等参数要专业准确

请严格按照以下 JSON 格式输出（不要输出其他内容）：
[
  {{
    "part_name": "备件名称（包含品牌和型号）",
    "specification": "规格型号",
    "category_name": "具体分类名称",
    "category_code": "分类代码（如 A.01.01）",
    "brand": "品牌",
    "material": "材质",
    "unit_price": 价格（数字），
    "supplier": "供应商名称",
    "stock_status": "充足/紧张/缺货"
  }}
]

确保生成的{count}条数据不重复，每条数据都有实际工业应用价值。"""

    # 调用文心一言 API（千帆平台）
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "model": "ernie-4.0-turbo-8k",  # 使用文心一言 4.0 模型
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_completion_tokens": 2048  # 最大 2048
    }
    
    print(f"  🔄 调用文心一言 API...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 调试输出
            if not content:
                print(f"  ⚠️ API 返回空内容")
                print(f"  完整响应：{result}")
                return []
            
            # 保存原始响应到文件（调试用）
            debug_file = os.path.join(output_dir, f'debug_{category_code}_{datetime.now().strftime("%H%M%S")}.txt')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📄 原始响应已保存到：{debug_file}")
            
            # 解析 JSON
            parts_data = parse_json_response(content)
            
            if parts_data:
                # 添加标准化编码
                for i, part in enumerate(parts_data, 1):
                    part['part_code'] = generate_part_code(part.get('brand', ''), category_code, i)
                
                print(f"  ✓ 成功生成 {len(parts_data)} 条数据")
                return parts_data
            else:
                print(f"  ✗ 解析 JSON 失败")
                print(f"  API 返回内容：{content[:500]}")
                return []
        else:
            print(f"  ✗ API 调用失败：{response.status_code}")
            print(f"  错误信息：{response.text}")
            return []
            
    except Exception as e:
        print(f"  ✗ 发生错误：{str(e)}")
        return []


def get_subcategories(category_code):
    """获取分类的子类列表"""
    subcategories_map = {
        "A": ["A.01.01 轴承", "A.01.02 齿轮", "A.01.03 联轴器", "A.02.01 皮带", "A.02.02 链条", "A.03.01 电机", "A.03.02 减速机"],
        "B": ["B.01.01 液压缸", "B.01.02 液压泵", "B.02.01 气缸", "B.02.02 气阀", "B.03.01 油管", "B.03.02 接头"],
        "C": ["C.01.01 开关", "C.01.02 传感器", "C.02.01 继电器", "C.02.02 断路器", "C.03.01 电缆", "C.03.02 接线端子"],
        "D": ["D.01.01 螺栓", "D.01.02 螺母", "D.02.01 螺钉", "D.02.02 垫圈", "D.03.01 铆钉", "D.03.02 销"],
        "E": ["E.01.01 润滑油", "E.01.02 润滑脂", "E.02.01 O 型圈", "E.02.02 密封垫", "E.03.01 油封", "E.03.02 密封圈"],
        "F": ["F.01.01 滤芯", "F.01.02 滤网", "F.02.01 过滤器", "F.02.02 滤清器", "F.03.01 除尘器", "F.03.02 净化装置"],
    }
    return ", ".join(subcategories_map.get(category_code, []))


def get_brands(category_code):
    """获取分类的常见品牌"""
    brands_map = {
        "A": ["SKF", "FAG", "NSK", "TIMKEN", "INA", "NTN", "KOYO"],
        "B": ["REXROTH", "PARKER", "SMC", "FESTO", "OMRON", "AirTAC"],
        "C": ["SIEMENS", "ABB", "Schneider", "OMRON", "Mitsubishi", "Phoenix Contact"],
        "D": ["BOSCH", "PEM", "SOUTHCO", "WD", "Hilti", "Bossard"],
        "E": ["Shell", "Mobil", "Castrol", "NOK", "SKF", "Garlock"],
        "F": ["Donaldson", "Pall", "HYDAC", "Parker", "3M", "Camfil"],
    }
    return brands_map.get(category_code, ["Generic"])


def generate_part_code(brand, category_code, sequence):
    """生成标准化备件代码"""
    # 品牌代码（4 位）
    brand_code = brand[:4].upper().ljust(4, 'X')
    
    # 分类代码（6 位）
    category_part = category_code.replace('.', '')
    
    # 规格代码（3 位）
    spec_code = f"{sequence:03d}"
    
    # 流水号（3 位）
    serial = f"{sequence:03d}"
    
    return f"{brand_code}-{category_part}-{spec_code}-{serial}"


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
    
    try:
        # 尝试直接解析
        data = json.loads(content)
        if isinstance(data, list):
            return data
    except:
        pass
    
    # 尝试提取 JSON 部分
    import re
    json_pattern = r'\[[\s\S]*\]'
    match = re.search(json_pattern, content)
    
    if match:
        try:
            json_str = match.group()
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
        except:
            pass
    
    return []


def save_to_file(parts_data, filename):
    """保存数据到文件"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存为 JSON
    json_path = os.path.join(output_dir, filename)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parts_data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 数据已保存到：{json_path}")
    
    # 保存为 CSV
    csv_path = json_path.replace('.json', '.csv')
    if parts_data:
        import csv
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=parts_data[0].keys())
            writer.writeheader()
            writer.writerows(parts_data)
        print(f"✓ CSV 已保存到：{csv_path}")


if __name__ == "__main__":
    # 生成数据
    parts_data = generate_parts_with_wenxin()
    
    if parts_data:
        # 保存数据
        filename = f"wenxin_parts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_to_file(parts_data, filename)
        
        print("\n" + "="*80)
        print("下一步：")
        print("1. 检查生成的数据文件")
        print("2. 运行 import_parts_to_db.py 导入数据库")
        print("="*80)
    else:
        print("\n✗ 数据生成失败")
