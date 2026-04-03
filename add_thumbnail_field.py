"""
直接添加thumbnail_url字段
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

def add_field():
    app = create_app()
    
    with app.app_context():
        try:
            print("正在添加thumbnail_url字段到spare_part表...")
            
            # 使用原生SQL添加字段
            db.session.execute(
                db.text("ALTER TABLE spare_part ADD COLUMN thumbnail_url VARCHAR(500) COMMENT '缩略图 URL'")
            )
            db.session.commit()
            
            print("✅ thumbnail_url字段添加成功！")
            
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("ℹ️ thumbnail_url字段已存在")
            else:
                print(f"❌ 错误: {str(e)}")
                db.session.rollback()

if __name__ == '__main__':
    add_field()
