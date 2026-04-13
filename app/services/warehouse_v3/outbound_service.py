"""
出库服务 V3
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.warehouse_v3.outbound import OutboundOrderV3, OutboundOrderItemV3
from app.extensions import db
import random
import string


class OutboundV3Service:
    """出库服务 V3"""
    
    @staticmethod
    def create_outbound_order(data: Dict) -> OutboundOrderV3:
        """创建出库单"""
        # 生成出库单号
        order_no = OutboundV3Service._generate_order_no()
        
        order = OutboundOrderV3(
            order_no=order_no,
            warehouse_id=data['warehouse_id'],
            order_type=data['order_type'],
            destination_type=data.get('destination_type'),
            destination_id=data.get('destination_id'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name'),
            priority=data.get('priority', 'normal'),
            planned_date=data.get('planned_date'),
            expected_date=data.get('expected_date'),
            description=data.get('description'),
            remarks=data.get('remarks'),
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by')
        )
        
        db.session.add(order)
        db.session.commit()
        return order
    
    @staticmethod
    def _generate_order_no() -> str:
        """生成出库单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase, k=4))
        return f"OUT{timestamp}{random_str}"
    
    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[OutboundOrderV3]:
        """根据 ID 获取出库单"""
        return OutboundOrderV3.query.filter_by(id=order_id).first()
    
    @staticmethod
    def get_all_orders(page: int = 1, per_page: int = 20, filters: Dict = None) -> Dict:
        """获取所有出库单（分页）"""
        query = OutboundOrderV3.query
        
        if filters:
            if filters.get('warehouse_id'):
                query = query.filter_by(warehouse_id=filters['warehouse_id'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('order_type'):
                query = query.filter_by(order_type=filters['order_type'])
        
        pagination = query.order_by(OutboundOrderV3.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }
    
    @staticmethod
    def pick_order(order_id: int, pick_data: List[Dict]) -> bool:
        """执行拣货"""
        order = OutboundV3Service.get_order_by_id(order_id)
        if not order:
            return False
        
        # 更新拣货状态
        order.picking_status = 'completed'
        order.picking_date = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        
        # 更新明细
        for item_data in pick_data:
            item = OutboundOrderItemV3.query.get(item_data['item_id'])
            if item:
                item.picked_quantity = item_data.get('picked_quantity', 0)
                item.picking_status = 'completed'
        
        db.session.commit()
        return True
    
    @staticmethod
    def ship_order(order_id: int) -> bool:
        """执行出库"""
        order = OutboundV3Service.get_order_by_id(order_id)
        if not order:
            return False
        
        order.status = 'completed'
        order.actual_date = datetime.now().date()
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True
