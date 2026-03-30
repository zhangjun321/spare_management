# -*- coding: utf-8 -*-
"""
调用文心一言API分析备件数据，进行设计分析和功能分析，以及适配度，并使用AI自动创建初始化的仓库数据
"""

import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.extensions import db
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation
from app.models.batch import Batch

load_dotenv()

# 文心一言 API 配置
API_KEY = os.getenv('BAIDU_API_KEY', '')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

# 获取 access token
def get_access_token():
    """获取文心一言 API 的 access token"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    
    response = requests.post(url, params=params)
    result = response.json()
    print(f"获取 access token 响应：{result}")
    return result.get("access_token")

# 调用文心一言 API
def call_wenxin_api(messages, max_tokens=2000):
    """调用文心一言 API"""
    access_token = get_access_token()
    if not access_token:
        print("✗ 获取 access token 失败")
        return None
    
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": messages,
        "max_output_tokens": max_tokens
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return result.get('result', '')
    else:
        print(f"✗ API 调用失败：{response.text}")
        return None

# 获取备件数据
def get_spare_parts_data():
    """获取当前备件数据"""
    parts = SparePart.query.all()
    categories = Category.query.all()
    
    parts_data = []
    for part in parts:
        parts_data.append({
            "part_code": part.part_code,
            "name": part.name,
            "specification": part.specification,
            "category": part.category.name if part.category else "未分类",
            "current_stock": part.current_stock,
            "stock_status": part.stock_status,
            "min_stock": part.min_stock,
            "max_stock": part.max_stock,
            "unit": part.unit,
            "unit_price": str(part.unit_price) if part.unit_price else "0",
            "brand": part.brand,
            "warranty_period": part.warranty_period
        })
    
    categories_data = [cat.name for cat in categories]
    
    # 如果数据库中没有数据，使用模拟数据
    if len(parts_data) == 0:
        print("⚠ 数据库中没有备件数据，使用模拟数据")
        categories_data = [
            "机械传动件", "液压气动件", "电气元件", "紧固件", 
            "润滑密封件", "过滤净化件", "传感器", "控制器",
            "电机", "阀门", "泵", "轴承", "齿轮", "皮带",
            "链条", "液压缸", "气缸", "接头", "密封件",
            "过滤器", "传感器", "开关", "继电器", "接触器",
            "断路器"
        ]
        
        parts_data = [
            {"part_code": "A001", "name": "齿轮减速机", "specification": "1:10", "category": "机械传动件", "current_stock": 5, "stock_status": "normal", "min_stock": 2, "max_stock": 10, "unit": "台", "unit_price": "1200", "brand": "西门子", "warranty_period": 24},
            {"part_code": "A002", "name": "皮带轮", "specification": "φ100mm", "category": "机械传动件", "current_stock": 15, "stock_status": "normal", "min_stock": 5, "max_stock": 20, "unit": "个", "unit_price": "80", "brand": "SKF", "warranty_period": 12},
            {"part_code": "B001", "name": "液压缸", "specification": "φ50×200", "category": "液压气动件", "current_stock": 8, "stock_status": "normal", "min_stock": 3, "max_stock": 15, "unit": "个", "unit_price": "650", "brand": "力士乐", "warranty_period": 18},
            {"part_code": "B002", "name": "气缸", "specification": "φ40×100", "category": "液压气动件", "current_stock": 20, "stock_status": "normal", "min_stock": 5, "max_stock": 30, "unit": "个", "unit_price": "280", "brand": "SMC", "warranty_period": 12},
            {"part_code": "C001", "name": "交流接触器", "specification": "CJX2-25", "category": "电气元件", "current_stock": 30, "stock_status": "normal", "min_stock": 10, "max_stock": 50, "unit": "个", "unit_price": "120", "brand": "施耐德", "warranty_period": 24},
            {"part_code": "C002", "name": "断路器", "specification": "DZ47-63 32A", "category": "电气元件", "current_stock": 25, "stock_status": "normal", "min_stock": 8, "max_stock": 40, "unit": "个", "unit_price": "85", "brand": "正泰", "warranty_period": 24},
            {"part_code": "D001", "name": "螺栓", "specification": "M10×50", "category": "紧固件", "current_stock": 100, "stock_status": "normal", "min_stock": 30, "max_stock": 200, "unit": "个", "unit_price": "2", "brand": "高强度", "warranty_period": 0},
            {"part_code": "D002", "name": "螺母", "specification": "M10", "category": "紧固件", "current_stock": 120, "stock_status": "normal", "min_stock": 50, "max_stock": 200, "unit": "个", "unit_price": "1", "brand": "高强度", "warranty_period": 0},
            {"part_code": "E001", "name": "黄油", "specification": "1kg", "category": "润滑密封件", "current_stock": 15, "stock_status": "normal", "min_stock": 5, "max_stock": 30, "unit": "桶", "unit_price": "60", "brand": "美孚", "warranty_period": 36},
            {"part_code": "E002", "name": "O型圈", "specification": "φ20", "category": "润滑密封件", "current_stock": 50, "stock_status": "normal", "min_stock": 20, "max_stock": 100, "unit": "个", "unit_price": "3", "brand": "氟橡胶", "warranty_period": 12}
        ]
    
    return {
        "total_parts": len(parts_data),
        "total_categories": len(categories_data),
        "categories": categories_data,
        "parts": parts_data
    }

# 分析备件数据并生成仓库设计
def analyze_parts_and_generate_warehouse():
    """分析备件数据并生成仓库设计"""
    print("="*80)
    print("调用文心一言API分析备件数据并生成仓库设计")
    print("="*80)
    
    # 检查 API 密钥
    if not API_KEY or not SECRET_KEY:
        print("\n✗ 错误：请先配置 BAIDU_API_KEY 和 BAIDU_SECRET_KEY")
        print("\n获取方式：")
        print("1. 访问 https://console.bce.baidu.com/")
        print("2. 创建文心一言应用")
        print("3. 获取 API Key 和 Secret Key")
        print("4. 添加到 .env 文件：")
        print("   BAIDU_API_KEY=your_api_key")
        print("   BAIDU_SECRET_KEY=your_secret_key")
        return
    
    # 获取备件数据
    print("\n正在获取备件数据...")
    parts_data = get_spare_parts_data()
    print(f"✓ 成功获取 {parts_data['total_parts']} 个备件，{parts_data['total_categories']} 个分类")
    
    # 准备分析请求
    analysis_prompt = f"""
    作为仓库管理系统专家，请分析以下备件数据并提供详细的仓库设计方案：
    
    备件数据概览：
    - 总备件数：{parts_data['total_parts']}
    - 总分类数：{parts_data['total_categories']}
    - 分类列表：{', '.join(parts_data['categories'])}
    
    详细备件数据：
    {json.dumps(parts_data['parts'][:10], ensure_ascii=False, indent=2)}...
    
    请提供以下分析：
    1. 设计分析：基于备件数据的仓库布局和存储策略建议
    2. 功能分析：仓库管理系统需要具备的核心功能
    3. 适配度分析：当前仓库管理模块与备件数据的适配程度
    4. 初始化仓库数据：创建10个初始化仓库，包括仓库名称、编码、类型、地址等信息
    5. 仓库与备件的关联方案：如何将备件数据与仓库数据相结合
    
    请提供详细的分析报告，输出格式为JSON，包含以下字段：
    {{"design_analysis": "", "function_analysis": "", "adaptation_analysis": "", "warehouses": [{{"name": "", "code": "", "type": "", "address": "", "area": 0, "capacity": 0, "description": ""}}], "integration_scheme": ""}}
    """
    
    print("\n正在调用文心一言API进行分析...")
    messages = [
        {
            "role": "system",
            "content": "你是一位专业的仓库管理系统专家，擅长分析备件数据并设计仓库管理方案。"
        },
        {
            "role": "user",
            "content": analysis_prompt
        }
    ]
    
    response = call_wenxin_api(messages, max_tokens=3000)
    
    if not response:
        print("\n⚠ API调用失败，使用模拟数据")
        # 使用预设的仓库数据
        result = {
            "design_analysis": "基于备件数据，建议采用分区存储策略，将不同类别备件分开存放。机械传动件和液压气动件应存放在重型货架区，电气元件和紧固件应存放在标准货架区，润滑密封件和过滤净化件应存放在恒温恒湿区。",
            "function_analysis": "仓库管理系统需要具备仓库基础信息管理、货位管理、库存管理、出入库管理、库存调拨、库存盘点、库存预警、报表分析等核心功能。",
            "adaptation_analysis": "当前仓库管理模块与备件数据的适配度较高，支持多仓库管理、货位管理和库存跟踪，能够满足备件管理的基本需求。",
            "warehouses": [
                {"name": "主仓库", "code": "WH001", "type": "general", "address": "北京市朝阳区建国路88号", "area": 5000, "capacity": 10000, "description": "主要存储各类备件的中央仓库"},
                {"name": "机械备件库", "code": "WH002", "type": "mechanical", "address": "北京市朝阳区建国路89号", "area": 3000, "capacity": 6000, "description": "专门存储机械传动件的仓库"},
                {"name": "电气备件库", "code": "WH003", "type": "electrical", "address": "北京市朝阳区建国路90号", "area": 2000, "capacity": 4000, "description": "专门存储电气元件的仓库"},
                {"name": "液压气动库", "code": "WH004", "type": "hydraulic", "address": "北京市朝阳区建国路91号", "area": 2500, "capacity": 5000, "description": "专门存储液压气动件的仓库"},
                {"name": "紧固件库", "code": "WH005", "type": "fastener", "address": "北京市朝阳区建国路92号", "area": 1500, "capacity": 3000, "description": "专门存储紧固件的仓库"},
                {"name": "润滑密封库", "code": "WH006", "type": "lubrication", "address": "北京市朝阳区建国路93号", "area": 1000, "capacity": 2000, "description": "专门存储润滑密封件的仓库"},
                {"name": "过滤净化库", "code": "WH007", "type": "filtration", "address": "北京市朝阳区建国路94号", "area": 1200, "capacity": 2400, "description": "专门存储过滤净化件的仓库"},
                {"name": "传感器库", "code": "WH008", "type": "sensor", "address": "北京市朝阳区建国路95号", "area": 800, "capacity": 1600, "description": "专门存储传感器的仓库"},
                {"name": "控制器库", "code": "WH009", "type": "controller", "address": "北京市朝阳区建国路96号", "area": 900, "capacity": 1800, "description": "专门存储控制器的仓库"},
                {"name": "应急备件库", "code": "WH010", "type": "emergency", "address": "北京市朝阳区建国路97号", "area": 600, "capacity": 1200, "description": "存储应急备件的仓库"}
            ],
            "integration_scheme": "将备件数据与仓库数据相结合的方案：1. 在备件表中添加仓库ID和货位ID字段，关联到仓库和货位表；2. 建立批次管理，记录每个备件的入库批次、仓库和货位信息；3. 通过库存调拨功能，实现备件在不同仓库之间的转移；4. 利用库存预警功能，监控各仓库的备件库存状态；5. 通过报表分析，了解各仓库的库存分布和使用情况。"
        }
    else:
        print("\n✓ 分析完成，正在处理结果...")
        
        # 解析JSON响应
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            print("\n✗ 解析响应失败，API返回格式错误")
            print(f"响应内容：{response}")
            # 使用预设的仓库数据
            result = {
                "design_analysis": "基于备件数据，建议采用分区存储策略，将不同类别备件分开存放。机械传动件和液压气动件应存放在重型货架区，电气元件和紧固件应存放在标准货架区，润滑密封件和过滤净化件应存放在恒温恒湿区。",
                "function_analysis": "仓库管理系统需要具备仓库基础信息管理、货位管理、库存管理、出入库管理、库存调拨、库存盘点、库存预警、报表分析等核心功能。",
                "adaptation_analysis": "当前仓库管理模块与备件数据的适配度较高，支持多仓库管理、货位管理和库存跟踪，能够满足备件管理的基本需求。",
                "warehouses": [
                    {"name": "主仓库", "code": "WH001", "type": "general", "address": "北京市朝阳区建国路88号", "area": 5000, "capacity": 10000, "description": "主要存储各类备件的中央仓库"},
                    {"name": "机械备件库", "code": "WH002", "type": "mechanical", "address": "北京市朝阳区建国路89号", "area": 3000, "capacity": 6000, "description": "专门存储机械传动件的仓库"},
                    {"name": "电气备件库", "code": "WH003", "type": "electrical", "address": "北京市朝阳区建国路90号", "area": 2000, "capacity": 4000, "description": "专门存储电气元件的仓库"},
                    {"name": "液压气动库", "code": "WH004", "type": "hydraulic", "address": "北京市朝阳区建国路91号", "area": 2500, "capacity": 5000, "description": "专门存储液压气动件的仓库"},
                    {"name": "紧固件库", "code": "WH005", "type": "fastener", "address": "北京市朝阳区建国路92号", "area": 1500, "capacity": 3000, "description": "专门存储紧固件的仓库"},
                    {"name": "润滑密封库", "code": "WH006", "type": "lubrication", "address": "北京市朝阳区建国路93号", "area": 1000, "capacity": 2000, "description": "专门存储润滑密封件的仓库"},
                    {"name": "过滤净化库", "code": "WH007", "type": "filtration", "address": "北京市朝阳区建国路94号", "area": 1200, "capacity": 2400, "description": "专门存储过滤净化件的仓库"},
                    {"name": "传感器库", "code": "WH008", "type": "sensor", "address": "北京市朝阳区建国路95号", "area": 800, "capacity": 1600, "description": "专门存储传感器的仓库"},
                    {"name": "控制器库", "code": "WH009", "type": "controller", "address": "北京市朝阳区建国路96号", "area": 900, "capacity": 1800, "description": "专门存储控制器的仓库"},
                    {"name": "应急备件库", "code": "WH010", "type": "emergency", "address": "北京市朝阳区建国路97号", "area": 600, "capacity": 1200, "description": "存储应急备件的仓库"}
                ],
                "integration_scheme": "将备件数据与仓库数据相结合的方案：1. 在备件表中添加仓库ID和货位ID字段，关联到仓库和货位表；2. 建立批次管理，记录每个备件的入库批次、仓库和货位信息；3. 通过库存调拨功能，实现备件在不同仓库之间的转移；4. 利用库存预警功能，监控各仓库的备件库存状态；5. 通过报表分析，了解各仓库的库存分布和使用情况。"
            }

    
    # 保存分析报告
    report_file = f"reports/warehouse_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('reports', exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 分析报告已保存到：{report_file}")
    
    # 显示分析结果
    print("\n" + "="*80)
    print("分析结果摘要")
    print("="*80)
    print(f"设计分析：{result.get('design_analysis', '')[:100]}...")
    print(f"功能分析：{result.get('function_analysis', '')[:100]}...")
    print(f"适配度分析：{result.get('adaptation_analysis', '')[:100]}...")
    print(f"生成的仓库数量：{len(result.get('warehouses', []))}")
    
    # 生成仓库数据
    print("\n" + "="*80)
    print("正在生成仓库数据...")
    print("="*80)
    
    warehouses = result.get('warehouses', [])
    created_count = 0
    
    for warehouse_data in warehouses:
        # 检查仓库编码是否已存在
        existing = Warehouse.query.filter_by(code=warehouse_data['code']).first()
        if existing:
            print(f"⚠ 仓库编码 {warehouse_data['code']} 已存在，跳过")
            continue
        
        # 创建仓库
        warehouse = Warehouse(
            name=warehouse_data['name'],
            code=warehouse_data['code'],
            type=warehouse_data['type'],
            address=warehouse_data['address'],
            area=warehouse_data['area'],
            capacity=warehouse_data['capacity'],
            description=warehouse_data['description'],
            is_active=True
        )
        
        db.session.add(warehouse)
        created_count += 1
        print(f"✓ 创建仓库：{warehouse_data['name']} ({warehouse_data['code']})")
    
    if created_count > 0:
        db.session.commit()
        print(f"\n✓ 成功创建 {created_count} 个仓库")
    else:
        print("\n⚠ 没有创建新仓库")
    
    # 显示集成方案
    print("\n" + "="*80)
    print("仓库与备件集成方案")
    print("="*80)
    print(result.get('integration_scheme', ''))
    
    print("\n" + "="*80)
    print("任务完成！")
    print("="*80)

if __name__ == "__main__":
    # 初始化数据库连接
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import create_app
    app = create_app()
    with app.app_context():
        analyze_parts_and_generate_warehouse()
