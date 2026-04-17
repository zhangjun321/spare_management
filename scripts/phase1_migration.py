"""
Phase 1 数据库迁移脚本
- 添加 Transaction.approver_id / reject_reason 字段
- 添加索引优化
运行方式：python scripts/phase1_migration.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text


def run_migration():
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        
        # ALTER TABLE 步骤（可能失败：列已存在）
        alter_steps = [
            ("添加 transaction.approver_id",
             "ALTER TABLE `transaction` ADD COLUMN approver_id INTEGER"),
            ("添加 transaction.reject_reason",
             "ALTER TABLE `transaction` ADD COLUMN reject_reason TEXT"),
        ]

        # 索引步骤（MySQL 不支持 IF NOT EXISTS，通过 information_schema 检查）
        index_steps = [
            ("idx_sp_status_active", "spare_part",
             "CREATE INDEX idx_sp_status_active ON spare_part(stock_status, is_active)"),
            ("idx_sp_reorder", "spare_part",
             "CREATE INDEX idx_sp_reorder ON spare_part(reorder_point, current_stock)"),
            ("idx_ir_wh_part_status", "inventory_record",
             "CREATE INDEX idx_ir_wh_part_status ON inventory_record(warehouse_id, spare_part_id, stock_status)"),
            ("idx_ib_wh_status_date", "inbound_order",
             "CREATE INDEX idx_ib_wh_status_date ON inbound_order(warehouse_id, status, created_at)"),
            ("idx_ob_wh_status_date", "outbound_order",
             "CREATE INDEX idx_ob_wh_status_date ON outbound_order(warehouse_id, status, created_at)"),
            ("idx_tx_operator_date", "transaction",
             "CREATE INDEX idx_tx_operator_date ON `transaction`(operator_id, created_at)"),
        ]

        success = 0
        skipped = 0

        for desc, sql in alter_steps:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"  [OK] {desc}")
                success += 1
            except Exception as e:
                err = str(e).lower()
                if 'duplicate column' in err or 'already exists' in err or '1060' in str(e):
                    print(f"  [SKIP] {desc}（列已存在）")
                    skipped += 1
                else:
                    print(f"  [FAIL] {desc}: {e}")

        # 获取当前数据库名
        db_name_row = conn.execute(text("SELECT DATABASE()")).fetchone()
        db_name = db_name_row[0]

        for idx_name, table_name, sql in index_steps:
            # 检查索引是否已存在
            exists = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.STATISTICS "
                "WHERE table_schema=:db AND table_name=:tbl AND index_name=:idx"
            ), {"db": db_name, "tbl": table_name, "idx": idx_name}).scalar()

            if exists:
                print(f"  [SKIP] 创建 {idx_name}（索引已存在）")
                skipped += 1
            else:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  [OK] 创建 {idx_name}")
                    success += 1
                except Exception as e:
                    print(f"  [FAIL] 创建 {idx_name}: {e}")

        conn.close()
        print(f"\n迁移完成：成功 {success} 项，跳过 {skipped} 项")


if __name__ == '__main__':
    run_migration()
