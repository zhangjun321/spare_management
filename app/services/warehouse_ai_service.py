
"""
仓库AI服务 - 智能仓库初始化、库位分配等
"""
import logging
from datetime import datetime
from app.extensions import db
from app.models import (
    Warehouse,
    WarehouseZone,
    WarehouseRack,
    WarehouseLocation,
    SparePart
)

logger = logging.getLogger(__name__)


class WarehouseAIService:
    """仓库AI服务类"""
    
    def __init__(self):
        pass
    
    def analyze_spare_parts(self, warehouse_id=None):
        """
        分析备件数据，为智能初始化做准备
        
        Args:
            warehouse_id: 仓库ID（可选，为None时分析所有备件）
            
        Returns:
            dict: 分析结果
        """
        logger.info("开始分析备件数据, warehouse_id=%s", warehouse_id)
        
        # 查询备件
        query = SparePart.query.filter_by(is_active=True)
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        spare_parts = query.all()
        total_parts = len(spare_parts)
        
        if total_parts == 0:
            logger.warning("没有找到可用的备件数据")
            return {
                'total_parts': 0,
                'abc_distribution': {'A': 0, 'B': 0, 'C': 0},
                'special_requirements': {
                    'cold_storage': 0,
                    'hazardous': 0,
                    'fragile': 0
                },
                'total_stock': 0,
                'total_value': 0,
                'recommendations': ['暂无备件数据，建议先添加备件']
            }
        
        # 统计数据
        abc_distribution = {'A': 0, 'B': 0, 'C': 0}
        special_requirements = {
            'cold_storage': 0,
            'hazardous': 0,
            'fragile': 0
        }
        total_stock = 0
        total_value = 0
        
        # 计算每个备件的价值
        parts_with_value = []
        for part in spare_parts:
            stock = part.current_stock or 0
            price = float(part.unit_price or 0)
            value = stock * price
            
            parts_with_value.append({
                'part': part,
                'value': value,
                'stock': stock
            })
            
            total_stock += stock
            total_value += value
        
        # 按价值排序进行ABC分类
        parts_with_value.sort(key=lambda x: x['value'], reverse=True)
        
        # 计算ABC分类
        cumulative_value = 0
        for idx, item in enumerate(parts_with_value):
            cumulative_value += item['value']
            if total_value &gt; 0:
                percentage = cumulative_value / total_value
            else:
                percentage = 0
            
            if percentage &lt;= 0.8:
                abc_class = 'A'
            elif percentage &lt;= 0.95:
                abc_class = 'B'
            else:
                abc_class = 'C'
            
            abc_distribution[abc_class] += 1
            
            # 分析特殊属性（简单模拟）
            part_name = item['part'].name.lower() if item['part'].name else ''
            if '冷' in part_name or '冰' in part_name or '冻' in part_name:
                special_requirements['cold_storage'] += 1
            if '危险' in part_name or '易燃' in part_name or '易爆' in part_name:
                special_requirements['hazardous'] += 1
            if '易碎' in part_name or '玻璃' in part_name or '陶瓷' in part_name:
                special_requirements['fragile'] += 1
        
        # 生成推荐
        recommendations = self._generate_recommendations(
            total_parts, abc_distribution, special_requirements, total_stock
        )
        
        result = {
            'total_parts': total_parts,
            'abc_distribution': abc_distribution,
            'special_requirements': special_requirements,
            'total_stock': total_stock,
            'total_value': round(total_value, 2),
            'recommendations': recommendations
        }
        
        logger.info("备件数据分析完成: %s", result)
        return result
    
    def _generate_recommendations(self, total_parts, abc_distribution, special_requirements, total_stock):
        """生成推荐建议"""
        recommendations = []
        
        # 库位数量估算
        locations_needed = max(total_parts * 2, 50)  # 每个备件至少2个库位，最少50个
        recommendations.append("建议创建约 " + str(locations_needed) + " 个货位")
        
        # ABC分类建议
        if abc_distribution['A'] &gt; 0:
            recommendations.append("A类备件 " + str(abc_distribution['A']) + " 个，建议设置快拣区")
        if abc_distribution['B'] &gt; 0:
            recommendations.append("B类备件 " + str(abc_distribution['B']) + " 个，建议设置普通区")
        if abc_distribution['C'] &gt; 0:
            recommendations.append("C类备件 " + str(abc_distribution['C']) + " 个，建议设置高架区")
        
        # 特殊需求建议
        if special_requirements.get('cold_storage', 0) &gt; 0:
            recommendations.append("检测到 " + str(special_requirements['cold_storage']) + " 个冷藏需求备件，建议设置冷藏区")
        if special_requirements.get('hazardous', 0) &gt; 0:
            recommendations.append("检测到 " + str(special_requirements['hazardous']) + " 个危险品，建议设置危险品区")
        if special_requirements.get('fragile', 0) &gt; 0:
            recommendations.append("检测到 " + str(special_requirements['fragile']) + " 个易碎品，建议设置特殊存放区")
        
        return recommendations
    
    def generate_zone_plan(self, analysis_result, warehouse_id):
        """
        根据分析结果生成库区规划
        
        Args:
            analysis_result: 备件分析结果
            warehouse_id: 仓库ID
            
        Returns:
            dict: 库区规划
        """
        logger.info("生成库区规划, warehouse_id=%s", warehouse_id)
        
        zones = []
        total_racks = 0
        total_locations = 0
        
        abc_dist = analysis_result.get('abc_distribution', {'A': 0, 'B': 0, 'C': 0})
        special_req = analysis_result.get('special_requirements', {})
        
        # A类快拣区
        if abc_dist.get('A', 0) &gt; 0:
            rack_count = max(abc_dist['A'] // 5 + 1, 2)
            locations_per_rack = 10
            zones.append({
                'zone_code': 'A-QUICK',
                'zone_name': '快拣区',
                'zone_type': 'general',
                'description': 'A类高周转备件，靠近出入口',
                'rack_count': rack_count,
                'locations_per_rack': locations_per_rack,
                'abc_type': 'A'
            })
            total_racks += rack_count
            total_locations += rack_count * locations_per_rack
        
        # B类普通区
        if abc_dist.get('B', 0) &gt; 0:
            rack_count = max(abc_dist['B'] // 8 + 1, 2)
            locations_per_rack = 15
            zones.append({
                'zone_code': 'B-NORMAL',
                'zone_name': '普通区',
                'zone_type': 'general',
                'description': 'B类中周转备件',
                'rack_count': rack_count,
                'locations_per_rack': locations_per_rack,
                'abc_type': 'B'
            })
            total_racks += rack_count
            total_locations += rack_count * locations_per_rack
        
        # C类高架区
        if abc_dist.get('C', 0) &gt; 0:
            rack_count = max(abc_dist['C'] // 10 + 1, 2)
            locations_per_rack = 20
            zones.append({
                'zone_code': 'C-HIGH',
                'zone_name': '高架区',
                'zone_type': 'elevated',
                'description': 'C类低周转备件',
                'rack_count': rack_count,
                'locations_per_rack': locations_per_rack,
                'abc_type': 'C'
            })
            total_racks += rack_count
            total_locations += rack_count * locations_per_rack
        
        # 冷藏区
        if special_req.get('cold_storage', 0) &gt; 0:
            zones.append({
                'zone_code': 'D-COLD',
                'zone_name': '冷藏区',
                'zone_type': 'cold',
                'temperature_min': 2,
                'temperature_max': 8,
                'description': '需冷藏保存的备件',
                'rack_count': 2,
                'locations_per_rack': 10,
                'is_special': True
            })
            total_racks += 2
            total_locations += 20
        
        # 危险品区
        if special_req.get('hazardous', 0) &gt; 0:
            zones.append({
                'zone_code': 'E-HAZARD',
                'zone_name': '危险品区',
                'zone_type': 'hazardous',
                'description': '危险品专用库区',
                'rack_count': 2,
                'locations_per_rack': 10,
                'is_special': True
            })
            total_racks += 2
            total_locations += 20
        
        # 如果没有任何区，创建默认区
        if not zones:
            zones.append({
                'zone_code': 'MAIN',
                'zone_name': '主库区',
                'zone_type': 'general',
                'description': '主要存储区域',
                'rack_count': 5,
                'locations_per_rack': 20
            })
            total_racks = 5
            total_locations = 100
        
        plan = {
            'zones': zones,
            'total_racks': total_racks,
            'total_locations': total_locations
        }
        
        logger.info("库区规划生成完成: %s", plan)
        return plan
    
    def create_zones(self, warehouse_id, zone_plan, user_id=None):
        """批量创建库区"""
        logger.info("开始创建库区, warehouse_id=%s", warehouse_id)
        
        created_zones = []
        
        for idx, zone_data in enumerate(zone_plan['zones']):
            zone = WarehouseZone(
                warehouse_id=warehouse_id,
                zone_code=zone_data['zone_code'],
                zone_name=zone_data['zone_name'],
                zone_type=zone_data['zone_type'],
                description=zone_data.get('description'),
                temperature_min=zone_data.get('temperature_min'),
                temperature_max=zone_data.get('temperature_max'),
                sort_order=idx,
                is_active=True
            )
            db.session.add(zone)
            created_zones.append(zone)
        
        db.session.flush()  # 获取ID但不提交
        logger.info("库区创建完成: %s 个", len(created_zones))
        
        return created_zones
    
    def create_racks(self, zones, zone_plan):
        """批量创建货架"""
        logger.info("开始创建货架")
        
        created_racks = []
        
        for zone_idx, zone in enumerate(zones):
            zone_data = zone_plan['zones'][zone_idx]
            rack_count = zone_data['rack_count']
            
            for rack_idx in range(rack_count):
                rack_code = zone.zone_code + "-R" + str(rack_idx + 1).zfill(2)
                rack = WarehouseRack(
                    zone_id=zone.id,
                    rack_code=rack_code,
                    rack_name=zone.zone_name + " 货架" + str(rack_idx + 1),
                    rack_type='standard',
                    levels_count=5,
                    sort_order=rack_idx,
                    is_active=True
                )
                db.session.add(rack)
                created_racks.append(rack)
        
        db.session.flush()
        logger.info("货架创建完成: %s 个", len(created_racks))
        
        return created_racks
    
    def create_locations(self, racks, zone_plan):
        """批量创建货位"""
        logger.info("开始创建货位")
        
        created_locations = []
        rack_zone_map = {}
        
        # 建立货架到库区数据的映射
        zone_data_list = zone_plan['zones']
        rack_idx = 0
        
        for zone_data in zone_data_list:
            for _ in range(zone_data['rack_count']):
                if rack_idx &lt; len(racks):
                    rack_zone_map[racks[rack_idx]] = zone_data
                    rack_idx += 1
        
        for rack in racks:
            zone_data = rack_zone_map.get(rack, {'locations_per_rack': 10})
            locations_per_rack = zone_data.get('locations_per_rack', 10)
            
            # 每层创建多个货位
            for level in range(1, 6):  # 5层
                for pos in range(1, (locations_per_rack // 5) + 2):
                    location_code = rack.rack_code + "-L" + str(level) + "-" + str(pos).zfill(2)
                    location = WarehouseLocation(
                        warehouse_id=rack.zone.warehouse_id,
                        location_code=location_code,
                        location_name=rack.rack_name + " " + str(level) + "层 " + str(pos) + "位",
                        location_type='general',
                        max_capacity=50,
                        current_capacity=0,
                        status='available'
                    )
                    db.session.add(location)
                    created_locations.append(location)
        
        db.session.flush()
        logger.info("货位创建完成: %s 个", len(created_locations))
        
        return created_locations
    
    def auto_assign_locations(self, warehouse_id, locations, analysis_result):
        """
        自动分配备件库位
        
        Args:
            warehouse_id: 仓库ID
            locations: 货位列表
            analysis_result: 备件分析结果
            
        Returns:
            dict: 分配结果
        """
        logger.info("开始自动分配备件库位, warehouse_id=%s", warehouse_id)
        
        # 查询备件
        spare_parts = SparePart.query.filter_by(is_active=True).all()
        
        # 按ABC分类分组
        abc_locations = {'A': [], 'B': [], 'C': []}
        for loc in locations:
            if '-QUICK' in loc.location_code or 'A-' in loc.location_code:
                abc_locations['A'].append(loc)
            elif '-NORMAL' in loc.location_code or 'B-' in loc.location_code:
                abc_locations['B'].append(loc)
            else:
                abc_locations['C'].append(loc)
        
        # 确保每个分类都有货位
        if not abc_locations['A']:
            abc_locations['A'] = locations[:len(locations)//3]
        if not abc_locations['B']:
            abc_locations['B'] = locations[len(locations)//3 : 2*len(locations)//3]
        if not abc_locations['C']:
            abc_locations['C'] = locations[2*len(locations)//3:]
        
        # 计算备件价值并排序
        parts_with_value = []
        for part in spare_parts:
            stock = part.current_stock or 0
            price = float(part.unit_price or 0)
            value = stock * price
            parts_with_value.append({
                'part': part,
                'value': value
            })
        
        parts_with_value.sort(key=lambda x: x['value'], reverse=True)
        
        # ABC分类并分配
        total_value = sum(x['value'] for x in parts_with_value)
        cumulative_value = 0
        assigned_count = 0
        location_pointers = {'A': 0, 'B': 0, 'C': 0}
        
        for item in parts_with_value:
            part = item['part']
            cumulative_value += item['value']
            if total_value &gt; 0:
                percentage = cumulative_value / total_value
            else:
                percentage = 0
            
            # 确定ABC分类
            if percentage &lt;= 0.8:
                abc_class = 'A'
            elif percentage &lt;= 0.95:
                abc_class = 'B'
            else:
                abc_class = 'C'
            
            # 分配货位
            target_locations = abc_locations.get(abc_class, [])
            if target_locations:
                loc_idx = location_pointers[abc_class] % len(target_locations)
                location = target_locations[loc_idx]
                
                # 更新备件
                part.warehouse_id = warehouse_id
                part.location_id = location.id
                
                location_pointers[abc_class] += 1
                assigned_count += 1
        
        logger.info("备件库位分配完成: %s 个备件已分配", assigned_count)
        return {
            'assigned_count': assigned_count,
            'total_parts': len(spare_parts)
        }
    
    def init_warehouse(self, warehouse_id, user_id=None):
        """
        一键初始化仓库完整流程
        
        Args:
            warehouse_id: 仓库ID
            user_id: 用户ID
            
        Returns:
            dict: 初始化结果报告
        """
        logger.info("开始一键初始化仓库, warehouse_id=%s", warehouse_id)
        start_time = datetime.now()
        
        try:
            with db.session.begin():
                # 1. 分析备件数据
                analysis_result = self.analyze_spare_parts(warehouse_id)
                
                # 2. 生成库区规划
                zone_plan = self.generate_zone_plan(analysis_result, warehouse_id)
                
                # 3. 创建库区
                zones = self.create_zones(warehouse_id, zone_plan, user_id)
                
                # 4. 创建货架
                racks = self.create_racks(zones, zone_plan)
                
                # 5. 创建货位
                locations = self.create_locations(racks, zone_plan)
                
                # 6. 分配备件库位
                assign_result = self.auto_assign_locations(warehouse_id, locations, analysis_result)
                
                # 7. 提交事务
                db.session.commit()
                
                # 生成报告
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                report = {
                    'success': True,
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_seconds': round(duration, 2),
                    'statistics': {
                        'zones_created': len(zones),
                        'racks_created': len(racks),
                        'locations_created': len(locations),
                        'parts_assigned': assign_result.get('assigned_count', 0)
                    },
                    'zone_plan': zone_plan,
                    'analysis_result': analysis_result,
                    'summary': '仓库智能初始化完成！'
                }
                
                logger.info("仓库初始化成功: %s", report)
                return report
                
        except Exception as e:
            db.session.rollback()
            logger.error("仓库初始化失败: %s", str(e), exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'summary': '仓库初始化失败，请查看日志'
            }

