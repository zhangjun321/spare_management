from app import db
from app.models.warehouse_v3.task_scheduler import TaskQueue, WarehouseTask, TaskScheduler, Worker
from app.models.warehouse_v3.outbound import OutboundOrderV3
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from decimal import Decimal
import json


class TaskQueueService:
    """任务队列服务"""
    
    @staticmethod
    def create_queue(queue_name, warehouse_id, queue_type, priority=5, max_capacity=1000):
        """
        创建任务队列
        :param queue_name: 队列名称
        :param warehouse_id: 仓库 ID
        :param queue_type: 队列类型（PICK/PUT/MOVE/COUNT/TRANSFER）
        :param priority: 优先级
        :param max_capacity: 最大容量
        :return: 任务队列
        """
        queue = TaskQueue(
            queue_name=queue_name,
            warehouse_id=warehouse_id,
            queue_type=queue_type,
            priority=priority,
            max_capacity=max_capacity
        )
        db.session.add(queue)
        db.session.commit()
        return queue
    
    @staticmethod
    def enqueue(task_data):
        """
        添加任务到队列
        :param task_data: 任务数据
        :return: 任务
        """
        queue_id = task_data.get('queue_id')
        queue = TaskQueue.query.get(queue_id)
        
        if not queue:
            return None
        
        if queue.current_size >= queue.max_capacity:
            return None  # 队列已满
        
        # 创建任务
        task = WarehouseTask(
            queue_id=queue_id,
            warehouse_id=queue.warehouse_id,
            task_type=task_data.get('task_type'),
            task_subtype=task_data.get('task_subtype'),
            priority=task_data.get('priority', queue.priority),
            part_id=task_data.get('part_id'),
            part_no=task_data.get('part_no'),
            part_name=task_data.get('part_name'),
            from_location_id=task_data.get('from_location_id'),
            to_location_id=task_data.get('to_location_id'),
            quantity=task_data.get('quantity'),
            unit=task_data.get('unit'),
            batch_no=task_data.get('batch_no'),
            source_type=task_data.get('source_type'),
            source_id=task_data.get('source_id'),
            source_no=task_data.get('source_no'),
            estimated_time=task_data.get('estimated_time'),
            route_sequence=task_data.get('route_sequence'),
            remark=task_data.get('remark')
        )
        
        task.task_no = TaskQueueService._generate_task_no()
        
        db.session.add(task)
        queue.current_size += 1
        db.session.commit()
        
        return task
    
    @staticmethod
    def dequeue(queue_id, scheduler_type='PRIORITY'):
        """
        从队列取出任务
        :param queue_id: 队列 ID
        :param scheduler_type: 调度类型
        :return: 任务
        """
        queue = TaskQueue.query.get(queue_id)
        if not queue or queue.current_size == 0:
            return None
        
        # 根据调度类型获取任务
        if scheduler_type == 'PRIORITY':
            # 按优先级排序
            task = WarehouseTask.query.filter_by(
                queue_id=queue_id,
                status='pending'
            ).order_by(WarehouseTask.priority.asc(), WarehouseTask.created_at.asc()).first()
        elif scheduler_type == 'FIRST_IN_FIRST_OUT':
            # 先进先出
            task = WarehouseTask.query.filter_by(
                queue_id=queue_id,
                status='pending'
            ).order_by(WarehouseTask.created_at.asc()).first()
        else:
            # 默认按优先级
            task = WarehouseTask.query.filter_by(
                queue_id=queue_id,
                status='pending'
            ).order_by(WarehouseTask.priority.asc(), WarehouseTask.created_at.asc()).first()
        
        if task:
            task.status = 'ready'
            queue.current_size -= 1
            db.session.commit()
        
        return task
    
    @staticmethod
    def get_queue_status(queue_id):
        """
        获取队列状态
        :param queue_id: 队列 ID
        :return: 队列状态
        """
        queue = TaskQueue.query.get(queue_id)
        if not queue:
            return None
        
        # 统计各状态任务数
        pending_count = WarehouseTask.query.filter_by(queue_id=queue_id, status='pending').count()
        ready_count = WarehouseTask.query.filter_by(queue_id=queue_id, status='ready').count()
        assigned_count = WarehouseTask.query.filter_by(queue_id=queue_id, status='assigned').count()
        working_count = WarehouseTask.query.filter_by(queue_id=queue_id, status='working').count()
        completed_count = WarehouseTask.query.filter_by(queue_id=queue_id, status='completed').count()
        
        return {
            'queue': queue.to_dict(),
            'statistics': {
                'pending': pending_count,
                'ready': ready_count,
                'assigned': assigned_count,
                'working': working_count,
                'completed': completed_count,
                'total': queue.current_size
            }
        }


class TaskSchedulerService:
    """任务调度服务"""
    
    @staticmethod
    def schedule_tasks(warehouse_id, scheduler_type='PRIORITY'):
        """
        调度任务
        :param warehouse_id: 仓库 ID
        :param scheduler_type: 调度类型
        :return: 调度结果
        """
        # 获取可用工人
        available_workers = Worker.query.filter_by(
            warehouse_id=warehouse_id,
            status='available'
        ).all()
        
        if not available_workers:
            return {'success': False, 'message': '没有可用工人'}
        
        # 获取活跃队列
        queues = TaskQueue.query.filter_by(
            warehouse_id=warehouse_id,
            status='active'
        ).order_by(TaskQueue.priority.asc()).all()
        
        scheduled_count = 0
        
        for queue in queues:
            # 从队列取出任务
            task = TaskQueueService.dequeue(queue.id, scheduler_type)
            
            if task:
                # 分配合适的工人
                worker = TaskSchedulerService._assign_worker(task, available_workers)
                
                if worker:
                    # 分配任务
                    TaskSchedulerService.assign_task_to_worker(task.id, worker.user_id)
                    scheduled_count += 1
                    
                    # 从可用工人列表移除
                    available_workers.remove(worker)
        
        return {
            'success': True,
            'message': f'成功调度{scheduled_count}个任务',
            'scheduled_count': scheduled_count
        }
    
    @staticmethod
    def _assign_worker(task, workers):
        """
        为任务分配工人
        :param task: 任务
        :param workers: 工人列表
        :return: 工人
        """
        if not workers:
            return None
        
        # 简单策略：选择效率评分最高的工人
        # TODO: 实现更复杂的技能匹配算法
        best_worker = max(workers, key=lambda w: w.efficiency_score)
        
        return best_worker
    
    @staticmethod
    def assign_task_to_worker(task_id, user_id):
        """
        分配任务给工人
        :param task_id: 任务 ID
        :param user_id: 用户 ID
        :return: 任务
        """
        task = WarehouseTask.query.get(task_id)
        if not task:
            return None
        
        worker = Worker.query.filter_by(user_id=user_id).first()
        if not worker or worker.status != 'available':
            return None
        
        # 更新任务状态
        task.status = 'assigned'
        task.assigned_to = user_id
        task.assigned_at = datetime.utcnow()
        
        # 更新工人状态
        worker.status = 'busy'
        worker.current_task_id = task_id
        worker.last_active_at = datetime.utcnow()
        
        db.session.commit()
        
        return task
    
    @staticmethod
    def start_task(task_id):
        """
        开始任务
        :param task_id: 任务 ID
        :return: 任务
        """
        task = WarehouseTask.query.get(task_id)
        if not task:
            return None
        
        task.status = 'working'
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        return task
    
    @staticmethod
    def complete_task(task_id, actual_time=None):
        """
        完成任务
        :param task_id: 任务 ID
        :param actual_time: 实际耗时
        :return: 任务
        """
        task = WarehouseTask.query.get(task_id)
        if not task:
            return None
        
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        
        if actual_time:
            task.actual_time = actual_time
        
        # 更新工人状态
        worker = Worker.query.filter_by(user_id=task.assigned_to).first()
        if worker:
            worker.status = 'available'
            worker.current_task_id = None
            worker.completed_tasks += 1
            
            # 更新效率评分
            if task.estimated_time and actual_time:
                efficiency = task.estimated_time / actual_time
                worker.efficiency_score = (worker.efficiency_score + efficiency * 10) / 2
        
        # 更新队列大小
        queue = TaskQueue.query.get(task.queue_id)
        if queue:
            queue.current_size += 1  # 任务完成，释放队列空间
        
        db.session.commit()
        
        return task
    
    @staticmethod
    def _generate_task_no():
        """生成任务号"""
        prefix = 'WT'
        date_str = datetime.now().strftime('%Y%m%d')
        
        last_task = WarehouseTask.query.filter(
            WarehouseTask.task_no.like(f'{prefix}{date_str}%')
        ).order_by(WarehouseTask.task_no.desc()).first()
        
        if last_task:
            last_no = int(last_task.task_no[-3:])
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f'{prefix}{date_str}{new_no:03d}'


class WorkerService:
    """工人服务"""
    
    @staticmethod
    def create_worker(user_id, warehouse_id, employee_no=None, skill_level=1):
        """
        创建工人
        :param user_id: 用户 ID
        :param warehouse_id: 仓库 ID
        :param employee_no: 工号
        :param skill_level: 技能等级
        :return: 工人
        """
        worker = Worker(
            user_id=user_id,
            warehouse_id=warehouse_id,
            employee_no=employee_no or f'EMP{user_id:05d}',
            skill_level=skill_level
        )
        db.session.add(worker)
        db.session.commit()
        return worker
    
    @staticmethod
    def update_worker_status(user_id, status):
        """
        更新工人状态
        :param user_id: 用户 ID
        :param status: 状态
        :return: 工人
        """
        worker = Worker.query.filter_by(user_id=user_id).first()
        if not worker:
            return None
        
        worker.status = status
        db.session.commit()
        
        return worker
    
    @staticmethod
    def get_available_workers(warehouse_id):
        """
        获取可用工人
        :param warehouse_id: 仓库 ID
        :return: 工人列表
        """
        workers = Worker.query.filter_by(
            warehouse_id=warehouse_id,
            status='available'
        ).order_by(Worker.efficiency_score.desc()).all()
        
        return [worker.to_dict() for worker in workers]
    
    @staticmethod
    def get_worker_statistics(warehouse_id=None):
        """
        获取工人统计
        :param warehouse_id: 仓库 ID
        :return: 统计数据
        """
        query = Worker.query
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        workers = query.all()
        
        total_workers = len(workers)
        available_workers = sum(1 for w in workers if w.status == 'available')
        busy_workers = sum(1 for w in workers if w.status == 'busy')
        offline_workers = sum(1 for w in workers if w.status == 'offline')
        
        total_tasks = sum(w.total_tasks for w in workers)
        completed_tasks = sum(w.completed_tasks for w in workers)
        
        avg_efficiency = sum(w.efficiency_score for w in workers) / total_workers if total_workers > 0 else 0
        
        return {
            'total_workers': total_workers,
            'available_workers': available_workers,
            'busy_workers': busy_workers,
            'offline_workers': offline_workers,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'avg_efficiency': round(avg_efficiency, 2)
        }
