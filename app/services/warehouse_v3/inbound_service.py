"""
入库服务 V3
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.warehouse_v3.inbound import InboundOrderV3, InboundOrderItemV3
from app.extensions import db
import random
import string


class InboundV3Service:
    """入库服务 V3"""
    
    @staticmethod
    def create_inbound_order(data: Dict) -> InboundOrderV3:
        """创建入库单"""
        # 生成入库单号
        order_no = InboundV3Service._generate_order_no()
        
        order = InboundOrderV3(
            order_no=order_no,
            warehouse_id=data['warehouse_id'],
            order_type=data['order_type'],
            source_type=data.get('source_type'),
            source_id=data.get('source_id'),
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name'),
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
        """生成入库单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase, k=4))
        return f"IN{timestamp}{random_str}"
    
    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[InboundOrderV3]:
        """根据 ID 获取入库单"""
        return InboundOrderV3.query.filter_by(id=order_id).first()
    
    @staticmethod
    def get_all_orders(page: int = 1, per_page: int = 20, filters: Dict = None) -> Dict:
        """获取所有入库单（分页）"""
        query = InboundOrderV3.query
        
        if filters:
            if filters.get('warehouse_id'):
                query = query.filter_by(warehouse_id=filters['warehouse_id'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('order_type'):
                query = query.filter_by(order_type=filters['order_type'])
        
        pagination = query.order_by(InboundOrderV3.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }
    
    @staticmethod
    def receive_order(order_id: int, receive_data: List[Dict]) -> bool:
        """执行入库"""
        order = InboundV3Service.get_order_by_id(order_id)
        if not order:
            return False
        
        # 更新入库单状态
        order.status = 'completed'
        order.actual_date = datetime.now().date()
        order.updated_at = datetime.utcnow()
        
        # 更新明细
        for item_data in receive_data:
            item = InboundOrderItemV3.query.get(item_data['item_id'])
            if item:
                item.received_quantity = item_data.get('received_quantity', 0)
                item.inspection_status = item_data.get('inspection_status', 'passed')
                item.inspection_result = item_data.get('inspection_result', '合格')
        
        db.session.commit()
        return True
