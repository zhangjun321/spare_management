"""
添加thumbnail_url字段到spare_part表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

def migrate():
    app = create_app()
    
    with app.app_context():
        try:
            # 检查字段是否已存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('spare_part')]
            
            if 'thumbnail_url' not in columns:
                print("正在添加thumbnail_url字段...")
                # 使用原生SQL添加字段
                db.session.execute(
                    db.text("ALTER TABLE spare_part ADD COLUMN thumbnail_url VARCHAR(500) COMMENT '缩略图 URL'")
                )
                db.session.commit()
                print("✅ thumbnail_url字段添加成功！")
            else:
                print("ℹ️ thumbnail_url字段已存在，跳过迁移")
                
        except Exception as e:
            print(f"❌ 迁移失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
