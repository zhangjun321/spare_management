"""
AI 分析服务 V3
基于百度千帆 AI 的智能分析服务
"""

import json
from typing import Dict, List, Optional
from app.services.baidu_image_service import baidu_image_service


class AIAnalysisV3Service:
    """AI 分析服务 V3"""
    
    @staticmethod
    def analyze_parts_data(parts_data: List[Dict]) -> Dict:
        """
        分析备件数据结构
        
        Args:
            parts_data: 备件数据列表
        
        Returns:
            分析结果
        """
        if not baidu_image_service.client:
            return {'error': 'AI 客户端未初始化'}
        
        try:
            # 构建分析提示词
            prompt = AIAnalysisV3Service._build_parts_analysis_prompt(parts_data)
            
            # 调用百度千帆 AI
            response = baidu_image_service.client.generate(
                model="ERNIE-Bot-4",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # 解析结果
            result = json.loads(response['result'])
            
            return {
                'success': True,
                'analysis': result,
                'recommendations': AIAnalysisV3Service._generate_recommendations(result)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _build_parts_analysis_prompt(parts_data: List[Dict]) -> str:
        """构建备件分析提示词"""
        return f"""
请分析以下备件数据结构，并提供详细的分析报告：

备件数量：{len(parts_data)}

分析维度：
1. 备件类型分布（按功能分类）
2. 价值分布分析（高价值、中价值、低价值）
3. 周转率分析（快速、中速、慢速）
4. 存储条件需求（常温、冷藏、特殊）
5. ABC 分类建议
6. 仓库类型推荐
7. 货位分配策略建议

备件数据示例：
{json.dumps(parts_data[:10], ensure_ascii=False, indent=2)}

请以 JSON 格式返回分析结果，包含以下字段：
{{
    "type_distribution": {{}},
    "value_distribution": {{}},
    "turnover_analysis": {{}},
    "storage_requirements": {{}},
    "abc_classification": {{}},
    "warehouse_recommendations": [],
    "location_strategy": []
}}
"""
    
    @staticmethod
    def _generate_recommendations(analysis_result: Dict) -> List[Dict]:
        """基于分析结果生成建议"""
        recommendations = []
        
        # 仓库类型建议
        if 'warehouse_recommendations' in analysis_result:
            for rec in analysis_result['warehouse_recommendations']:
                recommendations.append({
                    'type': 'warehouse',
                    'priority': 'high',
                    'content': rec
                })
        
        # 货位策略建议
        if 'location_strategy' in analysis_result:
            for strategy in analysis_result['location_strategy']:
                recommendations.append({
                    'type': 'location',
                    'priority': 'medium',
                    'content': strategy
                })
        
        return recommendations
    
    @staticmethod
    def recommend_location(part_data: Dict, warehouse_id: int, quantity: float) -> Dict:
        """
        智能货位推荐
        
        Args:
            part_data: 备件数据
            warehouse_id: 仓库 ID
            quantity: 数量
        
        Returns:
            推荐结果
        """
        if not baidu_image_service.client:
            return {'error': 'AI 客户端未初始化'}
        
        try:
            # 构建推荐提示词
            prompt = f"""
请为以下备件推荐最优货位：

备件信息：
- 名称：{part_data.get('name', 'Unknown')}
- 类型：{part_data.get('type', 'Unknown')}
- 尺寸：{part_data.get('dimensions', 'Unknown')}
- 重量：{part_data.get('weight', 'Unknown')}kg
- 存储条件：{part_data.get('storage_requirements', '常温')}
- 周转率：{part_data.get('turnover_rate', '中等')}

仓库 ID: {warehouse_id}
入库数量：{quantity}

请考虑以下因素进行推荐：
1. 货位尺寸匹配
2. 货位承重能力
3. 存储条件匹配
4. 周转率优化（高频备件靠近出口）
5. 同类备件集中存储
6. 拣货路径优化

返回 JSON 格式：
{{
    "recommended_locations": [
        {{"location_id": 1, "score": 95, "reason": "尺寸匹配，位置优越"}},
        {{"location_id": 2, "score": 88, "reason": "承重足够，邻近同类"}}
    ],
    "optimal_strategy": "建议存放在 A 区高频货位"
}}
"""
            
            # 调用 AI
            response = baidu_image_service.client.generate(
                model="ERNIE-Bot-4",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response['result'])
            
            return {
                'success': True,
                'recommendations': result.get('recommended_locations', []),
                'strategy': result.get('optimal_strategy', '')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def optimize_picking_path(picking_list: List[Dict]) -> Dict:
        """
        优化拣货路径
        
        Args:
            picking_list: 拣货清单
        
        Returns:
            优化后的路径
        """
        if not baidu_image_service.client:
            return {'error': 'AI 客户端未初始化'}
        
        try:
            # 构建优化提示词
            prompt = f"""
请优化以下拣货路径：

拣货清单（共{len(picking_list)}项）：
{json.dumps(picking_list[:20], ensure_ascii=False, indent=2)}

请考虑：
1. 最短路径原则
2. 避免重复路线
3. 先重后轻原则
4. 先大后小原则
5. 同区域集中拣选

返回 JSON 格式：
{{
    "optimized_sequence": [1, 3, 2, 4],  // 优化后的拣货顺序
    "estimated_distance": "150 米",
    "estimated_time": "5 分钟",
    "path_description": "A 区→B 区→C 区→出口"
}}
"""
            
            response = baidu_image_service.client.generate(
                model="ERNIE-Bot-4",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response['result'])
            
            return {
                'success': True,
                'optimized_sequence': result.get('optimized_sequence', []),
                'estimated_distance': result.get('estimated_distance', ''),
                'estimated_time': result.get('estimated_time', ''),
                'path_description': result.get('path_description', '')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def predict_demand(historical_data: List[Dict], days: int = 30) -> Dict:
        """
        需求预测
        
        Args:
            historical_data: 历史数据
            days: 预测天数
        
        Returns:
            预测结果
        """
        if not baidu_image_service.client:
            return {'error': 'AI 客户端未初始化'}
        
        try:
            prompt = f"""
请基于历史数据预测未来{days}天的需求：

历史数据（最近 3 个月）：
{json.dumps(historical_data[:30], ensure_ascii=False, indent=2)}

请分析：
1. 需求趋势（上升/下降/平稳）
2. 季节性因素
3. 预测准确率
4. 安全库存建议

返回 JSON 格式：
{{
    "trend": "上升",
    "predicted_demand": 1500,
    "confidence": 0.85,
    "safety_stock": 300,
    "reorder_point": 500,
    "analysis": "详细分析说明"
}}
"""
            
            response = baidu_image_service.client.generate(
                model="ERNIE-Bot-4",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response['result'])
            
            return {
                'success': True,
                'trend': result.get('trend', ''),
                'predicted_demand': result.get('predicted_demand', 0),
                'confidence': result.get('confidence', 0),
                'safety_stock': result.get('safety_stock', 0),
                'reorder_point': result.get('reorder_point', 0),
                'analysis': result.get('analysis', '')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
