"""
定时任务调度器
使用 APScheduler 实现定时任务调度
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
from app import db
from app.services.warning_service import WarningService

logger = logging.getLogger(__name__)

# 创建调度器
scheduler = BackgroundScheduler()


def check_inventory_warnings():
    """
    定时检查库存预警
    """
    logger.info("开始执行库存预警检查...")
    try:
        warnings = WarningService.check_all_rules()
        logger.info(f"库存预警检查完成，生成 {len(warnings)} 条预警")
    except Exception as e:
        logger.error(f"库存预警检查失败：{str(e)}")
        db.session.rollback()


def check_expiry_warnings():
    """
    定时检查有效期预警
    """
    logger.info("开始执行有效期预警检查...")
    try:
        # TODO: 实现有效期预警检查
        logger.info("有效期预警检查完成")
    except Exception as e:
        logger.error(f"有效期预警检查失败：{str(e)}")
        db.session.rollback()


def check_stock_age_warnings():
    """
    定时检查库龄预警
    """
    logger.info("开始执行库龄预警检查...")
    try:
        # TODO: 实现库龄预警检查
        logger.info("库龄预警检查完成")
    except Exception as e:
        logger.error(f"库龄预警检查失败：{str(e)}")
        db.session.rollback()


def init_scheduler(app=None):
    """
    初始化调度器
    
    Args:
        app: Flask 应用实例
    """
    if app:
        # 在 Flask 应用上下文中执行任务
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
    
    # 启动调度器
    if not scheduler.running:
        scheduler.start()
        logger.info("定时任务调度器已启动")
    
    return scheduler


def get_scheduler():
    """
    获取调度器实例
    
    Returns:
        调度器实例
    """
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
