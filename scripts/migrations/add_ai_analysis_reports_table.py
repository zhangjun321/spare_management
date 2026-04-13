"""
创建 AI 分析报告表的迁移脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def migrate():
    """执行数据库迁移"""
    app = create_app()
    
    with app.app_context():
        # 读取 SQL 文件
        sql_file = r'D:\Trae\spare_management\database\migrations\add_ai_analysis_reports_table.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 执行 SQL
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print("Success: Database migration completed. AI analysis reports table created.")
        except Exception as e:
            db.session.rollback()
            print(f"Error: Database migration failed: {e}")
            raise

if __name__ == '__main__':
    migrate()
