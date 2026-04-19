"""
全局搜索 API - 全站搜索
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.spare_part import SparePart
from app.models.warehouse import Warehouse
from app.models.batch import Batch
from app.models.inbound_outbound import InboundOrder, OutboundOrder
from app.models.equipment import Equipment
from app.models.maintenance import MaintenanceRecord
from app.models.purchase import PurchaseOrder
from app.models.transaction import Transaction
from app.extensions import db

search_bp = Blueprint('search', __name__, url_prefix='/api')


@search_bp.route('/search')
@login_required
def search():
    """
    全站搜索接口
    支持搜索：仓库、备件、入库单、出库单、批次、设备、维修记录、采购单、交易记录等
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 1:
        return jsonify([])
    
    results = []
    
    try:
        # 1. 搜索仓库（优先级最高）
        warehouses = Warehouse.query.filter(
            db.or_(
                Warehouse.name.like(f'%{query}%'),
                Warehouse.code.like(f'%{query}%'),
                Warehouse.address.like(f'%{query}%')
            )
        ).limit(5).all()
        
        for wh in warehouses:
            results.append({
                'id': f'warehouse_{wh.id}',
                'type': 'warehouse',
                'title': f'{wh.name} ({wh.code})',
                'description': f'位置：{wh.location} | 状态：{"启用" if wh.is_active else "禁用"}',
                'url': f'/warehouses/{wh.id}',
                'icon': 'fa-warehouse',
                'category': '仓库'
            })
        
        # 2. 搜索备件
        spare_parts = SparePart.query.filter(
            db.or_(
                SparePart.name.like(f'%{query}%'),
                SparePart.code.like(f'%{query}%'),
                SparePart.model.like(f'%{query}%'),
                SparePart.spec.like(f'%{query}%'),
                SparePart.material.like(f'%{query}%')
            )
        ).limit(5).all()
        
        for sp in spare_parts:
            results.append({
                'id': f'spare_part_{sp.id}',
                'type': 'spare_part',
                'title': f'{sp.name} ({sp.code})',
                'description': f'型号：{sp.model} | 规格：{sp.spec} | 库存：{sp.stock_quantity}',
                'url': f'/spare_parts/{sp.id}',
                'icon': 'fa-box',
                'category': '备件'
            })
        
        # 3. 搜索入库单
        inbounds = InboundOrder.query.filter(
            db.or_(
                InboundOrder.order_code.like(f'%{query}%'),
                InboundOrder.batch_number.like(f'%{query}%')
            )
        ).limit(3).all()
        
        for inbound in inbounds:
            results.append({
                'id': f'inbound_{inbound.id}',
                'type': 'inbound',
                'title': f'入库单：{inbound.order_code}',
                'description': f'批次：{inbound.batch_number} | 状态：{inbound.status}',
                'url': f'/warehouses/inbound/{inbound.id}',
                'icon': 'fa-arrow-down',
                'category': '入库'
            })
        
        # 4. 搜索出库单
        outbounds = OutboundOrder.query.filter(
            db.or_(
                OutboundOrder.order_code.like(f'%{query}%'),
                OutboundOrder.batch_number.like(f'%{query}%')
            )
        ).limit(3).all()
        
        for outbound in outbounds:
            results.append({
                'id': f'outbound_{outbound.id}',
                'type': 'outbound',
                'title': f'出库单：{outbound.order_code}',
                'description': f'批次：{outbound.batch_number} | 状态：{outbound.status}',
                'url': f'/warehouses/outbound/{outbound.id}',
                'icon': 'fa-arrow-up',
                'category': '出库'
            })
        
        # 5. 搜索批次
        batches = Batch.query.filter(
            db.or_(
                Batch.batch_code.like(f'%{query}%'),
                Batch.serial_number.like(f'%{query}%')
            )
        ).limit(3).all()
        
        for batch in batches:
            results.append({
                'id': f'batch_{batch.id}',
                'type': 'batch',
                'title': f'批次：{batch.batch_code}',
                'description': f'序列号：{batch.serial_number} | 数量：{batch.quantity}',
                'url': f'/batches/{batch.id}',
                'icon': 'fa-layer-group',
                'category': '批次'
            })
        
        # 6. 搜索设备
        equipment_list = Equipment.query.filter(
            db.or_(
                Equipment.name.like(f'%{query}%'),
                Equipment.code.like(f'%{query}%'),
                Equipment.model.like(f'%{query}%')
            )
        ).limit(3).all()
        
        for eq in equipment_list:
            results.append({
                'id': f'equipment_{eq.id}',
                'type': 'equipment',
                'title': f'{eq.name} ({eq.code})',
                'description': f'型号：{eq.model} | 状态：{eq.status}',
                'url': f'/equipment/{eq.id}',
                'icon': 'fa-cogs',
                'category': '设备'
            })
        
        # 7. 搜索维修记录
        maintenance_records = MaintenanceRecord.query.filter(
            db.or_(
                MaintenanceRecord.record_code.like(f'%{query}%'),
                MaintenanceRecord.description.like(f'%{query}%')
            )
        ).limit(3).all()
        
        for record in maintenance_records:
            results.append({
                'id': f'maintenance_{record.id}',
                'type': 'maintenance',
                'title': f'维修记录：{record.record_code}',
                'description': f'{record.description[:50]}... | 状态：{record.status}',
                'url': f'/maintenance/{record.id}',
                'icon': 'fa-tools',
                'category': '维修'
            })
        
        # 8. 搜索采购单
        purchases = PurchaseOrder.query.filter(
            db.or_(
                PurchaseOrder.order_code.like(f'%{query}%'),
                PurchaseOrder.supplier.like(f'%{query}%')
            )
        ).limit(3).all()
        
        for purchase in purchases:
            results.append({
                'id': f'purchase_{purchase.id}',
                'type': 'purchase',
                'title': f'采购单：{purchase.order_code}',
                'description': f'供应商：{purchase.supplier} | 状态：{purchase.status}',
                'url': f'/purchase/{purchase.id}',
                'icon': 'fa-shopping-cart',
                'category': '采购'
            })
        
        # 9. 搜索交易记录
        transactions = Transaction.query.filter(
            db.or_(
                Transaction.transaction_code.like(f'%{query}%'),
                Transaction.remark.like(f'%{query}%')
            )
        ).limit(3).all()
        
        for trans in transactions:
            results.append({
                'id': f'transaction_{trans.id}',
                'type': 'transaction',
                'title': f'交易：{trans.transaction_code}',
                'description': f'{trans.remark[:50] if trans.remark else "无备注"} | 类型：{trans.transaction_type}',
                'url': f'/transactions/{trans.id}',
                'icon': 'fa-exchange-alt',
                'category': '交易'
            })
        
        # 按类别排序
        category_order = {
            '仓库': 0,
            '备件': 1,
            '入库': 2,
            '出库': 3,
            '批次': 4,
            '设备': 5,
            '维修': 6,
            '采购': 7,
            '交易': 8
        }
        results.sort(key=lambda x: category_order.get(x['category'], 99))
        
    except Exception as e:
        print(f"搜索出错：{e}")
        import traceback
        traceback.print_exc()
        return jsonify([])
    
    return jsonify(results)
