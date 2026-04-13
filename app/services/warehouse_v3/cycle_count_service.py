from app import db
from app.models.warehouse_v3.cycle_count import CycleCountPlan, CycleCountItem, ABCClassification
from app.models.warehouse_v3.inventory import InventoryV3
from app.models.spare_part import SparePart
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from decimal import Decimal


class ABCClassificationService:
    """ABC 分类服务"""
    
    @staticmethod
    def calculate_abc_classification(warehouse_id=None):
        """
        计算 ABC 分类
        :param warehouse_id: 仓库 ID（可选，不传则计算所有仓库）
        """
        # 获取所有备件及其消耗金额
        query = db.session.query(
            SparePart.id,
            SparePart.part_no,
            SparePart.part_name,
            func.sum(InventoryV3.quantity * InventoryV3.unit_cost).label('total_value')
        ).join(InventoryV3, InventoryV3.part_id == SparePart.id)
        
        if warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == warehouse_id)
        
        query = query.group_by(SparePart.id)
        results = query.all()
        
        # 计算总价值
        total_value = sum([r.total_value for r in results])
        
        if total_value == 0:
            return {'success': False, 'message': '没有库存价值数据'}
        
        # 按价值降序排序
        sorted_results = sorted(results, key=lambda x: x.total_value, reverse=True)
        
        # 计算累计百分比并分类
        cumulative_value = 0
        abc_data = []
        
        for result in sorted_results:
            cumulative_value += result.total_value
            percentage = cumulative_value / total_value
            
            # ABC 分类标准：A 类 70%, B 类 20%, C 类 10%
            if percentage <= 0.7:
                abc_class = 'A'
            elif percentage <= 0.9:
                abc_class = 'B'
            else:
                abc_class = 'C'
            
            abc_data.append({
                'part_id': result.id,
                'warehouse_id': warehouse_id,
                'annual_consumption': float(result.total_value),
                'consumption_percentage': float(percentage),
                'abc_class': abc_class,
                'count_frequency': ABCClassification.get_count_frequency(abc_class)
            })
        
        # 保存到数据库
        for item in abc_data:
            existing = ABCClassification.query.filter_by(
                part_id=item['part_id'],
                warehouse_id=item['warehouse_id']
            ).first()
            
            if existing:
                existing.abc_class = item['abc_class']
                existing.annual_consumption = item['annual_consumption']
                existing.consumption_percentage = item['consumption_percentage']
                existing.count_frequency = item['count_frequency']
                existing.next_count_date = datetime.now().date() + timedelta(days=item['count_frequency'])
            else:
                abc = ABCClassification(**item)
                db.session.add(abc)
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'ABC 分类计算完成',
            'total_parts': len(abc_data),
            'class_a_count': sum(1 for x in abc_data if x['abc_class'] == 'A'),
            'class_b_count': sum(1 for x in abc_data if x['abc_class'] == 'B'),
            'class_c_count': sum(1 for x in abc_data if x['abc_class'] == 'C')
        }
    
    @staticmethod
    def get_parts_by_class(abc_class, warehouse_id=None):
        """
        获取指定 ABC 分类的备件
        :param abc_class: ABC 分类（A/B/C）
        :param warehouse_id: 仓库 ID
        :return: 备件列表
        """
        query = ABCClassification.query.filter_by(abc_class=abc_class)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        abc_items = query.all()
        return [item.to_dict() for item in abc_items]
    
    @staticmethod
    def get_due_for_count(warehouse_id=None):
        """
        获取到期需要盘点的物品
        :param warehouse_id: 仓库 ID
        :return: 到期物品列表
        """
        today = datetime.now().date()
        
        query = ABCClassification.query.filter(
            and_(
                ABCClassification.next_count_date <= today,
                ABCClassification.abc_class.isnot(None)
            )
        )
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        due_items = query.all()
        return [item.to_dict() for item in due_items]


class CycleCountPlanService:
    """循环盘点计划服务"""
    
    @staticmethod
    def create_plan_by_abc(abc_class, warehouse_id=None, plan_name=None, remark=None):
        """
        根据 ABC 分类创建盘点计划
        :param abc_class: ABC 分类（A/B/C）
        :param warehouse_id: 仓库 ID
        :param plan_name: 计划名称
        :param remark: 备注
        :return: 创建的盘点计划
        """
        # 生成计划号
        plan_no = CycleCountPlan.generate_plan_no()
        
        # 创建计划
        plan = CycleCountPlan(
            plan_no=plan_no,
            plan_name=plan_name or f'{abc_class}类物品循环盘点计划',
            plan_type='ABC',
            warehouse_id=warehouse_id,
            abc_class=abc_class,
            frequency=ABCClassification.get_count_frequency(abc_class),
            status='draft',
            created_by=1,  # TODO: 从当前用户获取
            remark=remark
        )
        
        db.session.add(plan)
        db.session.flush()  # 获取 plan.id
        
        # 添加盘点项目
        abc_items = ABCClassification.query.filter_by(abc_class=abc_class)
        if warehouse_id:
            abc_items = abc_items.filter_by(warehouse_id=warehouse_id)
        
        abc_items = abc_items.all()
        
        item_count = 0
        for abc_item in abc_items:
            # 获取库存信息
            inventory = InventoryV3.query.filter_by(
                part_id=abc_item.part_id,
                warehouse_id=warehouse_id
            ).first()
            
            if inventory:
                count_item = CycleCountItem(
                    plan_id=plan.id,
                    inventory_id=inventory.id,
                    part_id=inventory.part_id,
                    part_no=inventory.part.part_no if inventory.part else '',
                    part_name=inventory.part.part_name if inventory.part else '',
                    warehouse_id=inventory.warehouse_id,
                    location_id=inventory.location_id,
                    batch_no=inventory.batch_no,
                    book_quantity=inventory.quantity,
                    unit=inventory.unit,
                    status='pending'
                )
                db.session.add(count_item)
                item_count += 1
        
        # 更新计划总数
        plan.total_items = item_count
        db.session.commit()
        
        return plan
    
    @staticmethod
    def create_periodic_plan(warehouse_id, plan_name, start_date, end_date, remark=None):
        """
        创建定期盘点计划
        :param warehouse_id: 仓库 ID
        :param plan_name: 计划名称
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param remark: 备注
        :return: 创建的盘点计划
        """
        plan_no = CycleCountPlan.generate_plan_no()
        
        plan = CycleCountPlan(
            plan_no=plan_no,
            plan_name=plan_name,
            plan_type='PERIODIC',
            warehouse_id=warehouse_id,
            start_date=start_date,
            end_date=end_date,
            status='draft',
            created_by=1,  # TODO: 从当前用户获取
            remark=remark
        )
        
        db.session.add(plan)
        db.session.flush()
        
        # 添加仓库所有库存项目
        inventories = InventoryV3.query.filter_by(warehouse_id=warehouse_id).all()
        
        item_count = 0
        for inventory in inventories:
            count_item = CycleCountItem(
                plan_id=plan.id,
                inventory_id=inventory.id,
                part_id=inventory.part_id,
                part_no=inventory.part.part_no if inventory.part else '',
                part_name=inventory.part.part_name if inventory.part else '',
                warehouse_id=inventory.warehouse_id,
                location_id=inventory.location_id,
                batch_no=inventory.batch_no,
                book_quantity=inventory.quantity,
                unit=inventory.unit,
                status='pending'
            )
            db.session.add(count_item)
            item_count += 1
        
        plan.total_items = item_count
        db.session.commit()
        
        return plan
    
    @staticmethod
    def submit_for_approval(plan_id):
        """提交审批"""
        plan = CycleCountPlan.query.get(plan_id)
        if not plan:
            return None
        
        plan.status = 'pending_approval'
        db.session.commit()
        return plan
    
    @staticmethod
    def approve_plan(plan_id, approved_by):
        """审批计划"""
        plan = CycleCountPlan.query.get(plan_id)
        if not plan:
            return None
        
        plan.status = 'active'
        plan.approved_by = approved_by
        plan.approved_at = datetime.utcnow()
        db.session.commit()
        return plan
    
    @staticmethod
    def update_count_status(item_id, actual_quantity, counted_by, remark=None):
        """
        更新盘点结果
        :param item_id: 盘点项目 ID
        :param actual_quantity: 实际数量
        :param counted_by: 盘点人 ID
        :param remark: 备注
        :return: 盘点项目
        """
        item = CycleCountItem.query.get(item_id)
        if not item:
            return None
        
        item.actual_quantity = actual_quantity
        item.counted_by = counted_by
        item.counted_at = datetime.utcnow()
        item.status = 'counted'
        item.remark = remark
        
        # 计算差异
        item.calculate_variance()
        
        # 更新计划进度
        plan = CycleCountPlan.query.get(item.plan_id)
        if plan:
            plan.counted_items = CycleCountItem.query.filter_by(
                plan_id=plan.id,
                status='counted'
            ).count()
            
            # 统计差异物品数
            plan.variance_items = CycleCountItem.query.filter_by(
                plan_id=plan.id
            ).filter(
                CycleCountItem.variance_quantity != 0
            ).count()
        
        db.session.commit()
        return item
    
    @staticmethod
    def complete_plan(plan_id):
        """完成盘点计划"""
        plan = CycleCountPlan.query.get(plan_id)
        if not plan:
            return None
        
        # 检查是否所有项目都已盘点
        total = plan.total_items
        counted = CycleCountItem.query.filter_by(
            plan_id=plan_id,
            status='counted'
        ).count()
        
        if counted < total:
            return None
        
        plan.status = 'completed'
        db.session.commit()
        return plan
