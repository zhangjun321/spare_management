"""
AI 货位推荐服务
集成百度千帆 AI，实现智能仓库和货位推荐
"""

import json
import re
from app.models.warehouse import Warehouse
from app.models.warehouse_advanced import WarehouseZone, WarehouseRack
from app.models.warehouse_location import WarehouseLocation
from app.services.baidu_qianfan_service import get_qianfan_service
from flask import current_app


class AILocationService:
    """AI 货位推荐服务"""
    
    def __init__(self):
        self.qianfan_service = get_qianfan_service()
    
    def recommend_warehouse_and_location(self, spare_part_data):
        """
        AI 智能推荐仓库和货位
        
        Args:
            spare_part_data: 备件信息字典
                {
                    'name': '轴承 6204',
                    'specification': '6204-2RS',
                    'category': '轴承',
                    'dimensions': {'length': 52, 'width': 52, 'height': 15},
                    'weight': 0.15,
                    'storage_requirements': ['防潮', '防尘'],
                    'inbound_frequency': 'high',
                    'value': 'medium'
                }
        
        Returns:
            dict: 推荐结果
        """
        try:
            # 1. 获取所有可用仓库
            warehouses = Warehouse.query.filter_by(is_active=True).all()
            warehouse_info = []
            
            for wh in warehouses:
                wh_data = {
                    'id': wh.id,
                    'name': wh.name,
                    'code': wh.code,
                    'type': wh.type,
                    'capacity': wh.capacity,
                    'total_inventory': wh.total_inventory,
                    'utilization_rate': float(wh.utilization_rate) if wh.utilization_rate else 0,
                    'specialties': self._get_warehouse_specialties(wh)
                }
                warehouse_info.append(wh_data)
            
            # 2. 获取每个仓库的可用货位
            locations_info = []
            for wh in warehouses:
                available_locations = WarehouseLocation.query.filter_by(
                    warehouse_id=wh.id,
                    status='available',
                    is_active=True
                ).limit(20).all()
                
                for loc in available_locations:
                    locations_info.append({
                        'id': loc.id,
                        'warehouse_id': wh.id,
                        'location_code': loc.location_code,
                        'level': loc.level,
                        'column': loc.column,
                        'max_weight': float(loc.max_weight) if loc.max_weight else None,
                        'max_volume': float(loc.max_volume) if loc.max_volume else None,
                        'priority': loc.priority,
                        'distance_to_exit': self._calculate_distance_to_exit(loc)
                    })
            
            # 3. 构建 AI 提示词
            prompt = self._build_recommendation_prompt(
                spare_part=spare_part_data,
                warehouses=warehouse_info,
                locations=locations_info
            )
            
            # 4. 调用百度千帆 AI
            current_app.logger.info(f"调用百度千帆 AI 进行货位推荐，仓库数：{len(warehouses)}, 货位数：{len(locations_info)}")
            
            result = self.qianfan_service.chat(
                messages=[{'role': 'user', 'content': prompt}],
                system_prompt="你是智能仓库货位分配专家，擅长根据备件特性和仓库情况推荐最佳存储位置。请返回 JSON 格式结果。"
            )
            
            # 5. 解析 AI 返回结果
            if result['success']:
                recommendation = self._parse_ai_result(result['content'])
                current_app.logger.info(f"AI 推荐成功：仓库 ID={recommendation.get('recommended_warehouse_id')}, 货位 ID={recommendation.get('recommended_location_id')}")
                return recommendation
            else:
                current_app.logger.error(f"AI 推荐失败：{result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'AI 服务调用失败')
                }
                
        except Exception as e:
            current_app.logger.error(f"AI 推荐异常：{str(e)}")
            return {
                'success': False,
                'error': f'AI 推荐异常：{str(e)}'
            }
    
    def _get_warehouse_specialties(self, warehouse):
        """获取仓库专长（存储的备件类型）"""
        from app.models.spare_part import SparePart
        from app.models.category import Category
        from app.extensions import db
        
        try:
            categories = db.session.query(
                Category.name,
                db.func.count(SparePart.id).label('count')
            ).join(
                SparePart, SparePart.category_id == Category.id
            ).filter(
                SparePart.warehouse_id == warehouse.id
            ).group_by(
                Category.name
            ).order_by(
                db.func.count(SparePart.id).desc()
            ).limit(3).all()
            
            return [cat.name for cat, count in categories]
        except Exception as e:
            current_app.logger.error(f"获取仓库专长失败：{str(e)}")
            return []
    
    def _calculate_distance_to_exit(self, location):
        """计算货位到出口的距离（简化版）"""
        # 层级越低、列数越小，距离出口越近
        level = location.level or 0
        column = location.column or 0
        return level * 10 + column * 5
    
    def _build_recommendation_prompt(self, spare_part, warehouses, locations):
        """构建 AI 推荐提示词"""
        prompt = f"""请根据备件信息和仓库情况，推荐最佳仓库和货位。

【备件信息】
名称：{spare_part.get('name', '未知')}
规格：{spare_part.get('specification', '未知')}
分类：{spare_part.get('category', '未知')}
尺寸：{spare_part.get('dimensions', {})}
重量：{spare_part.get('weight', 0)} kg
存储要求：{spare_part.get('storage_requirements', [])}
出入库频率：{spare_part.get('inbound_frequency', 'medium')}
价值等级：{spare_part.get('value', 'medium')}

【可用仓库】（{len(warehouses)}个）
{json.dumps(warehouses, ensure_ascii=False, indent=2)}

【可用货位】（{len(locations)}个）
{json.dumps(locations, ensure_ascii=False, indent=2)}

【推荐要求】
请综合考虑以下因素：
1. 仓库类型匹配（危险品、冷库等特殊要求）
2. 仓库专长（该仓库常存储的备件类型）
3. 货位尺寸和承重（满足备件存储要求）
4. 出入库频率（高频备件靠近出口）
5. 价值等级（高价值备件放在安全位置）
6. 仓库利用率（避免过度拥挤的仓库）
7. 存储要求（防潮、防尘等）

请以 JSON 格式返回推荐结果：
{{
    "recommended_warehouse_id": 仓库 ID,
    "recommended_warehouse_name": "仓库名称",
    "recommended_location_id": 货位 ID,
    "recommended_location_code": "货位编码",
    "confidence": 92,
    "reason": "推荐理由（详细说明）",
    "alternative_warehouses": [备选仓库 ID 列表],
    "notes": "注意事项"
}}
"""
        return prompt
    
    def _parse_ai_result(self, ai_response):
        """解析 AI 返回结果"""
        try:
            # 提取 JSON 部分
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'success': True,
                    'recommended_warehouse_id': result.get('recommended_warehouse_id'),
                    'recommended_warehouse_name': result.get('recommended_warehouse_name', ''),
                    'recommended_location_id': result.get('recommended_location_id'),
                    'recommended_location_code': result.get('recommended_location_code', ''),
                    'confidence': result.get('confidence', 0),
                    'reason': result.get('reason', ''),
                    'alternative_warehouses': result.get('alternative_warehouses', []),
                    'notes': result.get('notes', '')
                }
        except Exception as e:
            current_app.logger.error(f"解析 AI 结果失败：{str(e)}")
        
        return {
            'success': False,
            'error': 'AI 结果解析失败'
        }
