"""
更新设备编号前缀：SEC -> NUC
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.equipment import Equipment
from sqlalchemy import text

def update_equipment_codes():
    """更新设备编号前缀"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 开始更新设备编号前缀...")
            
            # 查询所有以 SEC 开头的设备
            equipments = Equipment.query.filter(Equipment.equipment_code.like('SEC-%')).all()
            
            if not equipments:
                print("\n✅ 没有找到需要更新的设备编号")
                return True
            
            print(f"\n📋 找到 {len(equipments)} 台设备需要更新：")
            
            # 更新设备编号
            for equipment in equipments:
                old_code = equipment.equipment_code
                new_code = old_code.replace('SEC-', 'NUC-', 1)
                print(f"  {old_code} -> {new_code}")
                equipment.equipment_code = new_code
            
            db.session.commit()
            
            print("\n" + "="*60)
            print("🎉 设备编号前缀更新完成！")
            print("="*60)
            print(f"\n共更新 {len(equipments)} 台设备")
            print("前缀：SEC -> NUC (NUCTECH)")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 更新失败：{e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = update_equipment_codes()
    sys.exit(0 if success else 1)
