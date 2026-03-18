"""
全面检查和修复数据库表结构
添加所有缺失的字段
"""

import sys
import os
import pymysql
from dotenv import load_dotenv

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# 获取数据库配置
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'spare_parts_db')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')

# 定义所有表应该有的字段
TABLE_FIELDS = {
    'spare_part': [
        ('part_code', 'VARCHAR(50)', '备件代码'),
        ('name', 'VARCHAR(200)', '备件名称'),
        ('specification', 'VARCHAR(200)', '规格型号'),
        ('category_id', 'INT', '分类 ID'),
        ('supplier_id', 'INT', '供应商 ID'),
        ('current_stock', 'INT', '当前库存'),
        ('stock_status', 'VARCHAR(20)', '库存状态'),
        ('min_stock', 'INT', '最低库存'),
        ('max_stock', 'INT', '最高库存'),
        ('unit', 'VARCHAR(20)', '单位'),
        ('unit_price', 'DECIMAL(10,2)', '单价'),
        ('location', 'VARCHAR(200)', '存放位置'),
        ('image_url', 'VARCHAR(500)', '图片 URL'),
        ('remark', 'TEXT', '备注'),
        ('is_active', 'TINYINT(1)', '是否启用'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'equipment': [
        ('equipment_code', 'VARCHAR(50)', '设备代码'),
        ('name', 'VARCHAR(200)', '设备名称'),
        ('model', 'VARCHAR(100)', '型号'),
        ('category', 'VARCHAR(50)', '类别'),
        ('department_id', 'INT', '使用部门 ID'),
        ('location', 'VARCHAR(200)', '安装位置'),
        ('status', 'VARCHAR(20)', '状态'),
        ('purchase_date', 'DATE', '购买日期'),
        ('warranty_expiry', 'DATE', '保修到期日期'),
        ('supplier_id', 'INT', '供应商 ID'),
        ('purchase_price', 'DECIMAL(10,2)', '购买价格'),
        ('remark', 'TEXT', '备注'),
        ('is_active', 'TINYINT(1)', '是否启用'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'maintenance_order': [
        ('order_number', 'VARCHAR(50)', '工单编号'),
        ('equipment_id', 'INT', '设备 ID'),
        ('title', 'VARCHAR(200)', '工单标题'),
        ('description', 'TEXT', '工单描述'),
        ('priority', 'VARCHAR(20)', '优先级'),
        ('type', 'VARCHAR(20)', '工单类型'),
        ('status', 'VARCHAR(20)', '状态'),
        ('requester_id', 'INT', '报修人 ID'),
        ('assigned_to', 'INT', '指派给'),
        ('scheduled_date', 'DATETIME', '计划日期'),
        ('completed_date', 'DATETIME', '完成日期'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
    ],
    'maintenance_task': [
        ('order_id', 'INT', '工单 ID'),
        ('task_name', 'VARCHAR(200)', '任务名称'),
        ('description', 'TEXT', '任务描述'),
        ('status', 'VARCHAR(20)', '状态'),
        ('assigned_to', 'INT', '指派给'),
        ('started_at', 'DATETIME', '开始时间'),
        ('completed_at', 'DATETIME', '完成时间'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
    ],
    'maintenance_record': [
        ('order_id', 'INT', '工单 ID'),
        ('equipment_id', 'INT', '设备 ID'),
        ('maintenance_type', 'VARCHAR(20)', '维修类型'),
        ('description', 'TEXT', '维修描述'),
        ('spare_parts_used', 'TEXT', '使用的备件'),
        ('maintenance_result', 'TEXT', '维修结果'),
        ('maintenance_by', 'INT', '维修人 ID'),
        ('started_at', 'DATETIME', '开始时间'),
        ('completed_at', 'DATETIME', '完成时间'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
    ],
    'maintenance_cost': [
        ('order_id', 'INT', '工单 ID'),
        ('cost_type', 'VARCHAR(20)', '费用类型'),
        ('description', 'VARCHAR(200)', '费用描述'),
        ('amount', 'DECIMAL(10,2)', '金额'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'batch': [
        ('batch_number', 'VARCHAR(50)', '批次号'),
        ('spare_part_id', 'INT', '备件 ID'),
        ('warehouse_id', 'INT', '仓库 ID'),
        ('quantity', 'INT', '批次数量'),
        ('production_date', 'DATE', '生产日期'),
        ('expiry_date', 'DATE', '过期日期'),
        ('supplier_id', 'INT', '供应商 ID'),
        ('purchase_price', 'DECIMAL(10,2)', '采购价格'),
        ('location_id', 'INT', '库位 ID'),
        ('status', 'VARCHAR(20)', '状态'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'warehouse_location': [
        ('warehouse_id', 'INT', '仓库 ID'),
        ('location_code', 'VARCHAR(50)', '库位代码'),
        ('location_name', 'VARCHAR(100)', '库位名称'),
        ('location_type', 'VARCHAR(20)', '库位类型'),
        ('max_capacity', 'INT', '最大容量'),
        ('current_capacity', 'INT', '当前容量'),
        ('status', 'VARCHAR(20)', '状态'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'serial_number': [
        ('serial_number', 'VARCHAR(100)', '序列号'),
        ('spare_part_id', 'INT', '备件 ID'),
        ('batch_id', 'INT', '批次 ID'),
        ('equipment_id', 'INT', '设备 ID'),
        ('status', 'VARCHAR(20)', '状态'),
        ('purchase_date', 'DATE', '购买日期'),
        ('warranty_expiry', 'DATE', '保修到期日期'),
        ('supplier_id', 'INT', '供应商 ID'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'transaction': [
        ('transaction_number', 'VARCHAR(50)', '交易编号'),
        ('transaction_type', 'VARCHAR(20)', '交易类型'),
        ('spare_part_id', 'INT', '备件 ID'),
        ('batch_id', 'INT', '批次 ID'),
        ('warehouse_id', 'INT', '仓库 ID'),
        ('quantity', 'INT', '数量'),
        ('unit_price', 'DECIMAL(10,2)', '单价'),
        ('total_amount', 'DECIMAL(10,2)', '总金额'),
        ('related_order_id', 'INT', '关联单据 ID'),
        ('related_order_type', 'VARCHAR(20)', '关联单据类型'),
        ('transaction_date', 'DATETIME', '交易日期'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('created_by', 'INT', '创建人 ID'),
        ('confirmed_by', 'INT', '确认人 ID'),
        ('confirmed_at', 'DATETIME', '确认时间'),
        ('status', 'VARCHAR(20)', '状态'),
    ],
    'transaction_detail': [
        ('transaction_id', 'INT', '交易 ID'),
        ('spare_part_id', 'INT', '备件 ID'),
        ('batch_id', 'INT', '批次 ID'),
        ('quantity', 'INT', '数量'),
        ('unit_price', 'DECIMAL(10,2)', '单价'),
        ('total_amount', 'DECIMAL(10,2)', '总金额'),
        ('remark', 'TEXT', '备注'),
    ],
    'purchase_plan': [
        ('plan_number', 'VARCHAR(50)', '计划编号'),
        ('title', 'VARCHAR(200)', '计划标题'),
        ('description', 'TEXT', '计划描述'),
        ('status', 'VARCHAR(20)', '状态'),
        ('total_amount', 'DECIMAL(10,2)', '总金额'),
        ('planned_by', 'INT', '计划人 ID'),
        ('approved_by', 'INT', '批准人 ID'),
        ('planned_date', 'DATE', '计划日期'),
        ('approved_date', 'DATETIME', '批准日期'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
    ],
    'purchase_request': [
        ('request_number', 'VARCHAR(50)', '申请编号'),
        ('plan_id', 'INT', '计划 ID'),
        ('spare_part_id', 'INT', '备件 ID'),
        ('quantity', 'INT', '申请数量'),
        ('unit', 'VARCHAR(20)', '单位'),
        ('estimated_price', 'DECIMAL(10,2)', '预估单价'),
        ('estimated_total', 'DECIMAL(10,2)', '预估总价'),
        ('reason', 'TEXT', '申请原因'),
        ('status', 'VARCHAR(20)', '状态'),
        ('requested_by', 'INT', '申请人 ID'),
        ('approved_by', 'INT', '批准人 ID'),
        ('requested_date', 'DATETIME', '申请日期'),
        ('approved_date', 'DATETIME', '批准日期'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
    ],
    'purchase_order': [
        ('order_number', 'VARCHAR(50)', '订单编号'),
        ('supplier_id', 'INT', '供应商 ID'),
        ('title', 'VARCHAR(200)', '订单标题'),
        ('status', 'VARCHAR(20)', '状态'),
        ('total_amount', 'DECIMAL(10,2)', '总金额'),
        ('order_date', 'DATETIME', '订单日期'),
        ('expected_delivery_date', 'DATE', '预计交货日期'),
        ('actual_delivery_date', 'DATE', '实际交货日期'),
        ('received_by', 'INT', '收货人 ID'),
        ('approved_by', 'INT', '批准人 ID'),
        ('approved_date', 'DATETIME', '批准日期'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'purchase_order_item': [
        ('order_id', 'INT', '订单 ID'),
        ('request_id', 'INT', '申请 ID'),
        ('spare_part_id', 'INT', '备件 ID'),
        ('quantity', 'INT', '数量'),
        ('unit_price', 'DECIMAL(10,2)', '单价'),
        ('total_amount', 'DECIMAL(10,2)', '总金额'),
        ('received_quantity', 'INT', '已收货数量'),
        ('remark', 'TEXT', '备注'),
    ],
    'purchase_quote': [
        ('request_id', 'INT', '申请 ID'),
        ('supplier_id', 'INT', '供应商 ID'),
        ('quotation_number', 'VARCHAR(50)', '报价单号'),
        ('unit_price', 'DECIMAL(10,2)', '单价'),
        ('total_amount', 'DECIMAL(10,2)', '总价'),
        ('delivery_days', 'INT', '交货天数'),
        ('valid_until', 'DATE', '有效期至'),
        ('is_selected', 'TINYINT(1)', '是否选中'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'supplier_evaluation': [
        ('supplier_id', 'INT', '供应商 ID'),
        ('evaluation_date', 'DATE', '评估日期'),
        ('quality_score', 'INT', '质量评分'),
        ('delivery_score', 'INT', '交货评分'),
        ('service_score', 'INT', '服务评分'),
        ('price_score', 'INT', '价格评分'),
        ('total_score', 'INT', '总分'),
        ('evaluation_result', 'VARCHAR(20)', '评估结果'),
        ('evaluated_by', 'INT', '评估人 ID'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
    ],
    'tag': [
        ('tag_name', 'VARCHAR(50)', '标签名称'),
        ('tag_type', 'VARCHAR(20)', '标签类型'),
        ('color', 'VARCHAR(20)', '颜色'),
        ('description', 'VARCHAR(200)', '描述'),
        ('is_active', 'TINYINT(1)', '是否启用'),
        ('created_at', 'DATETIME', '创建时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'alert': [
        ('alert_type', 'VARCHAR(20)', '告警类型'),
        ('title', 'VARCHAR(200)', '告警标题'),
        ('message', 'TEXT', '告警内容'),
        ('level', 'VARCHAR(20)', '告警级别'),
        ('status', 'VARCHAR(20)', '状态'),
        ('related_object_id', 'INT', '关联对象 ID'),
        ('related_object_type', 'VARCHAR(20)', '关联对象类型'),
        ('triggered_at', 'DATETIME', '触发时间'),
        ('acknowledged_at', 'DATETIME', '确认时间'),
        ('acknowledged_by', 'INT', '确认人 ID'),
        ('resolved_at', 'DATETIME', '解决时间'),
        ('resolved_by', 'INT', '解决人 ID'),
        ('remark', 'TEXT', '备注'),
        ('created_at', 'DATETIME', '创建时间'),
    ],
    'alert_rule': [
        ('rule_name', 'VARCHAR(100)', '规则名称'),
        ('rule_type', 'VARCHAR(20)', '规则类型'),
        ('condition', 'TEXT', '条件'),
        ('threshold', 'VARCHAR(50)', '阈值'),
        ('alert_level', 'VARCHAR(20)', '告警级别'),
        ('notification_methods', 'VARCHAR(100)', '通知方式'),
        ('is_active', 'TINYINT(1)', '是否启用'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
        ('created_by', 'INT', '创建人 ID'),
    ],
    'notification': [
        ('user_id', 'INT', '用户 ID'),
        ('title', 'VARCHAR(200)', '通知标题'),
        ('message', 'TEXT', '通知内容'),
        ('type', 'VARCHAR(20)', '通知类型'),
        ('level', 'VARCHAR(20)', '通知级别'),
        ('is_read', 'TINYINT(1)', '是否已读'),
        ('related_object_id', 'INT', '关联对象 ID'),
        ('related_object_type', 'VARCHAR(20)', '关联对象类型'),
        ('read_at', 'DATETIME', '阅读时间'),
        ('created_at', 'DATETIME', '创建时间'),
    ],
    'email_config': [
        ('smtp_server', 'VARCHAR(100)', 'SMTP 服务器'),
        ('smtp_port', 'INT', 'SMTP 端口'),
        ('username', 'VARCHAR(100)', '用户名'),
        ('password', 'VARCHAR(200)', '密码'),
        ('sender_email', 'VARCHAR(100)', '发件人邮箱'),
        ('sender_name', 'VARCHAR(100)', '发件人名称'),
        ('use_tls', 'TINYINT(1)', '是否使用 TLS'),
        ('is_active', 'TINYINT(1)', '是否启用'),
        ('created_at', 'DATETIME', '创建时间'),
        ('updated_at', 'DATETIME', '更新时间'),
    ],
    'deletion_log': [
        ('table_name', 'VARCHAR(50)', '表名'),
        ('record_id', 'INT', '记录 ID'),
        ('record_data', 'TEXT', '记录数据'),
        ('deleted_by', 'INT', '删除人 ID'),
        ('deleted_at', 'DATETIME', '删除时间'),
        ('reason', 'TEXT', '删除原因'),
        ('ip_address', 'VARCHAR(50)', 'IP 地址'),
        ('can_restore', 'TINYINT(1)', '是否可恢复'),
        ('restored', 'TINYINT(1)', '是否已恢复'),
        ('restored_at', 'DATETIME', '恢复时间'),
        ('restored_by', 'INT', '恢复人 ID'),
    ],
    'system_log': [
        ('log_type', 'VARCHAR(20)', '日志类型'),
        ('action', 'VARCHAR(100)', '操作'),
        ('user_id', 'INT', '用户 ID'),
        ('username', 'VARCHAR(50)', '用户名'),
        ('ip_address', 'VARCHAR(50)', 'IP 地址'),
        ('user_agent', 'VARCHAR(500)', 'User-Agent'),
        ('request_method', 'VARCHAR(10)', '请求方法'),
        ('request_url', 'VARCHAR(500)', '请求 URL'),
        ('request_data', 'TEXT', '请求数据'),
        ('response_status', 'INT', '响应状态'),
        ('response_message', 'TEXT', '响应消息'),
        ('created_at', 'DATETIME', '创建时间'),
    ],
}


def fix_all_tables():
    """修复所有数据库表结构"""
    
    # 连接数据库
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4'
    )
    
    try:
        cursor = connection.cursor()
        
        print("=" * 60)
        print("开始全面检查和修复数据库表结构...")
        print("=" * 60)
        
        total_added = 0
        
        for table_name, fields in TABLE_FIELDS.items():
            print(f"\n检查表：{table_name}")
            
            for field_name, field_type, field_comment in fields:
                # 检查字段是否存在
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = %s 
                    AND COLUMN_NAME = %s
                """, (MYSQL_DATABASE, table_name, field_name))
                
                if cursor.fetchone()[0] == 0:
                    # 添加缺失的字段
                    sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{field_name}` {field_type} COMMENT '{field_comment}'"
                    
                    # 特殊处理：如果是第一个字段，添加位置不同
                    if field_name == 'id':
                        sql += " FIRST"
                    else:
                        sql += f" AFTER `{fields[fields.index((field_name, field_type, field_comment)) - 1][0]}`"
                    
                    try:
                        cursor.execute(sql)
                        print(f"  ✓ 添加 {table_name}.{field_name} 字段成功")
                        total_added += 1
                    except Exception as e:
                        print(f"  ✗ 添加 {table_name}.{field_name} 失败：{e}")
                else:
                    print(f"  ✓ {table_name}.{field_name} 字段已存在")
        
        connection.commit()
        
        print("\n" + "=" * 60)
        print(f"数据库表结构修复完成！共添加 {total_added} 个字段")
        print("=" * 60)
        
        cursor.close()
        
    except Exception as e:
        print(f"✗ 错误：{e}")
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == '__main__':
    print("=" * 60)
    print("开始全面检查和修复数据库表结构...")
    print("=" * 60)
    fix_all_tables()
    print("\n完成！")
