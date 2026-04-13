from app import create_app, db
from app.models.warehouse_v3.quality_check import QualityCheckStandard
from app.models.spare_part import SparePart

app = create_app()

with app.app_context():
    # 获取一些备件
    spare_parts = SparePart.query.limit(5).all()
    
    if not spare_parts:
        print("[WARNING] 数据库中没有备件数据，请先添加备件")
    else:
        print(f"[OK] 找到 {len(spare_parts)} 个备件")
        
        # 为每个备件添加质检标准
        for part in spare_parts:
            # 外观检查
            standard1 = QualityCheckStandard(
                part_id=part.id,
                part_code=part.part_code if hasattr(part, 'part_code') else f"SP-{part.id:03d}",
                check_item='外观检查',
                check_method='visual',
                standard_value='无划痕、无变形、无锈蚀',
                severity_level='normal',
                is_active=True
            )
            
            # 尺寸检测
            standard2 = QualityCheckStandard(
                part_id=part.id,
                part_code=part.part_code if hasattr(part, 'part_code') else f"SP-{part.id:03d}",
                check_item='尺寸检测',
                check_method='measurement',
                standard_value='符合图纸要求',
                unit='mm',
                severity_level='major',
                is_active=True
            )
            
            db.session.add(standard1)
            db.session.add(standard2)
        
        db.session.commit()
        print(f"[OK] 成功添加 {len(spare_parts) * 2} 条质检标准")
