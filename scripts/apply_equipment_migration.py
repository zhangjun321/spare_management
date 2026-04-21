"""
设备管理高级功能数据库迁移脚本
执行日期: 2024-04-20
功能: 应用设备管理高级模型的数据库迁移
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions import db
from app.models.equipment_advanced import (
    EquipmentHealthIndex,
    EquipmentIotData,
    EquipmentPredictiveMaintenance,
    EquipmentPerformanceMetric,
    EquipmentComponent,
    EquipmentMaintenanceTask,
    EquipmentDocument
)

def create_tables_using_orm():
    """使用ORM创建表（推荐方式）"""
    print("🚀 使用 Flask-SQLAlchemy 创建表...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 创建所有新表
            db.create_all()
            
            print("✅ 所有表创建成功！")
            print("📋 已创建的表:")
            print("  - equipment_health_index")
            print("  - equipment_iot_data")
            print("  - equipment_predictive_maintenance")
            print("  - equipment_performance_metric")
            print("  - equipment_component")
            print("  - equipment_maintenance_task")
            print("  - equipment_document")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建表时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def create_tables_using_sql():
    """使用SQL脚本创建表（备用方式）"""
    print("🚀 使用SQL脚本创建表...")
    
    sql_file = project_root / "database" / "migrations" / "add_equipment_advanced_models.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL文件不存在: {sql_file}")
        return False
    
    app = create_app()
    
    with app.app_context():
        try:
            # 读取并执行SQL文件
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句（简单分割，实际可能需要更复杂的解析）
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for stmt in statements:
                if stmt:
                    db.session.execute(db.text(stmt))
            
            db.session.commit()
            
            print("✅ SQL迁移执行成功！")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 执行SQL时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def check_tables_exist():
    """检查表是否已存在"""
    print("🔍 检查表是否已存在...")
    
    app = create_app()
    
    with app.app_context():
        try:
            tables_to_check = [
                'equipment_health_index',
                'equipment_iot_data',
                'equipment_predictive_maintenance',
                'equipment_performance_metric',
                'equipment_component',
                'equipment_maintenance_task',
                'equipment_document'
            ]
            
            existing_tables = []
            missing_tables = []
            
            inspector = db.inspect(db.engine)
            all_tables = inspector.get_table_names()
            
            for table in tables_to_check:
                if table in all_tables:
                    existing_tables.append(table)
                else:
                    missing_tables.append(table)
            
            if existing_tables:
                print(f"✅ 已存在的表: {', '.join(existing_tables)}")
            
            if missing_tables:
                print(f"❌ 缺失的表: {', '.join(missing_tables)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 检查时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    print("=" * 80)
    print("📦 设备管理高级功能 - 数据库迁移")
    print("=" * 80)
    
    # 首先检查表
    print("\n1️⃣  检查当前状态...")
    if check_tables_exist():
        print("\n✅ 所有表都已存在！")
        return True
    
    # 使用ORM创建表
    print("\n2️⃣  使用ORM创建表...")
    if create_tables_using_orm():
        print("\n✅ 数据库迁移完成！")
        return True
    
    print("\n⚠️ ORM方式失败，尝试SQL方式...")
    
    # 使用SQL脚本作为备用
    if create_tables_using_sql():
        print("\n✅ 数据库迁移完成！")
        return True
    
    print("\n❌ 所有迁移方法都失败了！")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
