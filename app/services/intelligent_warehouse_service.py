
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能仓库管理服务 - 使用百度千帆 API
提供智能库位推荐、仓库优化、可视化分析等功能
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from app.extensions import db
from app.models import Warehouse, SparePart, WarehouseZone, WarehouseRack, WarehouseLocation
from flask import current_app
import logging

logger = logging.getLogger(__name__)

load_dotenv()


class IntelligentWarehouseService:
    """智能仓库服务 - 基于百度千帆 AI"""
    
    def __init__(self):
        self.api_key = os.getenv("BAIDU_API_KEY", "")
        self.secret_key = os.getenv("BAIDU_SECRET_KEY", "")
        self.access_token = None
    
    def get_access_token(self):
        """获取百度千帆 API 的 access token"""
        if self.access_token:
            return self.access_token
            
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            response = requests.post(url, params=params)
            result = response.json()
            self.access_token = result.get("access_token")
            return self.access_token
        except Exception as e:
            logger.error(f"获取 access token 失败：{str(e)}")
            return None
    
    def call_wenxin_api(self, messages, max_tokens=3000):
        """调用文心一言 API"""
        access_token = self.get_access_token()
        if not access_token:
            return None
        
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "max_output_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                return result.get('result', '')
            else:
                logger.error(f"API 调用失败：{response.text}")
                return None
        except Exception as e:
            logger.error(f"API 调用异常：{str(e)}")
            return None
    
    def analyze_spare_parts_data(self, warehouse_id=None):
        """
        使用 AI 分析备件数据
        
        Args:
            warehouse_id: 仓库 ID
            
        Returns:
            dict: AI 分析结果
        """
        # 获取备件数据
        query = SparePart.query.filter_by(is_active=True)
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        spare_parts = query.all()
        
        if not spare_parts:
            return {
                'success': False,
                'error': '没有可用的备件数据'
            }
        
        # 构建备件数据
        parts_data = []
        total_value = 0
        for part in spare_parts:
            stock_value = (part.current_stock or 0) * float(part.unit_price or 0)
            total_value += stock_value
            parts_data.append({
                'name': part.name,
                'specification': part.specification,
                'category': part.category.name if part.category else '未分类',
                'current_stock': part.current_stock,
                'stock_status': part.stock_status,
                'unit_price': float(part.unit_price or 0),
                'stock_value': stock_value,
                'brand': part.brand,
                'min_stock': part.min_stock,
                'max_stock': part.max_stock
            })
        
        # 按价值排序
        parts_data.sort(key=lambda x: x['stock_value'], reverse=True)
        
        # 构建 AI 分析提示词
        prompt = f"""
你是一个智能仓库管理专家。请分析以下备件数据，并提供专业的仓库管理建议。

备件数据（共{len(parts_data)}个备件，总价值{total_value:.2f}元）：
{json.dumps(parts_data[:20], ensure_ascii=False, indent=2)}

请从以下维度进行分析：
1. ABC 分类分析（按价值）
2. 库存周转分析
3. 库位需求预测
4. 存储环境要求
5. 拣货路径优化建议
6. 安全库存建议

请以 JSON 格式返回分析结果，包含以下字段：
{{
    "abc_analysis": {{
        "A_class": [备件列表],
        "B_class": [备件列表],
        "C_class": [备件列表],
        "summary": "分类说明"
    }},
    "turnover_analysis": {{
        "high_turnover": [高周转备件],
        "medium_turnover": [中周转备件],
        "low_turnover": [低周转备件]
    }},
    "location_recommendations": [库位建议],
    "storage_requirements": [存储要求],
    "picking_optimization": [拣货优化建议],
    "safety_stock_suggestions": [安全库存建议]
}}
"""
        
        messages = [
            {"role": "system", "content": "你是智能仓库管理专家，精通库存优化、库位规划和仓储管理。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.call_wenxin_api(messages, max_tokens=4000)
        
        if result:
            try:
                # 尝试解析 JSON
                analysis = json.loads(result)
                return {
                    'success': True,
                    'analysis': analysis,
                    'total_parts': len(parts_data),
                    'total_value': total_value
                }
            except:
                return {
                    'success': True,
                    'raw_analysis': result,
                    'total_parts': len(parts_data),
                    'total_value': total_value
                }
        else:
            return {
                'success': False,
                'error': 'AI 分析失败'
            }
    
    def generate_warehouse_layout(self, warehouse_id, analysis_result):
        """
        使用 AI 生成仓库布局方案
        
        Args:
            warehouse_id: 仓库 ID
            analysis_result: AI 分析结果
            
        Returns:
            dict: 仓库布局方案
        """
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return {'success': False, 'error': '仓库不存在'}
        
        # 构建布局生成提示词
        prompt = f"""
请为以下仓库设计一个智能化的布局方案：

仓库信息：
- 名称：{warehouse.name}
- 类型：{warehouse.type}
- 面积：{warehouse.area} 平方米
- 容量：{warehouse.capacity} 立方米
- 地址：{warehouse.address}

备件分析结果：
{json.dumps(analysis_result.get('analysis', {}), ensure_ascii=False, indent=2)}

请设计一个符合以下原则的仓库布局：
1. ABC 分类分区（A 类靠近出入口）
2. 重物下层、轻物上层
3. 相似物品集中存放
4. 考虑特殊存储要求（冷藏、危险品等）
5. 优化拣货路径
6. 预留扩展空间

请以 JSON 格式返回布局方案：
{{
    "zones": [
        {{
            "zone_code": "A-QUICK",
            "zone_name": "快拣区",
            "zone_type": "general",
            "description": "A 类高周转备件",
            "area_percentage": 30,
            "rack_count": 10,
            "location_count": 200
        }}
    ],
    "rack_configuration": {{
        "standard_rack": {{
            "levels": 5,
            "positions_per_level": 10,
            "capacity_per_position": 50
        }}
    }},
    "traffic_flow": "描述物流动线",
    "special_areas": [特殊区域说明]
}}
"""
        
        messages = [
            {"role": "system", "content": "你是智能仓库设计专家，精通仓库布局规划和物流优化。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.call_wenxin_api(messages, max_tokens=4000)
        
        if result:
            try:
                layout = json.loads(result)
                return {
                    'success': True,
                    'layout': layout,
                    'warehouse_name': warehouse.name
                }
            except:
                return {
                    'success': True,
                    'raw_layout': result,
                    'warehouse_name': warehouse.name
                }
        else:
            return {'success': False, 'error': '布局生成失败'}
    
    def optimize_inventory(self, warehouse_id):
        """
        使用 AI 优化库存
        
        Args:
            warehouse_id: 仓库 ID
            
        Returns:
            dict: 库存优化建议
        """
        # 获取仓库备件
        spare_parts = SparePart.query.filter_by(
            warehouse_id=warehouse_id,
            is_active=True
        ).all()
        
        if not spare_parts:
            return {'success': False, 'error': '没有备件数据'}
        
        # 构建库存数据
        inventory_data = []
        for part in spare_parts:
            inventory_data.append({
                'name': part.name,
                'current_stock': part.current_stock,
                'min_stock': part.min_stock,
                'max_stock': part.max_stock,
                'stock_status': part.stock_status,
                'unit_price': float(part.unit_price or 0),
                'stock_value': (part.current_stock or 0) * float(part.unit_price or 0)
            })
        
        prompt = f"""
请分析以下库存数据，并提供优化建议：

库存数据（共{len(inventory_data)}个备件）：
{json.dumps(inventory_data, ensure_ascii=False, indent=2)}

请分析并提供：
1. 呆滞库存识别（超过 6 个月未动）
2. 缺货风险预警
3. 超储库存识别
4. 库存周转率分析
5. 补货建议
6. 库存调整建议

请以 JSON 格式返回：
{{
    "slow_moving": [呆滞库存列表],
    "shortage_risk": [缺货风险列表],
    "overstocked": [超储库存列表],
    "turnover_analysis": "周转率分析",
    "replenishment_suggestions": [补货建议],
    "adjustment_suggestions": [调整建议]
}}
"""
        
        messages = [
            {"role": "system", "content": "你是库存优化专家，精通库存控制和供应链管理。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.call_wenxin_api(messages, max_tokens=4000)
        
        if result:
            try:
                optimization = json.loads(result)
                return {
                    'success': True,
                    'optimization': optimization,
                    'total_items': len(inventory_data)
                }
            except:
                return {
                    'success': True,
                    'raw_optimization': result,
                    'total_items': len(inventory_data)
                }
        else:
            return {'success': False, 'error': '优化分析失败'}
    
    def generate_visualization_report(self, warehouse_id):
        """
        生成可视化报表数据
        
        Args:
            warehouse_id: 仓库 ID
            
        Returns:
            dict: 可视化报表数据
        """
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return {'success': False, 'error': '仓库不存在'}
        
        # 统计仓库数据
        total_parts = SparePart.query.filter_by(
            warehouse_id=warehouse_id,
            is_active=True
        ).count()
        
        # 按状态统计
        stock_status_stats = db.session.query(
            SparePart.stock_status,
            db.func.count(SparePart.id)
        ).filter_by(
            warehouse_id=warehouse_id,
            is_active=True
        ).group_by(SparePart.stock_status).all()
        
        # 按分类统计
        category_stats = db.session.query(
            SparePart.category_id,
            db.func.count(SparePart.id)
        ).filter_by(
            warehouse_id=warehouse_id,
            is_active=True
        ).group_by(SparePart.category_id).all()
        
        # 库存价值统计
        total_value = db.session.query(
            db.func.sum(SparePart.current_stock * SparePart.unit_price)
        ).filter_by(
            warehouse_id=warehouse_id,
            is_active=True
        ).scalar() or 0
        
        # 库位使用统计
        location_stats = db.session.query(
            db.func.count(WarehouseLocation.id),
            db.func.sum(WarehouseLocation.current_capacity)
        ).filter_by(
            warehouse_id=warehouse_id
        ).first()
        
        visualization_data = {
            'warehouse_info': {
                'name': warehouse.name,
                'code': warehouse.code,
                'type': warehouse.type,
                'area': float(warehouse.area) if warehouse.area else 0,
                'capacity': warehouse.capacity
            },
            'inventory_summary': {
                'total_parts': total_parts,
                'total_value': float(total_value),
                'stock_status': {
                    status: count 
                    for status, count in stock_status_stats
                },
                'category_distribution': [
                    {'category_id': cat_id, 'count': count}
                    for cat_id, count in category_stats
                ]
            },
            'location_usage': {
                'total_locations': location_stats[0] if location_stats else 0,
                'used_capacity': location_stats[1] if location_stats else 0
            }
        }
        
        return {
            'success': True,
            'visualization': visualization_data
        }


# 全局服务实例
intelligent_warehouse_service = IntelligentWarehouseService()

