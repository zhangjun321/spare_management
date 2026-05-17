import os
import sys
import traceback

sys.path.insert(0, r'd:\Trae\spare_management')
os.chdir(r'd:\Trae\spare_management')

output_file = r'd:\Trae\spare_management\debug_output.txt'

try:
    import logging
    logging.disable(logging.CRITICAL)

    from app import create_app
    app = create_app('development')

    with app.app_context():
        from app.models.spare_part import SparePart
        from app.models.maintenance import MaintenanceOrder
        from app.models.transaction import Transaction
        from app.models.equipment import Equipment
        from app.models.spare_part_advanced import SparePartQualityInspection, SparePartFaultRecord
        
        result = f"SpareParts={SparePart.query.count()}\n"
        result += f"Orders={MaintenanceOrder.query.count()}\n"
        result += f"Transactions={Transaction.query.count()}\n"
        result += f"Equipment={Equipment.query.count()}\n"
        result += f"QualityInspections={SparePartQualityInspection.query.count()}\n"
        result += f"FaultRecords={SparePartFaultRecord.query.count()}\n\n"
        
        # Sample spare parts
        for sp in SparePart.query.limit(5).all():
            result += f"SP: {sp.name} (stock={sp.current_stock}, status={sp.stock_status})\n"
        
        # Sample orders
        for o in MaintenanceOrder.query.limit(5).all():
            result += f"Order: {o.order_no} (status={o.status})\n"
        
        # Sample transactions
        for tx in Transaction.query.limit(5).all():
            result += f"TX: {tx.tx_type} qty={tx.total_qty}\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print("SUCCESS")
        print(result)
        
except Exception as e:
    error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(error_msg)
    print(error_msg)
