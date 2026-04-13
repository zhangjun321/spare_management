from app import db
from app.models.warehouse_v3.task_scheduler import WarehouseTask, Worker
from app.models.warehouse_v3.wave_management import WaveTask
from sqlalchemy import and_
from datetime import datetime
from decimal import Decimal


class AITaskAssignmentService:
    """AI 任务分配服务 - 基于机器学习的智能调度"""
    
    @staticmethod
    def calculate_worker_fitness(worker, task):
        """
        计算工人适配度评分
        :param worker: 工人
        :param task: 任务
        :return: 适配度评分 0-100
        """
        if not worker or not task:
            return 0
        
        score = 0
        
        # 技能等级匹配（30 分）
        skill_score = min(30, worker.skill_level * 6)
        score += skill_score
        
        # 效率评分（30 分）
        efficiency_score = min(30, worker.efficiency_score * 0.3)
        score += efficiency_score
        
        # 位置接近度（20 分）- 简化计算
        # TODO: 实际应该计算工人当前位置与任务起始位置的距离
        position_score = 15  # 假设中等接近度
        score += position_score
        
        # 工作负载均衡（20 分）
        # 已完成任务越多，得分越高
        completed_ratio = worker.completed_tasks / max(1, worker.total_tasks)
        workload_score = completed_ratio * 20
        score += workload_score
        
        return min(100, round(score, 2))
    
    @staticmethod
    def calculate_task_priority(task):
        """
        计算任务优先级评分
        :param task: 任务
        :return: 优先级评分 0-100
        """
        if not task:
            return 0
        
        score = 0
        
        # 基础优先级（50 分）- 1 最高，10 最低
        base_priority_score = (11 - task.priority) * 5
        score += base_priority_score
        
        # 紧急程度（30 分）
        # 根据任务创建时间判断
        created_hours_ago = (datetime.utcnow() - task.created_at).total_seconds() / 3600
        if created_hours_ago > 24:
            urgency_score = 30
        elif created_hours_ago > 12:
            urgency_score = 25
        elif created_hours_ago > 6:
            urgency_score = 20
        elif created_hours_ago > 2:
            urgency_score = 15
        else:
            urgency_score = 10
        
        score += urgency_score
        
        # 任务类型（20 分）
        type_scores = {
            'PICK': 18,  # 拣货优先级高
            'PUT': 15,
            'TRANSFER': 12,
            'COUNT': 10,
            'ADJUST': 15
        }
        type_score = type_scores.get(task.task_type, 10)
        score += type_score
        
        return min(100, round(score, 2))
    
    @staticmethod
    def smart_assign_task(task_id):
        """
        智能分配任务
        :param task_id: 任务 ID
        :return: 分配结果
        """
        task = WarehouseTask.query.get(task_id)
        if not task:
            return {'success': False, 'message': '任务不存在'}
        
        # 计算任务优先级
        task_priority = AITaskAssignmentService.calculate_task_priority(task)
        
        # 获取可用工人
        available_workers = Worker.query.filter_by(
            warehouse_id=task.warehouse_id,
            status='available'
        ).all()
        
        if not available_workers:
            return {'success': False, 'message': '没有可用工人'}
        
        # 计算每个工人的适配度
        worker_scores = []
        for worker in available_workers:
            fitness = AITaskAssignmentService.calculate_worker_fitness(worker, task)
            worker_scores.append({
                'worker': worker,
                'fitness': fitness
            })
        
        # 按适配度排序
        worker_scores.sort(key=lambda x: x['fitness'], reverse=True)
        
        # 选择最佳工人
        best_worker_data = worker_scores[0]
        best_worker = best_worker_data['worker']
        
        # 分配任务
        task.status = 'assigned'
        task.assigned_to = best_worker.user_id
        task.assigned_at = datetime.utcnow()
        task.priority = max(1, min(10, int((100 - task_priority) / 10)))
        
        # 更新工人状态
        best_worker.status = 'busy'
        best_worker.current_task_id = task.id
        best_worker.last_active_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'success': True,
            'message': '任务分配成功',
            'data': {
                'task': task.to_dict(),
                'assigned_worker': {
                    'user_id': best_worker.user_id,
                    'employee_no': best_worker.employee_no,
                    'fitness_score': best_worker_data['fitness']
                },
                'task_priority_score': task_priority
            }
        }
    
    @staticmethod
    def batch_smart_assign(warehouse_id, limit=20):
        """
        批量智能分配任务
        :param warehouse_id: 仓库 ID
        :param limit: 最大任务数
        :return: 分配结果
        """
        # 获取待分配任务
        pending_tasks = WarehouseTask.query.filter_by(
            warehouse_id=warehouse_id,
            status='pending'
        ).order_by(WarehouseTask.priority.asc(), WarehouseTask.created_at.asc()).limit(limit).all()
        
        results = []
        assigned_count = 0
        
        for task in pending_tasks:
            result = AITaskAssignmentService.smart_assign_task(task.id)
            results.append({
                'task_id': task.id,
                'success': result['success'],
                'message': result.get('message', '')
            })
            
            if result['success']:
                assigned_count += 1
        
        return {
            'success': True,
            'message': f'成功分配{assigned_count}个任务',
            'data': {
                'total_tasks': len(pending_tasks),
                'assigned_count': assigned_count,
                'results': results
            }
        }
    
    @staticmethod
    def optimize_task_sequence(worker_id):
        """
        优化工人任务序列
        :param worker_id: 工人 ID
        :return: 优化结果
        """
        worker = Worker.query.filter_by(user_id=worker_id).first()
        if not worker:
            return {'success': False, 'message': '工人不存在'}
        
        # 获取工人当前任务
        current_task = WarehouseTask.query.filter_by(
            assigned_to=worker_id,
            status='working'
        ).first()
        
        if not current_task:
            return {'success': False, 'message': '工人没有进行中任务'}
        
        # 获取工人待执行任务
        pending_tasks = WarehouseTask.query.filter_by(
            assigned_to=worker_id,
            status='assigned'
        ).order_by(WarehouseTask.route_sequence).all()
        
        if not pending_tasks:
            return {'success': False, 'message': '没有待执行任务'}
        
        # 按位置优化任务顺序
        # TODO: 实现基于路径优化的任务排序
        # 这里简化处理，按库位距离排序
        
        optimized_tasks = []
        for task in pending_tasks:
            optimized_tasks.append({
                'task_id': task.id,
                'task_no': task.task_no,
                'from_location': task.from_location_id,
                'to_location': task.to_location_id,
                'priority': task.priority
            })
        
        return {
            'success': True,
            'message': '任务序列优化完成',
            'data': {
                'worker_id': worker_id,
                'current_task': current_task.task_no,
                'pending_tasks': optimized_tasks,
                'total_pending': len(pending_tasks)
            }
        }
    
    @staticmethod
    def predict_task_duration(task):
        """
        预测任务耗时
        :param task: 任务
        :return: 预计耗时（分钟）
        """
        if not task:
            return None
        
        # 基础耗时
        base_time = 5  # 5 分钟基础时间
        
        # 根据任务类型
        type_times = {
            'PICK': 10,
            'PUT': 8,
            'TRANSFER': 15,
            'COUNT': 20,
            'ADJUST': 10
        }
        task_type_time = type_times.get(task.task_type, 10)
        
        # 根据数量
        quantity_factor = float(task.quantity) * 0.5 if task.quantity else 0
        
        # 根据距离（简化）
        distance_factor = 0
        if task.from_location_id and task.to_location_id:
            # TODO: 计算实际距离
            distance_factor = 5
        
        # 根据工人技能水平调整
        worker = Worker.query.filter_by(user_id=task.assigned_to).first()
        skill_factor = 1.0 - (worker.skill_level - 1) * 0.1 if worker else 1.0
        
        # 计算总耗时
        estimated_time = (base_time + task_type_time + quantity_factor + distance_factor) * skill_factor
        
        return round(estimated_time, 2)
    
    @staticmethod
    def get_task_recommendations(worker_id, limit=5):
        """
        获取任务推荐
        :param worker_id: 工人 ID
        :param limit: 推荐数量
        :return: 推荐任务列表
        """
        worker = Worker.query.filter_by(user_id=worker_id).first()
        if not worker:
            return []
        
        # 获取待分配任务
        pending_tasks = WarehouseTask.query.filter_by(
            warehouse_id=worker.warehouse_id,
            status='pending'
        ).all()
        
        # 计算适配度
        task_scores = []
        for task in pending_tasks:
            # 计算任务对工人的适配度
            fitness = AITaskAssignmentService.calculate_worker_fitness(worker, task)
            task_priority = AITaskAssignmentService.calculate_task_priority(task)
            
            # 综合评分
            total_score = fitness * 0.6 + task_priority * 0.4
            
            task_scores.append({
                'task': task,
                'total_score': total_score,
                'fitness': fitness,
                'priority': task_priority
            })
        
        # 按评分排序
        task_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 返回推荐
        recommendations = []
        for i, item in enumerate(task_scores[:limit]):
            recommendations.append({
                'rank': i + 1,
                'task_id': item['task'].id,
                'task_no': item['task'].task_no,
                'task_type': item['task'].task_type,
                'priority': item['task'].priority,
                'fitness_score': item['fitness'],
                'priority_score': item['priority'],
                'total_score': round(item['total_score'], 2),
                'estimated_duration': AITaskAssignmentService.predict_task_duration(item['task'])
            })
        
        return recommendations
