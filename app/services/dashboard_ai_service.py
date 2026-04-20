"""
仪表盘 AI 服务
集成百度千帆 AI 提供智能洞察功能
"""

import json
from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models.spare_part import SparePart
from app.models.equipment import Equipment
from app.models.transaction import Transaction
from app.models.maintenance import MaintenanceOrder
from app.models.kpi import AIAnalysisHistory
from app.services.baidu_qianfan_service import get_qianfan_service
from sqlalchemy import func


class DashboardAIService:
    """仪表盘 AI 分析服务"""

    def __init__(self):
        self.qianfan_service = get_qianfan_service()

    def get_inventory_health_score(self):
        """
        获取库存健康评分

        Returns:
            dict: 包含健康评分、评估、问题、建议的字典
        """
        try:
            # 获取库存数据
            parts = SparePart.query.all()
            inventory_data = []

            for part in parts[:30]:  # 限制数量避免 token 超限
                inventory_data.append({
                    'part_id': part.id,
                    'part_code': part.part_code or '',
                    'part_name': part.name or '',
                    'quantity': part.current_stock or 0,
                    'stock_status': part.stock_status or 'normal',
                    'min_stock': part.min_stock or 0,
                    'max_stock': part.max_stock or 0
                })

            # 首先尝试用简单算法计算（避免AI调用失败）
            simple_result = self._calculate_simple_health_score(parts)

            # 尝试调用AI分析
            if self.qianfan_service.client:
                try:
                    result = self.qianfan_service.analyze_inventory_health(inventory_data)

                    if result['success']:
                        # 保存分析历史
                        self._save_analysis_history('health', json.dumps(result.get('analysis', {})))
                        return {
                            'success': True,
                            'health_score': result['analysis'].get('health_score', simple_result['health_score']),
                            'summary': result['analysis'].get('summary', simple_result['summary']),
                            'issues': result['analysis'].get('issues', []),
                            'recommendations': result['analysis'].get('recommendations', []),
                            'method': 'ai'
                        }
                except Exception as e:
                    current_app.logger.warning(f'AI分析失败，使用简单算法: {str(e)}')

            # AI不可用，返回简单计算结果
            return {
                'success': True,
                'health_score': simple_result['health_score'],
                'summary': simple_result['summary'],
                'issues': simple_result['issues'],
                'recommendations': simple_result['recommendations'],
                'method': 'simple'
            }

        except Exception as e:
            current_app.logger.error(f'获取库存健康评分异常: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'health_score': 0,
                'summary': '分析失败',
                'issues': [],
                'recommendations': []
            }

    def _calculate_simple_health_score(self, parts):
        """
        简单算法计算库存健康评分（备用方案）

        Args:
            parts: 备件列表

        Returns:
            dict: 计算结果
        """
        total = len(parts)
        normal = 0
        low = 0
        out = 0
        overstocked = 0
        issues = []
        recommendations = []

        for part in parts:
            status = part.stock_status or 'normal'
            if status == 'normal':
                normal += 1
            elif status == 'low':
                low += 1
                issues.append({
                    'part_code': part.part_code or '',
                    'issue': '库存不足',
                    'suggestion': f'建议补货至{part.min_stock}个以上'
                })
            elif status == 'out':
                out += 1
                issues.append({
                    'part_code': part.part_code or '',
                    'issue': '已缺货',
                    'suggestion': '紧急补货'
                })
            elif status == 'overstocked':
                overstocked += 1
                issues.append({
                    'part_code': part.part_code or '',
                    'issue': '超储',
                    'suggestion': '考虑促销或调整采购计划'
                })

        # 计算健康评分
        if total > 0:
            health_score = int((normal / total) * 100)
        else:
            health_score = 50

        # 生成建议
        if low > 0:
            recommendations.append(f'需要补货{low}种低库存备件')
        if out > 0:
            recommendations.append(f'紧急处理{out}种缺货备件')
        if overstocked > 0:
            recommendations.append(f'清理{overstocked}种超储备件')
        if low == 0 and out == 0 and overstocked == 0:
            recommendations.append('库存状况良好，继续保持')

        summary = self._generate_simple_summary(normal, low, out, overstocked, total)

        return {
            'health_score': health_score,
            'summary': summary,
            'issues': issues[:10],  # 限制显示10个问题
            'recommendations': recommendations
        }

    def _generate_simple_summary(self, normal, low, out, overstocked, total):
        """生成简单评估文本"""
        if total == 0:
            return '暂无库存数据'

        normal_ratio = (normal / total) * 100
        if normal_ratio >= 90:
            return f'库存状况优秀，{normal_ratio:.1f}%备件库存正常'
        elif normal_ratio >= 70:
            return f'库存状况良好，{normal_ratio:.1f}%备件库存正常，有{low + out}种需要注意'
        elif normal_ratio >= 50:
            return f'库存状况一般，{normal_ratio:.1f}%备件库存正常，有{low + out}种需要处理'
        else:
            return f'库存状况需要关注，仅{normal_ratio:.1f}%备件库存正常'

    def get_anomaly_report(self):
        """
        获取异常检测报告

        Returns:
            dict: 异常报告
        """
        try:
            # 获取最近的交易记录
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            recent_transactions = Transaction.query.filter(
                Transaction.created_at >= start_date
            ).order_by(Transaction.created_at.desc()).limit(50).all()

            # 首先用简单算法检测
            simple_anomalies = self._detect_simple_anomalies(recent_transactions)

            # 尝试调用AI分析
            if self.qianfan_service.client and len(recent_transactions) > 0:
                try:
                    # 格式化数据用于AI分析
                    log_data = []
                    for tx in recent_transactions:
                        log_data.append({
                            'id': tx.id,
                            'tx_code': tx.tx_code or '',
                            'tx_type': tx.tx_type or '',
                            'total_qty': float(tx.total_qty) if tx.total_qty else 0,
                            'created_at': tx.created_at.isoformat() if tx.created_at else ''
                        })

                    result = self.qianfan_service.detect_anomalies(log_data)

                    if result['success']:
                        self._save_analysis_history('anomaly', json.dumps(result.get('anomalies', {})))
                        return {
                            'success': True,
                            'anomalies': result.get('anomalies', simple_anomalies),
                            'method': 'ai'
                        }
                except Exception as e:
                    current_app.logger.warning(f'AI异常检测失败，使用简单算法: {str(e)}')

            # 返回简单检测结果
            return {
                'success': True,
                'anomalies': simple_anomalies,
                'method': 'simple'
            }

        except Exception as e:
            current_app.logger.error(f'获取异常报告异常: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'anomalies': []
            }

    def _detect_simple_anomalies(self, transactions):
        """简单算法检测异常"""
        anomalies = []

        if not transactions:
            return anomalies

        # 计算平均交易量
        quantities = [float(tx.total_qty) for tx in transactions if tx.total_qty]
        if len(quantities) > 0:
            avg_qty = sum(quantities) / len(quantities)
            threshold = avg_qty * 3  # 超过平均值3倍认为异常

            for tx in transactions:
                if tx.total_qty and float(tx.total_qty) > threshold:
                    anomalies.append({
                        'type': '大额出入库',
                        'description': f'交易 {tx.tx_code or tx.id} 数量异常偏大',
                        'severity': 'medium'
                    })

        return anomalies[:10]

    def get_intelligent_insights(self):
        """
        获取综合智能洞察

        Returns:
            dict: 包含健康评分、异常、建议、预测的综合洞察
        """
        health_result = self.get_inventory_health_score()
        anomaly_result = self.get_anomaly_report()
        predictions = self._get_simple_predictions()

        insights = {
            'inventory_health': health_result,
            'anomalies': anomaly_result,
            'recommendations': self._generate_recommendations(health_result, anomaly_result),
            'predictions': predictions,
            'generated_at': datetime.now().isoformat()
        }

        return insights

    def _get_simple_predictions(self):
        """简单预测（备用方案）"""
        return {
            'next_7_days_demand': '根据历史趋势，预计未来7天需求稳定',
            'suggested_reorder': []
        }

    def _generate_recommendations(self, health_result, anomaly_result):
        """根据分析结果生成建议"""
        recommendations = []

        if health_result.get('health_score', 0) < 70:
            recommendations.append({
                'priority': 'high',
                'content': '库存健康状况需要关注，建议及时处理问题备件',
                'action': '查看库存预警'
            })

        anomalies = anomaly_result.get('anomalies', [])
        if len(anomalies) > 0:
            recommendations.append({
                'priority': 'high',
                'content': f'发现{len(anomalies)}个异常，建议核实处理',
                'action': '查看异常报告'
            })

        return recommendations

    def _save_analysis_history(self, analysis_type, result):
        """保存分析历史"""
        try:
            history = AIAnalysisHistory(
                analysis_type=analysis_type,
                analysis_result=result,
                confidence_score=0.85,
                created_at=datetime.utcnow()
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'保存分析历史失败: {str(e)}')
            db.session.rollback()

    def refresh_analysis(self):
        """
        刷新分析结果

        Returns:
            dict: 新的分析结果
        """
        return self.get_intelligent_insights()

    def get_demand_forecast(self):
        """
        获取需求预测分析

        Returns:
            dict: 需求预测结果
        """
        try:
            from datetime import datetime, timedelta

            # 获取历史数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            transactions = Transaction.query.filter(
                Transaction.tx_type == 'outbound',
                Transaction.created_at >= start_date
            ).all()

            # 简单的趋势分析
            total_outbound = sum(float(tx.total_qty or 0) for tx in transactions)
            avg_daily = total_outbound / 90 if transactions else 0

            # 预测未来需求
            forecast = {
                'next_7_days': round(avg_daily * 7 * 1.05, 2),  # 预计增长5%
                'next_30_days': round(avg_daily * 30 * 1.03, 2),  # 预计增长3%
                'historical_avg': round(avg_daily, 2),
                'trend': 'stable' if 0.95 <= (avg_daily * 30 / max(total_outbound, 1)) <= 1.05 else 'growing'
            }

            # 推荐补货的备件
            low_stock_parts = SparePart.query.filter(
                SparePart.stock_status.in_(['low', 'out'])
            ).limit(5).all()

            recommendations = [{
                'part_code': part.part_code,
                'part_name': part.name,
                'current_stock': part.current_stock,
                'min_stock': part.min_stock,
                'suggested_order': max(part.min_stock * 2 - part.current_stock, part.min_stock)
            } for part in low_stock_parts]

            return {
                'success': True,
                'forecast': forecast,
                'recommendations': recommendations
            }
        except Exception as e:
            current_app.logger.error(f'需求预测分析异常: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'forecast': {},
                'recommendations': []
            }

    def get_abc_analysis(self):
        """
        获取ABC分类分析

        Returns:
            dict: ABC分析结果
        """
        try:
            # 计算所有备件的库存价值
            parts = SparePart.query.all()
            part_values = []

            for part in parts:
                value = float(part.current_stock or 0) * float(part.unit_price or 0)
                part_values.append({
                    'part': part,
                    'value': value
                })

            # 按价值降序排序
            part_values.sort(key=lambda x: x['value'], reverse=True)

            # 计算总价值
            total_value = sum(pv['value'] for pv in part_values)

            # ABC分类
            abc_result = {
                'A': {'items': [], 'value': 0, 'percentage': 0, 'count': 0},
                'B': {'items': [], 'value': 0, 'percentage': 0, 'count': 0},
                'C': {'items': [], 'value': 0, 'percentage': 0, 'count': 0}
            }

            cumulative_percent = 0
            for pv in part_values:
                if total_value > 0:
                    item_percent = (pv['value'] / total_value) * 100
                else:
                    item_percent = 0

                if cumulative_percent < 80:
                    category = 'A'
                elif cumulative_percent < 95:
                    category = 'B'
                else:
                    category = 'C'

                abc_result[category]['items'].append({
                    'part_code': pv['part'].part_code,
                    'part_name': pv['part'].name,
                    'value': round(pv['value'], 2)
                })
                abc_result[category]['value'] += pv['value']
                abc_result[category]['count'] += 1

                cumulative_percent += item_percent

            # 计算各分类的百分比
            for category in abc_result:
                if total_value > 0:
                    abc_result[category]['percentage'] = round(
                        (abc_result[category]['value'] / total_value) * 100, 2
                    )
                abc_result[category]['value'] = round(abc_result[category]['value'], 2)
                # 只保留前5个项目
                abc_result[category]['items'] = abc_result[category]['items'][:5]

            return {
                'success': True,
                'total_value': round(total_value, 2),
                'abc_analysis': abc_result
            }
        except Exception as e:
            current_app.logger.error(f'ABC分析异常: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'total_value': 0,
                'abc_analysis': {}
            }

    def get_performance_insights(self):
        """
        获取综合绩效洞察

        Returns:
            dict: 绩效洞察
        """
        try:
            from datetime import datetime, timedelta

            # 库存健康
            health = self._calculate_simple_health_score(SparePart.query.all())

            # 设备效率
            total_equipment = Equipment.query.count()
            running = Equipment.query.filter_by(status='running').count()
            availability = round((running / total_equipment * 100), 2) if total_equipment > 0 else 0

            # 订单完成率
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            total_orders = MaintenanceOrder.query.filter(
                MaintenanceOrder.created_at >= start_date
            ).count()
            completed = MaintenanceOrder.query.filter(
                MaintenanceOrder.status == 'completed',
                MaintenanceOrder.created_at >= start_date
            ).count()
            completion_rate = round((completed / total_orders * 100), 2) if total_orders > 0 else 0

            # 综合评分
            overall_score = round((health['health_score'] + availability + completion_rate) / 3, 1)

            insights = []

            if overall_score >= 80:
                insights.append({
                    'type': 'success',
                    'title': '运营状况优秀',
                    'message': '整体运营效率处于良好水平，请继续保持。'
                })
            elif overall_score >= 60:
                insights.append({
                    'type': 'warning',
                    'title': '需要关注',
                    'message': '部分指标需要改进，建议查看详细分析。'
                })
            else:
                insights.append({
                    'type': 'danger',
                    'title': '需要立即改进',
                    'message': '运营状况需要重点关注和改进。'
                })

            if health['health_score'] < 70:
                insights.append({
                    'type': 'warning',
                    'title': '库存健康需要改进',
                    'message': f'当前库存健康评分{health["health_score"]}分，建议优化库存结构。'
                })

            if availability < 85:
                insights.append({
                    'type': 'warning',
                    'title': '设备可用性偏低',
                    'message': f'当前设备可用率{availability}%，建议优化维护计划。'
                })

            return {
                'success': True,
                'overall_score': overall_score,
                'metrics': {
                    'inventory_health': health['health_score'],
                    'equipment_availability': availability,
                    'order_completion': completion_rate
                },
                'insights': insights
            }
        except Exception as e:
            current_app.logger.error(f'绩效洞察分析异常: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }


# 全局服务实例
_dashboard_ai_service = None


def get_dashboard_ai_service():
    """获取仪表盘AI服务实例"""
    global _dashboard_ai_service
    if _dashboard_ai_service is None:
        _dashboard_ai_service = DashboardAIService()
    return _dashboard_ai_service
