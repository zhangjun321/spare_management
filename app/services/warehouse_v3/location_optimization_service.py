from app import db
from app.models.warehouse_v3.location_optimization import LocationOptimization, LocationHeatmap, LocationSuggestion
from app.models.warehouse_v3.inventory import InventoryV3
from app.models.warehouse_v3.outbound import OutboundOrderV3, OutboundOrderItemV3
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta
from decimal import Decimal


class LocationHeatmapService:
    """库位热度分析服务"""
    
    @staticmethod
    def update_location_heatmap(warehouse_id, location_id, operation_type='PICK', quantity=1):
        """
        更新库位热度
        :param warehouse_id: 仓库 ID
        :param location_id: 库位 ID
        :param operation_type: 操作类型（PICK/PUT/MOVE）
        :param quantity: 数量
        """
        today = datetime.now().date()
        
        # 查找或创建今日热度记录
        heatmap = LocationHeatmap.query.filter_by(
            warehouse_id=warehouse_id,
            location_id=location_id,
            date=today
        ).first()
        
        if not heatmap:
            heatmap = LocationHeatmap(
                warehouse_id=warehouse_id,
                location_id=location_id,
                date=today,
                pick_count=0,
                put_count=0,
                move_count=0
            )
            db.session.add(heatmap)
        
        # 更新计数
        if operation_type == 'PICK':
            heatmap.pick_count += quantity
        elif operation_type == 'PUT':
            heatmap.put_count += quantity
        elif operation_type == 'MOVE':
            heatmap.move_count += quantity
        
        heatmap.total_operations = heatmap.pick_count + heatmap.put_count + heatmap.move_count
        
        # 计算热度等级
        heatmap.heat_level = LocationHeatmapService._calculate_heat_level(heatmap.total_operations)
        
        db.session.commit()
        return heatmap
    
    @staticmethod
    def _calculate_heat_level(total_operations):
        """计算热度等级"""
        if total_operations >= 50:
            return 'HOT'
        elif total_operations >= 20:
            return 'WARM'
        else:
            return 'COLD'
    
    @staticmethod
    def get_location_heatmap(warehouse_id, start_date=None, end_date=None):
        """
        获取库位热度统计
        :param warehouse_id: 仓库 ID
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 热度统计列表
        """
        query = LocationHeatmap.query.filter_by(warehouse_id=warehouse_id)
        
        if start_date:
            query = query.filter(LocationHeatmap.date >= start_date)
        if end_date:
            query = query.filter(LocationHeatmap.date <= end_date)
        
        # 按库位分组统计
        results = db.session.query(
            LocationHeatmap.location_id,
            func.sum(LocationHeatmap.pick_count).label('total_pick'),
            func.sum(LocationHeatmap.put_count).label('total_put'),
            func.sum(LocationHeatmap.move_count).label('total_move'),
            func.sum(LocationHeatmap.total_operations).label('total_ops')
        ).filter_by(warehouse_id=warehouse_id)
        
        if start_date:
            results = results.filter(LocationHeatmap.date >= start_date)
        if end_date:
            results = results.filter(LocationHeatmap.date <= end_date)
        
        results = results.group_by(LocationHeatmap.location_id).all()
        
        heatmap_data = []
        for result in results:
            heatmap_data.append({
                'location_id': result.location_id,
                'total_pick': int(result.total_pick),
                'total_put': int(result.total_put),
                'total_move': int(result.total_move),
                'total_operations': int(result.total_ops),
                'heat_level': LocationHeatmapService._calculate_heat_level(int(result.total_ops))
            })
        
        # 按总操作数降序排序
        heatmap_data.sort(key=lambda x: x['total_operations'], reverse=True)
        
        return heatmap_data


class LocationOptimizationService:
    """库位优化服务"""
    
    @staticmethod
    def calculate_part_turnover(part_id, warehouse_id=None, days=30):
        """
        计算备件周转率
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :param days: 统计天数
        :return: 周转率
        """
        start_date = datetime.now().date() - timedelta(days=days)
        
        # 统计出库数量
        outbound_query = db.session.query(
            func.sum(OutboundOrderItemV3.quantity)
        ).join(
            OutboundOrderV3, OutboundOrderV3.id == OutboundOrderItemV3.outbound_order_id
        ).filter(
            and_(
                OutboundOrderItemV3.part_id == part_id,
                OutboundOrderV3.status == 'completed',
                OutboundOrderV3.created_at >= start_date
            )
        )
        
        if warehouse_id:
            outbound_query = outbound_query.filter(OutboundOrderV3.warehouse_id == warehouse_id)
        
        total_outbound = outbound_query.scalar() or 0
        
        # 获取当前库存
        inventory = InventoryV3.query.filter_by(part_id=part_id)
        if warehouse_id:
            inventory = inventory.filter_by(warehouse_id=warehouse_id)
        
        inventory_record = inventory.first()
        if not inventory_record or inventory_record.quantity == 0:
            return 0
        
        # 周转率 = 出库数量 / 平均库存
        turnover_rate = float(total_outbound) / float(inventory_record.quantity)
        
        return round(turnover_rate, 4)
    
    @staticmethod
    def analyze_pick_frequency(part_id, warehouse_id=None, days=30):
        """
        分析拣货频次
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :param days: 统计天数
        :return: 拣货频次
        """
        start_date = datetime.now().date() - timedelta(days=days)
        
        # 统计出库单次数
        outbound_query = db.session.query(
            func.count(func.distinct(OutboundOrderV3.id))
        ).join(
            OutboundOrderItemV3, OutboundOrderItemV3.outbound_order_id == OutboundOrderV3.id
        ).filter(
            and_(
                OutboundOrderItemV3.part_id == part_id,
                OutboundOrderV3.status == 'completed',
                OutboundOrderV3.created_at >= start_date
            )
        )
        
        if warehouse_id:
            outbound_query = outbound_query.filter(OutboundOrderV3.warehouse_id == warehouse_id)
        
        pick_frequency = outbound_query.scalar() or 0
        
        return pick_frequency
    
    @staticmethod
    def recommend_location(part_id, warehouse_id):
        """
        为备件推荐最优库位
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :return: 推荐库位 ID
        """
        # 计算周转率和拣货频次
        turnover_rate = LocationOptimizationService.calculate_part_turnover(part_id, warehouse_id)
        pick_frequency = LocationOptimizationService.analyze_pick_frequency(part_id, warehouse_id)
        
        # 获取备件信息
        inventory = InventoryV3.query.filter_by(part_id=part_id, warehouse_id=warehouse_id).first()
        if not inventory:
            return None
        
        # 根据周转率和频次确定存储策略
        if turnover_rate > 5 or pick_frequency > 20:
            # 高周转/高频次 - 推荐靠近出口的黄金库位
            storage_zone = 'A'  # 黄金区
            preferred_level = 'MIDDLE'  # 中层易拣选
        elif turnover_rate > 2 or pick_frequency > 10:
            # 中等周转 - 推荐次优库位
            storage_zone = 'B'  # 次优区
            preferred_level = 'MIDDLE'
        else:
            # 低周转 - 推荐边缘库位
            storage_zone = 'C'  # 低频区
            preferred_level = 'ANY'
        
        # 查询符合条件的空库位
        from app.models.location import Location
        from app.models.warehouse import Warehouse
        
        # 获取仓库信息
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return None
        
        # 查询可用库位
        available_locations = Location.query.filter(
            and_(
                Location.warehouse_id == warehouse_id,
                Location.zone == storage_zone,
                Location.is_occupied == False,
                Location.status == 'active'
            )
        )
        
        # 按优先级排序
        if preferred_level == 'MIDDLE':
            # 优先中层
            available_locations = available_locations.order_by(
                desc(Location.level == 'MIDDLE'),
                Location.distance_to_exit
            )
        else:
            available_locations = available_locations.order_by(Location.distance_to_exit)
        
        recommended_location = available_locations.first()
        
        if not recommended_location:
            # 如果没有完全匹配的，查询所有可用库位
            recommended_location = Location.query.filter(
                and_(
                    Location.warehouse_id == warehouse_id,
                    Location.is_occupied == False,
                    Location.status == 'active'
                )
            ).order_by(Location.distance_to_exit).first()
        
        return recommended_location
    
    @staticmethod
    def generate_optimization_suggestions(warehouse_id):
        """
        生成库位优化建议
        :param warehouse_id: 仓库 ID
        :return: 优化建议列表
        """
        # 获取仓库所有备件
        inventories = InventoryV3.query.filter_by(warehouse_id=warehouse_id).all()
        
        suggestions = []
        
        for inventory in inventories:
            part_id = inventory.part_id
            current_location_id = inventory.location_id
            
            # 计算周转率
            turnover_rate = LocationOptimizationService.calculate_part_turnover(
                part_id, warehouse_id
            )
            
            # 分析拣货频次
            pick_frequency = LocationOptimizationService.analyze_pick_frequency(
                part_id, warehouse_id
            )
            
            # 判断是否需要优化
            need_optimization = False
            reason = ''
            priority = 3
            expected_gain = 0
            
            # 高周转但位置偏远
            if turnover_rate > 5:
                current_location = inventory.location
                if current_location and current_location.distance_to_exit > 50:
                    need_optimization = True
                    reason = '高周转备件库位偏远'
                    priority = 1
                    expected_gain = 30
            
            # 高频次但在高层/低层
            elif pick_frequency > 20:
                current_location = inventory.location
                if current_location and current_location.level not in ['MIDDLE']:
                    need_optimization = True
                    reason = '高频次备件拣选不便'
                    priority = 2
                    expected_gain = 20
            
            if need_optimization:
                # 生成优化记录
                optimization = LocationOptimization(
                    warehouse_id=warehouse_id,
                    part_id=part_id,
                    current_location_id=current_location_id,
                    turnover_rate=Decimal(str(turnover_rate)),
                    pick_frequency=pick_frequency,
                    demand_stability='HIGH' if pick_frequency > 20 else ('MEDIUM' if pick_frequency > 10 else 'LOW'),
                    weight=inventory.weight if hasattr(inventory, 'weight') else None,
                    volume=inventory.volume if hasattr(inventory, 'volume') else None,
                    status='pending'
                )
                db.session.add(optimization)
                
                # 推荐库位
                recommended_location = LocationOptimizationService.recommend_location(
                    part_id, warehouse_id
                )
                
                if recommended_location:
                    optimization.recommended_location_id = recommended_location.id
                    optimization.optimization_score = Decimal('90') if priority == 1 else Decimal('70')
                    
                    # 创建建议
                    suggestion = LocationSuggestion(
                        warehouse_id=warehouse_id,
                        part_id=part_id,
                        part_no=inventory.part.part_no if inventory.part else '',
                        part_name=inventory.part.part_name if inventory.part else '',
                        suggested_location_id=recommended_location.id,
                        suggestion_reason=reason,
                        priority=priority,
                        expected_efficiency_gain=Decimal(str(expected_gain))
                    )
                    db.session.add(suggestion)
                    suggestions.append(suggestion)
        
        db.session.commit()
        return suggestions
