from app import db
from app.models.warehouse_v3.wave_management import WavePlan, WaveOrder, WaveOrderItem, WaveTask, WaveTaskItem
from app.models.warehouse_v3.outbound import OutboundOrderV3
from app.models.warehouse_v3.inventory import InventoryV3
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from decimal import Decimal


class WaveGenerationService:
    """波次生成服务"""
    
    @staticmethod
    def generate_by_time_window(warehouse_id, time_window_minutes=60):
        """
        按时间窗口生成波次
        :param warehouse_id: 仓库 ID
        :param time_window_minutes: 时间窗口（分钟）
        :return: 生成的波次
        """
        # 获取待处理的出库单
        time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        pending_orders = OutboundOrderV3.query.filter(
            and_(
                OutboundOrderV3.warehouse_id == warehouse_id,
                OutboundOrderV3.status == 'pending',
                OutboundOrderV3.created_at >= time_threshold
            )
        ).all()
        
        if not pending_orders:
            return None
        
        # 按路线分组
        orders_by_route = {}
        for order in pending_orders:
            route = order.shipping_route or 'DEFAULT'
            if route not in orders_by_route:
                orders_by_route[route] = []
            orders_by_route[route].append(order)
        
        waves = []
        for route, orders in orders_by_route.items():
            wave = WaveGenerationService._create_wave(
                warehouse_id=warehouse_id,
                orders=orders,
                strategy_type='TIME',
                route_filter=route
            )
            waves.append(wave)
        
        return waves
    
    @staticmethod
    def generate_by_quantity(warehouse_id, max_orders=20, max_items=100):
        """
        按数量阈值生成波次
        :param warehouse_id: 仓库 ID
        :param max_orders: 最大订单数
        :param max_items: 最大商品项数
        :return: 生成的波次
        """
        # 获取待处理的出库单
        pending_orders = OutboundOrderV3.query.filter(
            and_(
                OutboundOrderV3.warehouse_id == warehouse_id,
                OutboundOrderV3.status == 'pending'
            )
        ).order_by(OutboundOrderV3.created_at.asc()).limit(max_orders).all()
        
        if not pending_orders:
            return None
        
        # 检查商品项数
        total_items = sum([len(order.items) for order in pending_orders])
        
        if total_items > max_items:
            # 超过阈值，分批处理
            waves = []
            current_batch = []
            current_items = 0
            
            for order in pending_orders:
                order_items = len(order.items)
                if current_items + order_items > max_items:
                    # 创建当前波次
                    wave = WaveGenerationService._create_wave(
                        warehouse_id=warehouse_id,
                        orders=current_batch,
                        strategy_type='QUANTITY'
                    )
                    waves.append(wave)
                    current_batch = []
                    current_items = 0
                
                current_batch.append(order)
                current_items += order_items
            
            # 创建最后一个波次
            if current_batch:
                wave = WaveGenerationService._create_wave(
                    warehouse_id=warehouse_id,
                    orders=current_batch,
                    strategy_type='QUANTITY'
                )
                waves.append(wave)
            
            return waves
        else:
            # 创建一个波次
            wave = WaveGenerationService._create_wave(
                warehouse_id=warehouse_id,
                orders=pending_orders,
                strategy_type='QUANTITY'
            )
            return [wave]
    
    @staticmethod
    def generate_by_plan(plan_id):
        """
        根据波次计划生成波次
        :param plan_id: 波次计划 ID
        :return: 生成的波次
        """
        plan = WavePlan.query.get(plan_id)
        if not plan:
            return None
        
        # 获取待处理的出库单
        query = OutboundOrderV3.query.filter(
            and_(
                OutboundOrderV3.warehouse_id == plan.warehouse_id,
                OutboundOrderV3.status == 'pending'
            )
        )
        
        # 应用筛选条件
        if plan.strategy_type == 'TIME' and plan.time_window:
            time_threshold = datetime.utcnow() - timedelta(minutes=plan.time_window)
            query = query.filter(OutboundOrderV3.created_at >= time_threshold)
        
        if plan.route_filter:
            query = query.filter(OutboundOrderV3.shipping_route == plan.route_filter)
        
        if plan.carrier_filter:
            query = query.filter(OutboundOrderV3.carrier == plan.carrier_filter)
        
        orders = query.order_by(OutboundOrderV3.created_at.asc()).all()
        
        if not orders:
            return None
        
        # 限制订单数
        if plan.max_orders and len(orders) > plan.max_orders:
            orders = orders[:plan.max_orders]
        
        wave = WaveGenerationService._create_wave(
            warehouse_id=plan.warehouse_id,
            orders=orders,
            strategy_type=plan.strategy_type,
            plan_id=plan.id,
            route_filter=plan.route_filter,
            carrier_filter=plan.carrier_filter
        )
        
        return wave
    
    @staticmethod
    def _create_wave(warehouse_id, orders, strategy_type, plan_id=None, route_filter=None, carrier_filter=None):
        """
        创建波次
        :param warehouse_id: 仓库 ID
        :param orders: 出库单列表
        :param strategy_type: 策略类型
        :param plan_id: 计划 ID
        :param route_filter: 路线筛选
        :param carrier_filter: 承运商筛选
        :return: 波次
        """
        # 生成波次号
        wave_no = WaveGenerationService._generate_wave_no()
        
        # 创建波次
        wave = WaveOrder(
            wave_no=wave_no,
            plan_id=plan_id,
            warehouse_id=warehouse_id,
            status='pending',
            total_orders=len(orders),
            total_items=0,
            total_quantity=0,
            created_by=1  # TODO: 从当前用户获取
        )
        
        db.session.add(wave)
        db.session.flush()
        
        # 添加波次订单项
        total_items = 0
        total_quantity = 0
        
        for order in orders:
            for item in order.items:
                wave_item = WaveOrderItem(
                    wave_id=wave.id,
                    outbound_order_id=order.id,
                    outbound_order_no=order.order_no,
                    part_id=item.part_id,
                    part_no=item.part.part_no if item.part else '',
                    part_name=item.part.part_name if item.part else '',
                    warehouse_id=warehouse_id,
                    location_id=item.location_id,
                    batch_no=item.batch_no,
                    required_quantity=item.quantity,
                    status='pending'
                )
                db.session.add(wave_item)
                total_items += 1
                total_quantity += float(item.quantity)
        
        wave.total_items = total_items
        wave.total_quantity = Decimal(str(total_quantity))
        db.session.commit()
        
        return wave
    
    @staticmethod
    def _generate_wave_no():
        """生成波次号"""
        prefix = 'WAVE'
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 获取当天最后一个波次号
        last_wave = WaveOrder.query.filter(
            WaveOrder.wave_no.like(f'{prefix}{date_str}%')
        ).order_by(WaveOrder.wave_no.desc()).first()
        
        if last_wave:
            last_no = int(last_wave.wave_no[-3:])
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f'{prefix}{date_str}{new_no:03d}'


class WaveTaskService:
    """波次任务服务"""
    
    @staticmethod
    def create_picking_tasks(wave_id):
        """
        创建拣货任务
        :param wave_id: 波次 ID
        :return: 任务列表
        """
        wave = WaveOrder.query.get(wave_id)
        if not wave:
            return []
        
        # 获取波次订单项，按库位分组
        items = WaveOrderItem.query.filter_by(wave_id=wave_id).all()
        
        # 按库位分组
        items_by_location = {}
        for item in items:
            location_id = item.location_id
            if location_id not in items_by_location:
                items_by_location[location_id] = []
            items_by_location[location_id].append(item)
        
        # 创建拣货任务
        tasks = []
        sequence = 1
        
        for location_id, location_items in items_by_location.items():
            task_no = WaveTaskService._generate_task_no()
            
            task = WaveTask(
                task_no=task_no,
                wave_id=wave_id,
                task_type='PICK',
                status='pending',
                priority=1,
                route_sequence=sequence,
                created_at=datetime.utcnow()
            )
            
            db.session.add(task)
            db.session.flush()
            
            # 添加任务明细
            for item in location_items:
                task_item = WaveTaskItem(
                    task_id=task.id,
                    wave_item_id=item.id,
                    part_id=item.part_id,
                    part_no=item.part_no,
                    location_id=location_id,
                    location_code=item.location.location_code if item.location else '',
                    batch_no=item.batch_no,
                    quantity=item.required_quantity,
                    sequence=sequence
                )
                db.session.add(task_item)
            
            tasks.append(task)
            sequence += 1
        
        db.session.commit()
        
        # 更新波次状态
        wave.status = 'picking'
        wave.started_at = datetime.utcnow()
        db.session.commit()
        
        return tasks
    
    @staticmethod
    def assign_task(task_id, user_id):
        """
        分配任务
        :param task_id: 任务 ID
        :param user_id: 用户 ID
        :return: 任务
        """
        task = WaveTask.query.get(task_id)
        if not task:
            return None
        
        task.assigned_to = user_id
        task.status = 'assigned'
        db.session.commit()
        
        return task
    
    @staticmethod
    def start_task(task_id):
        """
        开始任务
        :param task_id: 任务 ID
        :return: 任务
        """
        task = WaveTask.query.get(task_id)
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
        :param actual_time: 实际耗时（分钟）
        :return: 任务
        """
        task = WaveTask.query.get(task_id)
        if not task:
            return None
        
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        if actual_time:
            task.actual_time = actual_time
        
        # 更新任务明细状态
        task_items = WaveTaskItem.query.filter_by(task_id=task_id).all()
        for task_item in task_items:
            task_item.status = 'completed'
            # 更新波次订单项
            wave_item = WaveOrderItem.query.get(task_item.wave_item_id)
            if wave_item:
                wave_item.picked_quantity += task_item.quantity
                if wave_item.picked_quantity >= wave_item.required_quantity:
                    wave_item.status = 'completed'
        
        # 检查波次是否完成
        WaveTaskService._check_wave_completion(task.wave_id)
        
        db.session.commit()
        
        return task
    
    @staticmethod
    def _check_wave_completion(wave_id):
        """检查波次是否完成"""
        wave = WaveOrder.query.get(wave_id)
        if not wave:
            return
        
        # 统计完成情况
        total_items = wave.total_items
        completed_items = WaveOrderItem.query.filter_by(
            wave_id=wave_id,
            status='completed'
        ).count()
        
        wave.picked_items = completed_items
        wave.progress = Decimal(str((completed_items / total_items * 100) if total_items > 0 else 0))
        
        if completed_items >= total_items:
            wave.status = 'completed'
            wave.completed_at = datetime.utcnow()
    
    @staticmethod
    def _generate_task_no():
        """生成任务号"""
        prefix = 'TASK'
        date_str = datetime.now().strftime('%Y%m%d')
        
        last_task = WaveTask.query.filter(
            WaveTask.task_no.like(f'{prefix}{date_str}%')
        ).order_by(WaveTask.task_no.desc()).first()
        
        if last_task:
            last_no = int(last_task.task_no[-3:])
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f'{prefix}{date_str}{new_no:03d}'
