from app import db
from app.models.warehouse_v3.location import WarehouseLocationV3 as Location
from app.models.warehouse_v3.wave_management import WaveTaskItem
from sqlalchemy import and_
from datetime import datetime
from decimal import Decimal
import math


class PathOptimizationService:
    """路径优化服务 - 实现 TSP（旅行商问题）算法"""
    
    @staticmethod
    def calculate_distance(location1, location2):
        """
        计算两个库位之间的距离
        :param location1: 库位 1
        :param location2: 库位 2
        :return: 距离（米）
        """
        if not location1 or not location2:
            return 0
        
        # 使用三维距离公式
        dx = (location2.x_coordinate or 0) - (location1.x_coordinate or 0)
        dy = (location2.y_coordinate or 0) - (location1.y_coordinate or 0)
        dz = (location2.z_coordinate or 0) - (location1.z_coordinate or 0)
        
        # 如果没有坐标，使用距离出口的差值
        if dx == 0 and dy == 0 and dz == 0:
            return abs((location2.distance_to_exit or 0) - (location1.distance_to_exit or 0))
        
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        return round(distance, 2)
    
    @staticmethod
    def nearest_neighbor_tsp(locations, start_location=None):
        """
        最近邻算法解决 TSP 问题
        :param locations: 库位列表
        :param start_location: 起始库位
        :return: 优化后的路径顺序
        """
        if not locations:
            return []
        
        # 如果没有指定起始点，使用距离出口最近的点
        if not start_location:
            start_location = min(locations, key=lambda loc: loc.distance_to_exit or 999)
        
        unvisited = [loc for loc in locations if loc.id != start_location.id]
        current = start_location
        path = [current]
        
        while unvisited:
            # 找到最近的未访问库位
            nearest = min(unvisited, key=lambda loc: PathOptimizationService.calculate_distance(current, loc))
            path.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return path
    
    @staticmethod
    def two_opt_tsp(locations, start_location=None):
        """
        2-opt 算法优化 TSP 路径
        :param locations: 库位列表
        :param start_location: 起始库位
        :return: 优化后的路径
        """
        # 先用最近邻算法获得初始路径
        path = PathOptimizationService.nearest_neighbor_tsp(locations, start_location)
        
        if len(path) <= 2:
            return path
        
        improved = True
        while improved:
            improved = False
            for i in range(1, len(path) - 1):
                for j in range(i + 1, len(path)):
                    # 尝试反转路径段
                    new_path = path[:i] + path[i:j+1][::-1] + path[j+1:]
                    
                    # 计算新旧路径长度
                    old_distance = PathOptimizationService.calculate_path_distance(path)
                    new_distance = PathOptimizationService.calculate_path_distance(new_path)
                    
                    if new_distance < old_distance:
                        path = new_path
                        improved = True
                        break
                
                if improved:
                    break
        
        return path
    
    @staticmethod
    def calculate_path_distance(path):
        """
        计算路径总长度
        :param path: 路径（库位列表）
        :return: 总距离
        """
        if not path or len(path) <= 1:
            return 0
        
        total_distance = 0
        for i in range(len(path) - 1):
            total_distance += PathOptimizationService.calculate_distance(path[i], path[i+1])
        
        return round(total_distance, 2)
    
    @staticmethod
    def optimize_picking_route(task_items):
        """
        优化拣货路径
        :param task_items: 拣货任务项列表
        :return: 优化后的路径
        """
        if not task_items:
            return []
        
        # 提取库位
        locations = []
        location_map = {}
        
        for item in task_items:
            if item.location and item.location not in locations:
                locations.append(item.location)
                location_map[item.location.id] = []
            
            if item.location:
                location_map[item.location.id].append(item)
        
        # 优化路径
        optimized_locations = PathOptimizationService.two_opt_tsp(locations)
        
        # 重新排序任务项
        optimized_items = []
        for location in optimized_locations:
            items_at_location = location_map.get(location.id, [])
            optimized_items.extend(items_at_location)
        
        return optimized_items
    
    @staticmethod
    def generate_s_shape_route(locations, start_location=None):
        """
        生成 S 型拣货路径（适用于传统仓库布局）
        :param locations: 库位列表
        :param start_location: 起始库位
        :return: S 型路径
        """
        if not locations:
            return []
        
        # 按通道分组
        aisles = {}
        for location in locations:
            aisle = location.aisle or 'UNKNOWN'
            if aisle not in aisles:
                aisles[aisle] = []
            aisles[aisle].append(location)
        
        # 对每个通道的库位排序
        for aisle in aisles:
            aisles[aisle].sort(key=lambda loc: loc.section or 0)
        
        # 按通道顺序生成 S 型路径
        sorted_aisles = sorted(aisles.keys())
        path = []
        
        for i, aisle in enumerate(sorted_aisles):
            aisle_locations = aisles[aisle]
            # 偶数通道从前往后，奇数通道从后往前
            if i % 2 == 0:
                path.extend(aisle_locations)
            else:
                path.extend(aisle_locations[::-1])
        
        return path
    
    @staticmethod
    def calculate_estimated_time(path, walking_speed=1.5, pick_time_per_item=0.5):
        """
        计算预计耗时
        :param path: 路径
        :param walking_speed: 步行速度（米/秒）
        :param pick_time_per_item: 每件拣货时间（分钟）
        :return: 预计耗时（分钟）
        """
        if not path:
            return 0
        
        # 计算行走时间
        total_distance = PathOptimizationService.calculate_path_distance(path)
        walking_time = (total_distance / walking_speed) / 60  # 转换为分钟
        
        # 计算拣货时间
        total_items = len(path)
        pick_time = total_items * pick_time_per_item
        
        return round(walking_time + pick_time, 2)


class RouteOptimizationService:
    """路线优化服务"""
    
    @staticmethod
    def optimize_wave_task_route(task_id):
        """
        优化波次任务的拣货路径
        :param task_id: 任务 ID
        :return: 优化结果
        """
        # 获取任务明细
        task_items = WaveTaskItem.query.filter_by(task_id=task_id).all()
        
        if not task_items:
            return {'success': False, 'message': '任务没有明细'}
        
        # 优化路径
        optimized_items = PathOptimizationService.optimize_picking_route(task_items)
        
        # 更新顺序
        for i, item in enumerate(optimized_items):
            item.sequence = i + 1
        
        db.session.commit()
        
        # 计算优化效果
        original_locations = [item.location for item in task_items if item.location]
        optimized_locations = list(set([item.location for item in optimized_items if item.location]))
        
        original_distance = PathOptimizationService.calculate_path_distance(original_locations)
        optimized_distance = PathOptimizationService.calculate_path_distance(optimized_locations)
        
        improvement = 0
        if original_distance > 0:
            improvement = ((original_distance - optimized_distance) / original_distance) * 100
        
        return {
            'success': True,
            'message': '路径优化成功',
            'data': {
                'original_distance': original_distance,
                'optimized_distance': optimized_distance,
                'improvement_percent': round(improvement, 2),
                'total_items': len(optimized_items),
                'estimated_time': PathOptimizationService.calculate_estimated_time(optimized_locations)
            }
        }
    
    @staticmethod
    def batch_optimize_routes(task_ids):
        """
        批量优化路径
        :param task_ids: 任务 ID 列表
        :return: 优化结果
        """
        results = []
        
        for task_id in task_ids:
            result = RouteOptimizationService.optimize_wave_task_route(task_id)
            results.append({
                'task_id': task_id,
                'result': result
            })
        
        total_improvement = sum([r['result']['data']['improvement_percent'] for r in results if r['result']['success']])
        avg_improvement = total_improvement / len(results) if results else 0
        
        return {
            'success': True,
            'message': f'批量优化{len(results)}个任务',
            'data': {
                'total_tasks': len(results),
                'average_improvement': round(avg_improvement, 2),
                'details': results
            }
        }
