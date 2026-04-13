from app import db
from app.models.warehouse_v3.batch_genealogy import BatchGenealogy, BatchTrace
from app.models.warehouse_v3.inventory import InventoryV3
from sqlalchemy import and_
from datetime import datetime


class BatchGenealogyService:
    """批次谱系服务"""
    
    @staticmethod
    def create_split_genealogy(parent_batch_id, child_batch_ids, quantities, operation_type=None, operation_id=None, remark=None):
        """
        创建批次拆分谱系关系
        :param parent_batch_id: 父批次 ID
        :param child_batch_ids: 子批次 ID 列表
        :param quantities: 数量列表
        :param operation_type: 操作类型
        :param operation_id: 操作单据 ID
        :param remark: 备注
        """
        genealogies = []
        for i, child_batch_id in enumerate(child_batch_ids):
            genealogy = BatchGenealogy.create_genealogy(
                child_batch_id=child_batch_id,
                parent_batch_id=parent_batch_id,
                relationship_type='SPLIT',
                quantity=quantities[i] if i < len(quantities) else 0,
                operation_type=operation_type,
                operation_id=operation_id,
                remark=remark
            )
            genealogies.append(genealogy)
        
        db.session.commit()
        return genealogies
    
    @staticmethod
    def create_merge_genealogy(parent_batch_id, child_batch_ids, quantities, operation_type=None, operation_id=None, remark=None):
        """
        创建批次合并谱系关系
        :param parent_batch_id: 父批次 ID（合并后的批次）
        :param child_batch_ids: 子批次 ID 列表（被合并的批次）
        :param quantities: 数量列表
        :param operation_type: 操作类型
        :param operation_id: 操作单据 ID
        :param remark: 备注
        """
        genealogies = []
        for i, child_batch_id in enumerate(child_batch_ids):
            genealogy = BatchGenealogy.create_genealogy(
                child_batch_id=parent_batch_id,
                parent_batch_id=child_batch_id,
                relationship_type='MERGE',
                quantity=quantities[i] if i < len(quantities) else 0,
                operation_type=operation_type,
                operation_id=operation_id,
                remark=remark
            )
            genealogies.append(genealogy)
        
        db.session.commit()
        return genealogies
    
    @staticmethod
    def get_batch_genealogy(inventory_id, direction='both', depth=10):
        """
        获取批次谱系（向上或向下追溯）
        :param inventory_id: 批次 ID
        :param direction: 追溯方向：'up'(向上)/'down'(向下)/'both'(双向)
        :param depth: 追溯深度
        :return: 谱系树
        """
        result = {
            'current_batch': None,
            'parents': [],
            'children': []
        }
        
        # 获取当前批次信息
        inventory = InventoryV3.query.get(inventory_id)
        if inventory:
            result['current_batch'] = inventory.to_dict()
        
        if direction in ['up', 'both']:
            # 向上追溯（查找父批次）
            result['parents'] = BatchGenealogyService._trace_up(inventory_id, depth)
        
        if direction in ['down', 'both']:
            # 向下追溯（查找子批次）
            result['children'] = BatchGenealogyService._trace_down(inventory_id, depth)
        
        return result
    
    @staticmethod
    def _trace_up(inventory_id, depth, current_depth=0):
        """向上追溯父批次"""
        if current_depth >= depth:
            return []
        
        genealogies = BatchGenealogy.query.filter_by(child_batch_id=inventory_id).all()
        result = []
        
        for genealogy in genealogies:
            parent_info = genealogy.to_dict()
            parent_inventory = InventoryV3.query.get(genealogy.parent_batch_id)
            if parent_inventory:
                parent_info['parent_batch_info'] = parent_inventory.to_dict()
                # 递归追溯更上层
                parent_info['ancestors'] = BatchGenealogyService._trace_up(
                    genealogy.parent_batch_id, depth, current_depth + 1
                )
            result.append(parent_info)
        
        return result
    
    @staticmethod
    def _trace_down(inventory_id, depth, current_depth=0):
        """向下追溯子批次"""
        if current_depth >= depth:
            return []
        
        genealogies = BatchGenealogy.query.filter_by(parent_batch_id=inventory_id).all()
        result = []
        
        for genealogy in genealogies:
            child_info = genealogy.to_dict()
            child_inventory = InventoryV3.query.get(genealogy.child_batch_id)
            if child_inventory:
                child_info['child_batch_info'] = child_inventory.to_dict()
                # 递归追溯更下层
                child_info['descendants'] = BatchGenealogyService._trace_down(
                    genealogy.child_batch_id, depth, current_depth + 1
                )
            result.append(child_info)
        
        return result
    
    @staticmethod
    def get_batch_full_trace(inventory_id):
        """
        获取批次完整追溯链（包含谱系和流转记录）
        :param inventory_id: 批次 ID
        :return: 完整追溯信息
        """
        inventory = InventoryV3.query.get(inventory_id)
        if not inventory:
            return None
        
        result = {
            'batch_info': inventory.to_dict(),
            'genealogy': BatchGenealogyService.get_batch_genealogy(inventory_id, 'both', 10),
            'trace_records': []
        }
        
        # 获取流转记录
        trace_records = BatchTrace.query.filter_by(inventory_id=inventory_id)\
            .order_by(BatchTrace.operation_time.asc()).all()
        
        result['trace_records'] = [trace.to_dict() for trace in trace_records]
        
        return result


class BatchTraceService:
    """批次追溯服务"""
    
    @staticmethod
    def create_inbound_trace(inventory, inbound_order_id, operator_id=None, remark=None):
        """创建入库追溯记录"""
        return BatchTrace.create_trace(
            batch_no=inventory.batch_no,
            inventory_id=inventory.id,
            part_id=inventory.part_id,
            trace_type='INBOUND',
            quantity=inventory.quantity,
            source_type='inbound_order',
            source_id=inbound_order_id,
            warehouse_id=inventory.warehouse_id,
            location_id=inventory.location_id,
            operator_id=operator_id,
            remark=remark
        )
    
    @staticmethod
    def create_outbound_trace(inventory, quantity, outbound_order_id, operator_id=None, remark=None):
        """创建出库追溯记录"""
        return BatchTrace.create_trace(
            batch_no=inventory.batch_no,
            inventory_id=inventory.id,
            part_id=inventory.part_id,
            trace_type='OUTBOUND',
            quantity=quantity,
            source_type='outbound_order',
            source_id=outbound_order_id,
            warehouse_id=inventory.warehouse_id,
            location_id=inventory.location_id,
            operator_id=operator_id,
            remark=remark
        )
    
    @staticmethod
    def create_transfer_trace(inventory, quantity, from_location_id, to_location_id, 
                             transfer_order_id, operator_id=None, remark=None):
        """创建调拨追溯记录"""
        return BatchTrace.create_trace(
            batch_no=inventory.batch_no,
            inventory_id=inventory.id,
            part_id=inventory.part_id,
            trace_type='TRANSFER',
            quantity=quantity,
            source_type='transfer_order',
            source_id=transfer_order_id,
            warehouse_id=inventory.warehouse_id,
            location_id=to_location_id,
            operator_id=operator_id,
            remark=remark
        )
    
    @staticmethod
    def create_adjust_trace(inventory, quantity, adjust_order_id, operator_id=None, remark=None):
        """创建调整追溯记录"""
        return BatchTrace.create_trace(
            batch_no=inventory.batch_no,
            inventory_id=inventory.id,
            part_id=inventory.part_id,
            trace_type='ADJUST',
            quantity=quantity,
            source_type='adjust_order',
            source_id=adjust_order_id,
            warehouse_id=inventory.warehouse_id,
            location_id=inventory.location_id,
            operator_id=operator_id,
            remark=remark
        )
    
    @staticmethod
    def get_part_trace(part_id, warehouse_id=None, start_date=None, end_date=None):
        """
        获取备件批次追溯记录
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID（可选）
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 追溯记录列表
        """
        query = BatchTrace.query.filter_by(part_id=part_id)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if start_date:
            query = query.filter(BatchTrace.operation_time >= start_date)
        
        if end_date:
            query = query.filter(BatchTrace.operation_time <= end_date)
        
        traces = query.order_by(BatchTrace.operation_time.desc()).all()
        return [trace.to_dict() for trace in traces]
    
    @staticmethod
    def get_batch_trace_by_batch_no(batch_no):
        """
        根据批次号获取追溯记录
        :param batch_no: 批次号
        :return: 追溯记录列表
        """
        traces = BatchTrace.query.filter_by(batch_no=batch_no)\
            .order_by(BatchTrace.operation_time.desc()).all()
        return [trace.to_dict() for trace in traces]
    
    @staticmethod
    def get_inventory_trace(inventory_id):
        """
        获取库存批次完整追溯链
        :param inventory_id: 库存 ID
        :return: 追溯记录列表（按时间排序）
        """
        traces = BatchTrace.query.filter_by(inventory_id=inventory_id)\
            .order_by(BatchTrace.operation_time.asc()).all()
        return [trace.to_dict() for trace in traces]
