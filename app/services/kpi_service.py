"""
KPI管理服务
提供KPI配置、历史记录、计算等功能
"""

from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models.kpi import KPIConfig, KPIHistory
from app.models.spare_part import SparePart
from app.models.equipment import Equipment
from app.models.transaction import Transaction
from app.models.maintenance import MaintenanceOrder
from sqlalchemy import func


class KPIService:
    """KPI管理服务"""

    def __init__(self):
        pass

    def get_default_kpis(self):
        """获取默认的KPI列表"""
        return [
            {
                'name': '备件种类',
                'code': 'spare_parts_count',
                'description': '系统中的备件种类数量',
                'target_value': 500,
                'unit': '种',
                'check_frequency': 'daily'
            },
            {
                'name': '设备总数',
                'code': 'equipment_count',
                'description': '系统中的设备总数',
                'target_value': 100,
                'unit': '台',
                'check_frequency': 'daily'
            },
            {
                'name': '设备运行率',
                'code': 'equipment_running_rate',
                'description': '正常运行的设备比例',
                'target_value': 90,
                'unit': '%',
                'check_frequency': 'daily'
            },
            {
                'name': '库存周转率',
                'code': 'inventory_turnover',
                'description': '月度库存周转率',
                'target_value': 4,
                'unit': '次/月',
                'check_frequency': 'monthly'
            },
            {
                'name': '工单及时完成率',
                'code': 'order_completion_rate',
                'description': '维护工单及时完成的比例',
                'target_value': 95,
                'unit': '%',
                'check_frequency': 'weekly'
            }
        ]

    def init_default_kpis(self):
        """初始化默认KPI配置"""
        try:
            default_kpis = self.get_default_kpis()
            for kpi_data in default_kpis:
                existing = KPIConfig.query.filter_by(code=kpi_data['code']).first()
                if not existing:
                    kpi = KPIConfig(
                        name=kpi_data['name'],
                        code=kpi_data['code'],
                        description=kpi_data['description'],
                        target_value=kpi_data['target_value'],
                        unit=kpi_data['unit'],
                        check_frequency=kpi_data['check_frequency'],
                        is_active=True
                    )
                    db.session.add(kpi)

            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f'初始化默认KPI失败: {str(e)}')
            db.session.rollback()
            return False

    def get_active_kpis(self):
        """获取启用的KPI配置列表"""
        return KPIConfig.query.filter_by(is_active=True).all()

    def get_kpi_summary(self, period='daily'):
        """获取KPI汇总数据"""
        kpis = self.get_active_kpis()
        summary = []

        for kpi in kpis:
            actual_value = self._calculate_kpi_value(kpi.code)
            target_value = kpi.target_value or 0
            trend = self._calculate_trend(kpi.code, period)

            # 计算完成率
            completion_rate = 0
            if target_value > 0:
                if kpi.code == 'equipment_running_rate' or kpi.code == 'order_completion_rate':
                    # 百分比指标，直接比较
                    completion_rate = (actual_value / target_value) * 100 if target_value > 0 else 0
                else:
                    completion_rate = (actual_value / target_value) * 100 if target_value > 0 else 0

            # 确定状态
            status = 'normal'
            if kpi.warning_threshold and actual_value < kpi.warning_threshold:
                status = 'warning'
            if kpi.critical_threshold and actual_value < kpi.critical_threshold:
                status = 'critical'

            summary.append({
                'id': kpi.id,
                'name': kpi.name,
                'code': kpi.code,
                'actual_value': actual_value,
                'target_value': target_value,
                'unit': kpi.unit,
                'completion_rate': round(completion_rate, 1),
                'trend': trend,
                'status': status
            })

        return summary

    def _calculate_kpi_value(self, code):
        """计算KPI实际值"""
        try:
            if code == 'spare_parts_count':
                return SparePart.query.count()

            elif code == 'equipment_count':
                return Equipment.query.count()

            elif code == 'equipment_running_rate':
                total = Equipment.query.count()
                running = Equipment.query.filter_by(status='running').count()
                return round((running / total) * 100, 1) if total > 0 else 0

            elif code == 'inventory_turnover':
                # 简化计算：用月度出库数量
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                outbound = Transaction.query.filter(
                    Transaction.tx_type == 'outbound',
                    Transaction.created_at >= start_date
                ).count()
                return outbound  # 简化为次数

            elif code == 'order_completion_rate':
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                total = MaintenanceOrder.query.filter(
                    MaintenanceOrder.created_at >= start_date
                ).count()
                completed = MaintenanceOrder.query.filter(
                    MaintenanceOrder.status == 'completed',
                    MaintenanceOrder.created_at >= start_date
                ).count()
                return round((completed / total) * 100, 1) if total > 0 else 0

            return 0
        except Exception as e:
            current_app.logger.error(f'计算KPI值失败: {code} - {str(e)}')
            return 0

    def _calculate_trend(self, code, period):
        """计算趋势"""
        # 简化处理：返回 0 表示持平
        return 0

    def get_kpi_history(self, kpi_id, days=30):
        """获取KPI历史数据"""
        kpi = KPIConfig.query.get(kpi_id)
        if not kpi:
            return []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        history = KPIHistory.query.filter(
            KPIHistory.kpi_id == kpi_id,
            KPIHistory.created_at >= start_date
        ).order_by(KPIHistory.created_at.asc()).all()

        return [h.to_dict() for h in history]

    def record_kpi_snapshot(self):
        """记录KPI快照"""
        try:
            kpis = self.get_active_kpis()
            now = datetime.now()
            today = now.date()

            for kpi in kpis:
                # 检查今天是否已经记录过
                existing = KPIHistory.query.filter(
                    KPIHistory.kpi_id == kpi.id,
                    func.date(KPIHistory.created_at) == today
                ).first()

                if existing:
                    continue

                value = self._calculate_kpi_value(kpi.code)
                history = KPIHistory(
                    kpi_id=kpi.id,
                    period='daily',
                    period_start=datetime.combine(today, datetime.min.time()),
                    period_end=datetime.combine(today, datetime.max.time()),
                    actual_value=value,
                    target_value=kpi.target_value,
                    created_at=now
                )
                db.session.add(history)

            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f'记录KPI快照失败: {str(e)}')
            db.session.rollback()
            return False

    def get_leaderboard(self, leaderboard_type='equipment'):
        """获取排行榜数据"""
        if leaderboard_type == 'equipment':
            # 设备运行状态排行
            status_count = {
                'running': Equipment.query.filter_by(status='running').count(),
                'stopped': Equipment.query.filter_by(status='stopped').count(),
                'maintenance': Equipment.query.filter_by(status='maintenance').count()
            }
            return status_count
        elif leaderboard_type == 'warehouse':
            # 仓库利用率排行（模拟）
            return {
                '仓库1': 85,
                '仓库2': 78,
                '仓库3': 92
            }
        return {}


# 全局服务实例
_kpi_service = None


def get_kpi_service():
    """获取KPI服务实例"""
    global _kpi_service
    if _kpi_service is None:
        _kpi_service = KPIService()
        # 自动初始化默认KPI
        _kpi_service.init_default_kpis()
    return _kpi_service
