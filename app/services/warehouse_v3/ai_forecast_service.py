from app import db
from app.models.warehouse_v3.ai_forecast import DemandForecast, ReorderRecommendation, InventoryOptimization
from app.models.warehouse_v3.inventory import InventoryV3
from app.models.warehouse_v3.outbound import OutboundOrderV3, OutboundOrderItemV3
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from decimal import Decimal
import math


class DemandForecastService:
    """需求预测服务"""
    
    @staticmethod
    def calculate_moving_average(part_id, warehouse_id=None, periods=30):
        """
        计算移动平均需求
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :param periods: 周期（天）
        :return: 平均需求
        """
        start_date = datetime.now().date() - timedelta(days=periods)
        
        # 统计出库数量
        query = db.session.query(
            func.sum(OutboundOrderItemV3.quantity)
        ).join(
            OutboundOrderV3, OutboundOrderV3.id == OutboundOrderItemV3.outbound_order_id
        ).filter(
            and_(
                OutboundOrderItemV3.part_id == part_id,
                OutboundOrderV3.status == 'completed',
                OutboundOrderV3.created_at >= start_date
            )
        )
        
        if warehouse_id:
            query = query.filter(OutboundOrderV3.warehouse_id == warehouse_id)
        
        total_demand = query.scalar() or 0
        
        # 计算日均需求
        avg_daily_demand = total_demand / periods if periods > 0 else 0
        
        return round(avg_daily_demand, 4)
    
    @staticmethod
    def calculate_trend(part_id, warehouse_id=None, periods=60):
        """
        计算需求趋势
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :param periods: 周期（天）
        :return: 趋势类型和增长率
        """
        half_periods = periods // 2
        midpoint = datetime.now().date() - timedelta(days=half_periods)
        
        # 前半段需求
        query1 = db.session.query(
            func.sum(OutboundOrderItemV3.quantity)
        ).join(
            OutboundOrderV3, OutboundOrderV3.id == OutboundOrderItemV3.outbound_order_id
        ).filter(
            and_(
                OutboundOrderItemV3.part_id == part_id,
                OutboundOrderV3.status == 'completed',
                OutboundOrderV3.created_at < midpoint,
                OutboundOrderV3.created_at >= midpoint - timedelta(days=half_periods)
            )
        )
        
        if warehouse_id:
            query1 = query1.filter(OutboundOrderV3.warehouse_id == warehouse_id)
        
        first_half = query1.scalar() or 0
        
        # 后半段需求
        query2 = db.session.query(
            func.sum(OutboundOrderItemV3.quantity)
        ).join(
            OutboundOrderV3, OutboundOrderV3.id == OutboundOrderItemV3.outbound_order_id
        ).filter(
            and_(
                OutboundOrderItemV3.part_id == part_id,
                OutboundOrderV3.status == 'completed',
                OutboundOrderV3.created_at >= midpoint
            )
        )
        
        if warehouse_id:
            query2 = query2.filter(OutboundOrderV3.warehouse_id == warehouse_id)
        
        second_half = query2.scalar() or 0
        
        # 计算增长率
        if first_half > 0:
            growth_rate = (second_half - first_half) / first_half
        else:
            growth_rate = 0 if second_half == 0 else 1
        
        # 判断趋势
        if growth_rate > 0.1:
            trend = 'INCREASING'
        elif growth_rate < -0.1:
            trend = 'DECREASING'
        else:
            trend = 'STABLE'
        
        return trend, round(growth_rate, 4)
    
    @staticmethod
    def calculate_seasonality(part_id, warehouse_id=None):
        """
        计算季节性指数（简化版）
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :return: 季节性指数
        """
        current_month = datetime.now().month
        
        # 获取过去 12 个月的数据
        one_year_ago = datetime.now().date() - timedelta(days=365)
        
        # 当前月份的历史平均
        query = db.session.query(
            func.avg(OutboundOrderItemV3.quantity)
        ).join(
            OutboundOrderV3, OutboundOrderV3.id == OutboundOrderItemV3.outbound_order_id
        ).filter(
            and_(
                OutboundOrderItemV3.part_id == part_id,
                OutboundOrderV3.status == 'completed',
                OutboundOrderV3.created_at >= one_year_ago,
                func.extract('month', OutboundOrderV3.created_at) == current_month
            )
        )
        
        if warehouse_id:
            query = query.filter(OutboundOrderV3.warehouse_id == warehouse_id)
        
        current_month_avg = query.scalar() or 0
        
        # 全年平均
        query2 = db.session.query(
            func.avg(OutboundOrderItemV3.quantity)
        ).join(
            OutboundOrderV3, OutboundOrderV3.id == OutboundOrderItemV3.outbound_order_id
        ).filter(
            and_(
                OutboundOrderItemV3.part_id == part_id,
                OutboundOrderV3.status == 'completed',
                OutboundOrderV3.created_at >= one_year_ago
            )
        )
        
        if warehouse_id:
            query2 = query2.filter(OutboundOrderV3.warehouse_id == warehouse_id)
        
        yearly_avg = query2.scalar() or 0
        
        # 计算季节性指数
        if yearly_avg > 0:
            seasonality_index = current_month_avg / yearly_avg
        else:
            seasonality_index = 1.0
        
        return round(seasonality_index, 2)
    
    @staticmethod
    def generate_forecast(part_id, warehouse_id, forecast_days=30):
        """
        生成需求预测
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :param forecast_days: 预测天数
        :return: 预测结果
        """
        # 计算基础指标
        avg_daily_demand = DemandForecastService.calculate_moving_average(part_id, warehouse_id)
        trend, growth_rate = DemandForecastService.calculate_trend(part_id, warehouse_id)
        seasonality_index = DemandForecastService.calculate_seasonality(part_id, warehouse_id)
        
        # 预测需求
        base_demand = avg_daily_demand * forecast_days
        
        # 应用趋势和季节性调整
        if trend == 'INCREASING':
            adjusted_demand = base_demand * (1 + growth_rate) * seasonality_index
        elif trend == 'DECREASING':
            adjusted_demand = base_demand * (1 - abs(growth_rate)) * seasonality_index
        else:
            adjusted_demand = base_demand * seasonality_index
        
        # 计算置信度（简化）
        confidence_level = min(95, max(50, 100 - abs(growth_rate) * 100))
        
        forecast_date = datetime.now().date()
        
        # 创建预测记录
        forecast = DemandForecast(
            warehouse_id=warehouse_id,
            part_id=part_id,
            forecast_date=forecast_date,
            forecast_period=forecast_days,
            predicted_demand=Decimal(str(round(adjusted_demand, 2))),
            confidence_level=Decimal(str(round(confidence_level, 2))),
            demand_trend=trend,
            seasonality_index=Decimal(str(seasonality_index)),
            model_type='MOVING_AVERAGE_WITH_TREND',
            status='active'
        )
        
        db.session.add(forecast)
        db.session.commit()
        
        return forecast


class ReorderRecommendationService:
    """补货建议服务"""
    
    @staticmethod
    def calculate_safety_stock(part_id, warehouse_id, service_level=95):
        """
        计算安全库存
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :param service_level: 服务水平（%）
        :return: 安全库存
        """
        # 获取需求标准差（简化计算）
        avg_demand = DemandForecastService.calculate_moving_average(part_id, warehouse_id, 30)
        std_deviation = avg_demand * 0.2  # 假设标准差为均值的 20%
        
        # Z 值（服务水平对应的标准正态分布分位数）
        z_values = {
            90: 1.28,
            95: 1.65,
            99: 2.33
        }
        z_value = z_values.get(service_level, 1.65)
        
        # 假设提前期为 7 天
        lead_time = 7
        safety_stock = z_value * std_deviation * math.sqrt(lead_time)
        
        return round(safety_stock, 2)
    
    @staticmethod
    def calculate_eoq(part_id, warehouse_id, annual_demand=None):
        """
        计算经济订货批量（EOQ）
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :param annual_demand: 年需求量
        :return: EOQ
        """
        if not annual_demand:
            # 计算年需求
            daily_demand = DemandForecastService.calculate_moving_average(part_id, warehouse_id)
            annual_demand = daily_demand * 365
        
        # 假设参数（实际应从配置获取）
        ordering_cost = 100  # 每次订货成本
        holding_cost_rate = 0.2  # 持有成本率（20%）
        
        # 获取备件单价
        inventory = InventoryV3.query.filter_by(part_id=part_id, warehouse_id=warehouse_id).first()
        unit_cost = float(inventory.unit_cost) if inventory and inventory.unit_cost else 10
        
        holding_cost = unit_cost * holding_cost_rate
        
        if holding_cost > 0:
            eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        else:
            eoq = 0
        
        return round(eoq, 0)
    
    @staticmethod
    def generate_reorder_recommendation(part_id, warehouse_id):
        """
        生成补货建议
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :return: 补货建议
        """
        # 获取当前库存
        inventory = InventoryV3.query.filter_by(
            part_id=part_id,
            warehouse_id=warehouse_id
        ).first()
        
        if not inventory:
            return None
        
        current_stock = float(inventory.available_quantity)
        
        # 计算安全库存
        safety_stock = ReorderRecommendationService.calculate_safety_stock(part_id, warehouse_id)
        
        # 计算 reorder 点
        daily_demand = DemandForecastService.calculate_moving_average(part_id, warehouse_id)
        lead_time = 7  # 7 天提前期
        reorder_point = daily_demand * lead_time + safety_stock
        
        # 计算 EOQ
        eoq = ReorderRecommendationService.calculate_eoq(part_id, warehouse_id)
        
        # 判断是否需要补货
        if current_stock <= reorder_point:
            recommended_quantity = max(eoq, reorder_point - current_stock)
            
            # 计算缺货风险
            stockout_risk = max(0, min(100, (reorder_point - current_stock) / reorder_point * 100)) if reorder_point > 0 else 0
            
            # 确定紧急程度
            if current_stock <= safety_stock * 0.5:
                urgency_level = 'URGENT'
                priority = 1
            elif current_stock <= safety_stock:
                urgency_level = 'HIGH'
                priority = 2
            elif current_stock <= reorder_point * 0.8:
                urgency_level = 'MEDIUM'
                priority = 3
            else:
                urgency_level = 'LOW'
                priority = 4
            
            # 获取预测需求
            forecast = DemandForecast.query.filter_by(
                part_id=part_id,
                warehouse_id=warehouse_id,
                status='active'
            ).order_by(DemandForecast.created_at.desc()).first()
            
            forecast_demand = float(forecast.predicted_demand) if forecast else 0
            
            # 创建补货建议
            recommendation = ReorderRecommendation(
                warehouse_id=warehouse_id,
                part_id=part_id,
                part_no=inventory.part.part_no if inventory.part else '',
                part_name=inventory.part.part_name if inventory.part else '',
                current_stock=current_stock,
                safety_stock=safety_stock,
                reorder_point=reorder_point,
                recommended_quantity=recommended_quantity,
                priority=priority,
                urgency_level=urgency_level,
                lead_time_days=lead_time,
                estimated_cost=recommended_quantity * float(inventory.unit_cost),
                forecast_demand=forecast_demand,
                stockout_risk=round(stockout_risk, 2),
                status='pending',
                generated_by='AI'
            )
            
            db.session.add(recommendation)
            db.session.commit()
            
            return recommendation
        
        return None
    
    @staticmethod
    def batch_generate_recommendations(warehouse_id):
        """
        批量生成补货建议
        :param warehouse_id: 仓库 ID
        :return: 生成的建议数量
        """
        # 获取仓库所有备件
        inventories = InventoryV3.query.filter_by(warehouse_id=warehouse_id).all()
        
        count = 0
        for inventory in inventories:
            recommendation = ReorderRecommendationService.generate_reorder_recommendation(
                inventory.part_id, warehouse_id
            )
            if recommendation:
                count += 1
        
        return count


class InventoryOptimizationService:
    """库存优化服务"""
    
    @staticmethod
    def calculate_optimization_params(part_id, warehouse_id):
        """
        计算库存优化参数
        :param part_id: 备件 ID
        :param warehouse_id: 仓库 ID
        :return: 优化参数
        """
        # 计算需求统计
        avg_daily_demand = DemandForecastService.calculate_moving_average(part_id, warehouse_id)
        trend, growth_rate = DemandForecastService.calculate_trend(part_id, warehouse_id)
        
        # 计算需求波动率
        demand_variability = abs(growth_rate) * 100
        
        # 计算提前期波动率（假设）
        lead_time_variability = 10.0  # 10%
        
        # 计算安全库存
        safety_stock = ReorderRecommendationService.calculate_safety_stock(part_id, warehouse_id)
        
        # 计算 reorder 点
        lead_time = 7
        reorder_point = avg_daily_demand * lead_time + safety_stock
        
        # 计算 EOQ
        eoq = ReorderRecommendationService.calculate_eoq(part_id, warehouse_id)
        
        # 计算最大库存
        max_stock = reorder_point + eoq
        
        # 获取或创建优化配置
        optimization = InventoryOptimization.query.filter_by(
            part_id=part_id,
            warehouse_id=warehouse_id
        ).first()
        
        if not optimization:
            optimization = InventoryOptimization(
                warehouse_id=warehouse_id,
                part_id=part_id,
                target_service_level=95.00
            )
            db.session.add(optimization)
        
        # 更新参数
        optimization.demand_variability = Decimal(str(round(demand_variability, 2)))
        optimization.lead_time_variability = Decimal(str(lead_time_variability))
        optimization.safety_stock = Decimal(str(safety_stock))
        optimization.reorder_point = Decimal(str(reorder_point))
        optimization.eoq = Decimal(str(eoq))
        optimization.max_stock = Decimal(str(max_stock))
        optimization.last_calculated_at = datetime.utcnow()
        optimization.status = 'active'
        
        db.session.commit()
        
        return optimization
