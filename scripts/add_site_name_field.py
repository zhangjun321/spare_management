"""
添加站点名称字段到数据库并生成站点名称
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.equipment import Equipment


def generate_site_name(equipment):
    """
    生成站点名称：[系列]-[城市]-[序号]
    例如：FS-北京-001、MT-上海-002
    """
    # 获取系列（如果没有，默认为FS）
    series = equipment.series or 'FS'
    
    # 从地址中提取城市
    city = '未知'
    if equipment.map_address:
        # 简单的城市提取逻辑
        cities = ['北京', '上海', '天津', '重庆', '广州', '深圳', '杭州', 
                  '南京', '武汉', '成都', '西安', '沈阳', '哈尔滨', '长春',
                  '石家庄', '郑州', '济南', '青岛', '合肥', '福州', '厦门',
                  '南昌', '长沙', '南宁', '海口', '昆明', '贵阳', '兰州',
                  '西宁', '银川', '乌鲁木齐', '拉萨', '呼和浩特', '太原']
        for c in cities:
            if c in equipment.map_address:
                city = c
                break
    elif equipment.location:
        for c in cities:
            if c in equipment.location:
                city = c
                break
    
    # 生成3位序号
    seq = str(equipment.id % 1000).zfill(3)
    
    return f"{series}-{city}-{seq}"


def migrate():
    app = create_app('development')
    
    with app.app_context():
        # 检查site_name字段是否已存在
        try:
            db.session.query(Equipment.site_name).first()
        except Exception as e:
            # 如果不存在，添加字段
            print("添加site_name字段到数据库...")
            
            # 使用SQL直接添加字段（跨数据库兼容的方式）
            try:
                from sqlalchemy import text
                db.session.execute(text('ALTER TABLE equipment ADD COLUMN site_name VARCHAR(100) COMMENT "站点名称"'))
                db.session.commit()
                print("✓ 字段添加成功")
            except Exception as e:
                print(f"字段可能已存在: {e}")
                db.session.rollback()
        
        # 为现有设备生成站点名称
        print("\n为现有设备生成站点名称...")
        equipments = Equipment.query.all()
        updated_count = 0
        
        for eq in equipments:
            if not eq.site_name:
                eq.site_name = generate_site_name(eq)
                updated_count += 1
                print(f"  {eq.equipment_code} -> {eq.site_name}")
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n✓ 更新了 {updated_count} 台设备的站点名称")
        else:
            print("\n所有设备都已有站点名称，无需更新")
        
        print("\n迁移完成！")


if __name__ == '__main__':
    migrate()
