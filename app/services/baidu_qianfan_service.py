"""
百度千帆 AI 服务
集成百度千帆大模型，实现智能分析和决策
使用 OpenAI SDK 方式调用（与图片生成服务一致）
"""

import json
import os
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.spare_part import SparePart
from app.models.inbound_outbound import InboundOrder, OutboundOrder
from sqlalchemy import func, and_
from sqlalchemy.sql import text

# 使用 OpenAI SDK 调用百度千帆
try:
    from openai import OpenAI
except ImportError:
    print("警告：未安装 openai 库，请运行：pip install openai")
    OpenAI = None


class BaiduQianfanService:
    """百度千帆 AI 服务"""
    
    def __init__(self, api_key=None):
        """
        初始化百度千帆服务（使用 OpenAI SDK 方式）
        
        Args:
            api_key: 百度千帆 API Key
        """
        import os
        
        if not api_key:
            # 从环境变量获取（与图片生成服务使用相同的配置）
            self.api_key = os.getenv("BAIDU_API_KEY", "")
        else:
            self.api_key = api_key
        
        self.client = None
        
        # 初始化 OpenAI 客户端（用于百度千帆）
        if OpenAI and self.api_key:
            self.client = OpenAI(
                base_url='https://qianfan.baidubce.com/v2',
                api_key=self.api_key
            )
            current_app.logger.info("百度千帆 OpenAI 客户端初始化成功")
        elif not self.api_key:
            current_app.logger.warning("未配置 BAIDU_API_KEY")
        else:
            current_app.logger.warning("未安装 openai 库，AI 功能不可用")
    
    def chat(self, messages, system_prompt=None):
        """
        调用 ERNIE-Bot 进行对话（使用 OpenAI SDK）
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "你好"}]
            system_prompt: 系统提示词
            
        Returns:
            dict: AI 响应
        """
        if not self.client:
            return {'success': False, 'error': '客户端未初始化'}
        
        try:
            # 使用 OpenAI SDK 调用百度千帆
            response = self.client.chat.completions.create(
                model="ernie-bot-4.0",  # 使用 ERNIE-Bot 4.0
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                stream=False
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return {
                    'success': True,
                    'content': content,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                        'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                        'total_tokens': response.usage.total_tokens if response.usage else 0
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '无响应内容'
                }
                
        except Exception as e:
            current_app.logger.error(f"调用百度千帆 AI 异常：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_inventory_trend(self, inventory_records, days=30):
        """
        AI 分析库存趋势
        
        Args:
            inventory_records: 库存记录列表
            days: 分析天数
            
        Returns:
            dict: 分析结果
        """
        try:
            # 构建分析提示词
            parts_data = []
            for record in inventory_records[:20]:  # 限制数量，避免 token 超限
                spare_part = record.spare_part
                parts_data.append({
                    'part_code': spare_part.part_code,
                    'name': spare_part.name,
                    'current_stock': record.quantity,
                    'stock_status': record.stock_status,
                    'min_stock': record.min_stock,
                    'max_stock': record.max_stock
                })
            
            system_prompt = """你是一个智能仓库管理 AI 助手，擅长分析库存趋势和提供优化建议。
请分析以下备件的库存数据，提供：
1. 库存状态总体评估
2. 需要补货的备件清单
3. 可能超储的备件清单
4. 库存优化建议
请用 JSON 格式返回结果。"""
            
            user_message = f"请分析以下{len(parts_data)}个备件的库存数据：\n{json.dumps(parts_data, ensure_ascii=False)}"
            
            messages = [{'role': 'user', 'content': user_message}]
            
            result = self.chat(messages, system_prompt)
            
            if result['success']:
                # 尝试解析 JSON 结果
                try:
                    import re
                    json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        return {
                            'success': True,
                            'analysis': analysis,
                            'raw_content': result['content']
                        }
                except:
                    pass
                
                return {
                    'success': True,
                    'analysis': {'text': result['content']},
                    'raw_content': result['content']
                }
            else:
                return result
                
        except Exception as e:
            current_app.logger.error(f"AI 分析库存趋势异常：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    def analyze_inventory_health(self, inventory_data):
        """
        AI 分析库存健康状况
        
        Args:
            inventory_data: 库存数据列表
                [
                    {
                        'part_id': 1,
                        'part_code': 'SP-001',
                        'part_name': '备件名称',
                        'quantity': 100,
                        'stock_status': 'normal',
                        'min_stock': 50,
                        'max_stock': 200
                    },
                    ...
                ]
        
        Returns:
            dict: 分析结果
                {
                    'success': True,
                    'analysis': {
                        'health_score': 85,
                        'summary': '库存整体健康状况良好',
                        'issues': [
                            {'part_code': 'SP-002', 'issue': '库存不足', 'suggestion': '建议补货 50 个'},
                            ...
                        ],
                        'recommendations': ['优化 A 类备件库存', '清理超储备件']
                    }
                }
        """
        try:
            # 构建分析提示词
            system_prompt = """你是一个智能仓库库存健康分析 AI 助手，擅长评估库存健康状况并提供优化建议。
请分析以下库存数据，提供：
1. 库存健康评分（0-100 分）
2. 库存状态总体评估
3. 问题备件清单（库存不足、超储、呆滞等）
4. 具体优化建议
请用 JSON 格式返回结果。"""
            
            user_message = f"请分析以下{len(inventory_data)}个备件的库存健康状况：\n{json.dumps(inventory_data, ensure_ascii=False)}"
            
            messages = [{'role': 'user', 'content': user_message}]
            
            result = self.chat(messages, system_prompt)
            
            if result['success']:
                # 尝试解析 JSON 结果
                try:
                    import re
                    json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        return {
                            'success': True,
                            'analysis': analysis,
                            'raw_content': result['content']
                        }
                except Exception as e:
                    current_app.logger.error(f"解析 AI 健康分析结果失败：{str(e)}")
                    return {
                        'success': True,
                        'analysis': {'summary': result['content']},
                        'raw_content': result['content']
                    }
            else:
                return result
                
        except Exception as e:
            current_app.logger.error(f"AI 分析库存健康异常：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    def predict_demand(self, historical_data, days=30):
        """
        AI 预测需求
        
        Args:
            historical_data: 历史数据（出入库记录）
            days: 预测天数
            
        Returns:
            dict: 预测结果
        """
        try:
            # 构建预测提示词
            system_prompt = """你是一个智能仓库需求预测 AI 助手，擅长根据历史数据预测未来需求。
请分析以下历史出入库数据，预测未来 30 天的需求：
1. 各备件的平均日出库量
2. 需求趋势（增长/下降/稳定）
3. 建议的安全库存水平
4. 建议的补货时间点
请用 JSON 格式返回结果。"""
            
            user_message = f"请分析以下历史数据并预测未来{days}天的需求：\n{json.dumps(historical_data, ensure_ascii=False)}"
            
            messages = [{'role': 'user', 'content': user_message}]
            
            result = self.chat(messages, system_prompt)
            
            if result['success']:
                try:
                    import re
                    json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                    if json_match:
                        prediction = json.loads(json_match.group())
                        return {
                            'success': True,
                            'prediction': prediction,
                            'raw_content': result['content']
                        }
                except:
                    pass
                
                return {
                    'success': True,
                    'prediction': {'text': result['content']},
                    'raw_content': result['content']
                }
            else:
                return result
                
        except Exception as e:
            current_app.logger.error(f"AI 预测需求异常：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    def recommend_location(self, part_data, warehouse_locations):
        """
        AI 推荐最佳货位
        
        Args:
            part_data: 备件数据
            warehouse_locations: 仓库货位列表
            
        Returns:
            dict: 推荐结果
        """
        try:
            system_prompt = """你是一个智能仓库货位分配 AI 助手，擅长根据备件特性和仓库布局推荐最佳货位。
请考虑以下因素：
1. 备件的尺寸、重量、存储要求
2. 备件的出入库频率（ABC 分类）
3. 货位的位置、大小、承重
4. 拣货路径优化
请推荐最佳货位并说明理由。
请用 JSON 格式返回结果。"""
            
            user_message = f"""备件数据：{json.dumps(part_data, ensure_ascii=False)}
可用货位：{json.dumps(warehouse_locations, ensure_ascii=False)}
请推荐最佳货位。"""
            
            messages = [{'role': 'user', 'content': user_message}]
            
            result = self.chat(messages, system_prompt)
            
            if result['success']:
                try:
                    import re
                    json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                    if json_match:
                        recommendation = json.loads(json_match.group())
                        return {
                            'success': True,
                            'recommendation': recommendation,
                            'raw_content': result['content']
                        }
                except:
                    pass
                
                return {
                    'success': True,
                    'recommendation': {'text': result['content']},
                    'raw_content': result['content']
                }
            else:
                return result
                
        except Exception as e:
            current_app.logger.error(f"AI 推荐货位异常：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    def optimize_picking_path(self, picking_list, warehouse_layout):
        """
        AI 优化拣货路径
        
        Args:
            picking_list: 拣货清单
            warehouse_layout: 仓库布局
            
        Returns:
            dict: 优化结果
        """
        try:
            system_prompt = """你是一个智能仓库路径优化 AI 助手，擅长优化拣货路径提高效率。
请根据仓库布局和拣货清单，规划最优拣货路径，考虑：
1. 减少行走距离
2. 避免重复路径
3. 考虑货物重量（重物在下）
4. 考虑易碎品（轻拿轻放）
请返回优化后的拣货顺序和路径。
请用 JSON 格式返回结果。"""
            
            user_message = f"""拣货清单：{json.dumps(picking_list, ensure_ascii=False)}
仓库布局：{json.dumps(warehouse_layout, ensure_ascii=False)}
请优化拣货路径。"""
            
            messages = [{'role': 'user', 'content': user_message}]
            
            result = self.chat(messages, system_prompt)
            
            if result['success']:
                try:
                    import re
                    json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                    if json_match:
                        optimization = json.loads(json_match.group())
                        return {
                            'success': True,
                            'optimization': optimization,
                            'raw_content': result['content']
                        }
                except:
                    pass
                
                return {
                    'success': True,
                    'optimization': {'text': result['content']},
                    'raw_content': result['content']
                }
            else:
                return result
                
        except Exception as e:
            current_app.logger.error(f"AI 优化拣货路径异常：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_intelligent_report(self, report_type, data):
        """
        AI 生成智能报告
        
        Args:
            report_type: 报告类型（daily/weekly/monthly/analysis）
            data: 报告数据
            
        Returns:
            dict: 生成的报告
        """
        try:
            system_prompts = {
                'daily': "你是一个智能仓库日报生成助手，请根据提供的数据生成简洁明了的日报。",
                'weekly': "你是一个智能仓库周报生成助手，请根据提供的数据生成全面的周报，包括趋势分析。",
                'monthly': "你是一个智能仓库月报生成助手，请根据提供的数据生成详细的月报，包括 KPI 分析和改进建议。",
                'analysis': "你是一个智能仓库分析专家，请根据提供的数据进行深度分析，提供洞察和建议。"
            }
            
            system_prompt = system_prompts.get(report_type, "你是一个智能仓库报告生成助手。")
            
            user_message = f"请生成{report_type}报告，数据如下：\n{json.dumps(data, ensure_ascii=False)}"
            
            messages = [{'role': 'user', 'content': user_message}]
            
            result = self.chat(messages, system_prompt)
            
            if result['success']:
                return {
                    'success': True,
                    'report': result['content'],
                    'report_type': report_type
                }
            else:
                return result
                
        except Exception as e:
            current_app.logger.error(f"AI 生成智能报告异常：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    def detect_anomalies(self, transaction_logs):
        """
        AI 检测异常
        
        Args:
            transaction_logs: 库存变动日志
            
        Returns:
            dict: 检测结果
        """
        try:
            system_prompt = """你是一个智能仓库异常检测 AI 助手，擅长发现库存变动中的异常模式。
请检测以下异常：
1. 异常的大额出入库
2. 频繁的库存调整
3. 非工作时间的操作
4. 其他可疑模式
请列出发现的异常并说明原因。
请用 JSON 格式返回结果。"""
            
            user_message = f"请检测以下库存变动记录中的异常：\n{json.dumps(transaction_logs, ensure_ascii=False)}"
            
            messages = [{'role': 'user', 'content': user_message}]
            
            result = self.chat(messages, system_prompt)
            
            if result['success']:
                try:
                    import re
                    json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                    if json_match:
                        anomalies = json.loads(json_match.group())
                        return {
                            'success': True,
                            'anomalies': anomalies,
                            'raw_content': result['content']
                        }
                except:
                    pass
                
                return {
                    'success': True,
                    'anomalies': {'text': result['content']},
                    'raw_content': result['content']
                }
            else:
                return result
                
        except Exception as e:
            current_app.logger.error(f"AI 检测异常异常：{str(e)}")
            return {'success': False, 'error': str(e)}


# 全局服务实例
_qianfan_service = None


def get_qianfan_service():
    """获取百度千帆服务实例"""
    global _qianfan_service
    if _qianfan_service is None:
        _qianfan_service = BaiduQianfanService()
    return _qianfan_service
