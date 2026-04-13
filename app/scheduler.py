"""
定时任务调度器
使用 APScheduler 实现定时任务调度
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# 创建调度器
scheduler = BackgroundScheduler()


def check_inventory_warnings():
    """定时检查库存预警"""
    logger.info("开始执行库存预警检查...")
    try:
        from app.services.warning_service import WarningService
        warnings = WarningService.check_all_rules()
        logger.info(f"库存预警检查完成，生成 {len(warnings)} 条预警")
    except Exception as e:
        logger.error(f"库存预警检查失败：{str(e)}")
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            pass


def check_expiry_warnings():
    """定时检查有效期预警，调用 ExpiryWarningService 并将结果写入 Alert 表"""
    logger.info("开始执行有效期预警检查...")
    try:
        from app.extensions import db
        from app.services.warehouse_v3.expiry_warning_service import ExpiryWarningService
        from app.models.system import Alert

        warnings = ExpiryWarningService.get_expiry_warnings(days_threshold=30)
        expired = ExpiryWarningService.get_expired_inventory()
        created_count = 0
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        level_map = {'red': 'critical', 'orange': 'high', 'yellow': 'medium'}

        for item in warnings:
            days = item.get('days_remaining', 0)
            alert_level = level_map.get(item.get('warning_level', 'yellow'), 'medium')
            existing = Alert.query.filter(
                Alert.alert_type == 'expiry_warning',
                Alert.related_object_id == item.get('inventory_id'),
                Alert.related_object_type == 'inventory',
                Alert.triggered_at >= today_start
            ).first()
            if not existing:
                alert = Alert(
                    alert_type='expiry_warning',
                    title=f"近效期预警：{item.get('part_name', '')}",
                    message=(
                        f"备件【{item.get('part_code', '')} {item.get('part_name', '')}】"
                        f"（批次：{item.get('batch_no', 'N/A')}）"
                        f"将在 {days} 天后过期（{item.get('expiry_date', '')}），"
                        f"库存数量：{item.get('quantity', 0)} {item.get('unit', '')}，"
                        f"仓库：{item.get('warehouse_name', 'N/A')}"
                    ),
                    level=alert_level,
                    status='active',
                    related_object_id=item.get('inventory_id'),
                    related_object_type='inventory'
                )
                db.session.add(alert)
                created_count += 1

        for item in expired:
            existing = Alert.query.filter(
                Alert.alert_type == 'expired',
                Alert.related_object_id == item.get('inventory_id'),
                Alert.related_object_type == 'inventory',
                Alert.triggered_at >= today_start
            ).first()
            if not existing:
                alert = Alert(
                    alert_type='expired',
                    title=f"已过期告警：{item.get('part_name', '')}",
                    message=(
                        f"备件【{item.get('part_code', '')} {item.get('part_name', '')}】"
                        f"（批次：{item.get('batch_no', 'N/A')}）"
                        f"已过期 {item.get('days_overdue', 0)} 天（{item.get('expiry_date', '')}），"
                        f"库存数量：{item.get('quantity', 0)} {item.get('unit', '')}，"
                        f"仓库：{item.get('warehouse_name', 'N/A')}"
                    ),
                    level='critical',
                    status='active',
                    related_object_id=item.get('inventory_id'),
                    related_object_type='inventory'
                )
                db.session.add(alert)
                created_count += 1

        db.session.commit()
        logger.info(f"有效期预警检查完成，新增 {created_count} 条预警告警")
    except Exception as e:
        logger.error(f"有效期预警检查失败：{str(e)}")
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            pass


def check_stock_age_warnings():
    """定时检查库龄预警，查询入库超过 365 天的库存记录并写入 Alert 表"""
    logger.info("开始执行库龄预警检查...")
    try:
        from app.extensions import db
        from app.models.inventory import InventoryRecord
        from app.models.system import Alert

        age_threshold_days = 365
        cutoff_date = datetime.now() - timedelta(days=age_threshold_days)
        old_records = InventoryRecord.query.filter(
            InventoryRecord.created_at <= cutoff_date,
            InventoryRecord.quantity > 0
        ).all()

        created_count = 0
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for record in old_records:
            stock_age = (datetime.now() - record.created_at).days
            existing = Alert.query.filter(
                Alert.alert_type == 'stock_age_warning',
                Alert.related_object_id == record.id,
                Alert.related_object_type == 'inventory_record',
                Alert.triggered_at >= today_start
            ).first()
            if not existing:
                part_name = record.spare_part.name if record.spare_part else str(record.spare_part_id)
                part_code = record.spare_part.code if record.spare_part else ''
                alert = Alert(
                    alert_type='stock_age_warning',
                    title=f"库龄超期预警：{part_name}",
                    message=(
                        f"备件【{part_code} {part_name}】库龄已达 {stock_age} 天"
                        f"（入库时间：{record.created_at.strftime('%Y-%m-%d')}），"
                        f"当前库存数量：{record.quantity}，"
                        f"建议及时处置或盘点。"
                    ),
                    level='medium',
                    status='active',
                    related_object_id=record.id,
                    related_object_type='inventory_record'
                )
                db.session.add(alert)
                created_count += 1

        db.session.commit()
        logger.info(f"库龄预警检查完成，新增 {created_count} 条预警告警")
    except Exception as e:
        logger.error(f"库龄预警检查失败：{str(e)}")
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            pass


def init_scheduler(app=None):
    """
    初始化调度器

    Args:
        app: Flask 应用实例
    """
    if app:
        @scheduler.scheduled_job('interval', minutes=5, id='check_inventory_warnings')
        def wrapped_check_inventory():
            with app.app_context():
                check_inventory_warnings()

        @scheduler.scheduled_job('cron', hour=2, minute=0, id='check_expiry_warnings')
        def wrapped_check_expiry():
            with app.app_context():
                check_expiry_warnings()

        @scheduler.scheduled_job('cron', hour=3, minute=0, id='check_stock_age')
        def wrapped_check_stock_age():
            with app.app_context():
                check_stock_age_warnings()

    if not scheduler.running:
        scheduler.start()
        logger.info("定时任务调度器已启动")

    return scheduler


def get_scheduler():
    """获取调度器实例"""
    return scheduler


def add_job(func, trigger, job_id=None, **trigger_args):
    """
    添加定时任务

    Args:
        func: 任务函数
        trigger: 触发器类型 ('interval', 'cron', 'date')
        job_id: 任务 ID
        **trigger_args: 触发器参数
    """
    if trigger == 'interval':
        scheduler.add_job(func, IntervalTrigger(**trigger_args), id=job_id)
    elif trigger == 'cron':
        scheduler.add_job(func, CronTrigger(**trigger_args), id=job_id)
    elif trigger == 'date':
        scheduler.add_job(func, 'date', run_date=trigger_args.get('run_date'), id=job_id)

    logger.info(f"添加定时任务：{job_id}")


def remove_job(job_id):
    """
    移除定时任务

    Args:
        job_id: 任务 ID
    """
    try:
        scheduler.remove_job(job_id)
        logger.info(f"移除定时任务：{job_id}")
    except Exception as e:
        logger.error(f"移除定时任务失败：{str(e)}")
