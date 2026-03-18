# -*- coding: utf-8 -*-
"""
备件数据 AI 检测功能
对备件信息进行智能检测，识别不准确内容并给出修复建议
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 硅基流动 API 配置
API_KEY = os.getenv('SILICONFLOW_API_KEY', 'sk-ojhphrjqyigzgskcackiaixmsznscynmhydoiayelgpmmitn')
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-72B-Instruct"


class AIPartsChecker:
    """AI 备件检测器"""
    
    def __init__(self):
        self.api_key = API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.check_results = []
    
    def check_single_part(self, part_data, check_items=None):
        """
        检测单个备件
        
        Args:
            part_data: 备件数据字典
            check_items: 检测项列表（默认检测全部）
        """
        if check_items is None:
            check_items = [
                'completeness',      # 数据完整性
                'naming',           # 命名规范性
                'classification',   # 分类准确性
                'coding',          # 编码正确性
                'parameters',      # 参数合理性
                'supplier',        # 供应商可信度
                'price',           # 价格合理性
                'duplicate'        # 重复检测
            ]
        
        prompt = self._build_check_prompt(part_data, check_items)
        
        try:
            payload = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是工业备件数据质量专家，负责检测和修复备件数据问题。熟悉各类工业备件的标准、规范、市场价格等信息。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 3000
            }
            
            response = requests.post(API_URL, headers=self.headers, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 提取 JSON 结果
            check_result = self._extract_json(content)
            
            # 添加原始数据
            check_result['original_data'] = part_data
            check_result['check_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.check_results.append(check_result)
            
            return check_result
            
        except Exception as e:
            print(f"✗ AI 检测失败：{str(e)}")
            return {
                'is_valid': False,
                'score': 0,
                'error': str(e),
                'original_data': part_data
            }
    
    def check_batch(self, parts_data, check_items=None):
        """
        批量检测备件
        
        Args:
            parts_data: 备件数据列表
            check_items: 检测项列表
        """
        print(f"\n{'='*70}")
        print(f"开始批量 AI 检测 - 共{len(parts_data)}条记录")
        print(f"{'='*70}")
        
        results = []
        
        for i, part in enumerate(parts_data, 1):
            print(f"\n[{i}/{len(parts_data)}] 检测：{part.get('part_name', '未知')}")
            
            result = self.check_single_part(part, check_items)
            results.append(result)
            
            # 打印检测结果摘要
            score = result.get('score', 0)
            is_valid = result.get('is_valid', False)
            issues_count = len(result.get('issues', []))
            
            if is_valid and score >= 90:
                print(f"  ✓ 通过检测 - 评分：{score} - 问题数：{issues_count}")
            elif score >= 70:
                print(f"  ⚠ 需要改进 - 评分：{score} - 问题数：{issues_count}")
            else:
                print(f"  ✗ 存在问题 - 评分：{score} - 问题数：{issues_count}")
            
            # 避免 API 限流
            import time
            time.sleep(2)
        
        # 生成统计报告
        self._print_statistics(results)
        
        return results
    
    def _build_check_prompt(self, part_data, check_items):
        """构建检测提示词"""
        
        check_item_names = {
            'completeness': '数据完整性检测',
            'naming': '命名规范性检测',
            'classification': '分类准确性检测',
            'coding': '编码正确性检测',
            'parameters': '参数合理性检测',
            'supplier': '供应商可信度检测',
            'price': '价格合理性检测',
            'duplicate': '重复数据检测'
        }
        
        check_items_desc = '\n'.join([
            f"  - {key}: {check_item_names.get(key, '')}"
            for key in check_items
        ])
        
        return f"""
请对以下备件数据进行全面质量检测：

## 备件信息
{json.dumps(part_data, ensure_ascii=False, indent=2)}

## 检测项
{check_items_desc}

## 详细检测要求

### 1. 数据完整性检测
检查以下必填字段是否完整：
- part_code: 备件编码
- part_name: 备件名称（5-100 字符）
- spec_model: 规格型号
- category_code: 分类代码
- unit: 单位
- unit_price: 单价（正数）
- supplier: 供应商

### 2. 命名规范性检测
- 名称格式：品牌 + 品类 + 关键参数
- 禁止特殊字符（除-_.外）
- 禁止模糊词汇（如"优质"、"高级"）
- 必须包含关键规格参数

### 3. 分类准确性检测
- 备件名称与分类代码是否匹配
- 规格型号与分类是否匹配
- 给出分类置信度评分

### 4. 编码正确性检测
- 编码格式：品牌代码 (4 位)-分类代码 (6 位)-规格代码 (3 位)-流水号 (3 位)
- 品牌代码是否有效
- 分类代码是否匹配

### 5. 参数合理性检测
- 重量与尺寸是否匹配
- 材质描述是否准确
- 安全库存是否合理

### 6. 供应商可信度检测
- 供应商名称是否规范
- 是否为知名供应商或授权商
- 给出供应商可信度评级（A/B/C/D）

### 7. 价格合理性检测
- 与同类备件市场价对比
- 价格偏离度计算
- 标记异常价格（偏离度>50%）

### 8. 重复数据检测
- 与已有备件对比相似度
- 识别完全重复（相似度≥95%）
- 识别高度相似（相似度≥80%）

## 输出格式
输出纯 JSON 格式，不要任何其他说明文字。格式如下：
{{
  "is_valid": true/false,
  "score": 0-100,
  "check_items": {{
    "completeness": {{
      "passed": true/false,
      "score": 0-100,
      "missing_fields": [],
      "suggestions": ""
    }},
    "naming": {{
      "passed": true/false,
      "score": 0-100,
      "issues": [],
      "suggested_name": ""
    }},
    "classification": {{
      "passed": true/false,
      "score": 0-100,
      "confidence": 0-100,
      "suggested_category": "",
      "issues": []
    }},
    "coding": {{
      "passed": true/false,
      "score": 0-100,
      "corrected_code": "",
      "issues": []
    }},
    "parameters": {{
      "passed": true/false,
      "score": 0-100,
      "abnormal_params": [],
      "suggestions": []
    }},
    "supplier": {{
      "passed": true/false,
      "score": 0-100,
      "credit_level": "A/B/C/D",
      "issues": []
    }},
    "price": {{
      "passed": true/false,
      "score": 0-100,
      "market_reference": 0,
      "deviation_rate": 0,
      "warning_level": "正常/关注/警告/异常"
    }},
    "duplicate": {{
      "passed": true/false,
      "score": 0-100,
      "similarity": 0-100,
      "possible_duplicates": []
    }}
  }},
  "issues": [
    {{
      "type": "问题类型",
      "description": "问题描述",
      "severity": "高/中/低",
      "suggestion": "修复建议",
      "auto_fix_value": "自动修复值（如有）"
    }}
  ],
  "fixed_data": {{修复后的完整数据}},
  "summary": "总体评价和建议"
}}

现在开始检测：
"""
    
    def _extract_json(self, content):
        """从 AI 响应中提取 JSON"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except:
            # 查找 JSON 块
            import re
            json_pattern = r'\{\s*".*?\}'
            matches = re.findall(json_pattern, content, re.DOTALL)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except:
                    print("⚠ JSON 解析失败，返回基础结构")
                    return {
                        'is_valid': False,
                        'score': 0,
                        'issues': [{'type': '解析错误', 'description': 'AI 响应格式异常'}]
                    }
            else:
                print("⚠ 未找到 JSON 数据")
                return {
                    'is_valid': False,
                    'score': 0,
                    'issues': [{'type': '格式错误', 'description': 'AI 未返回有效数据'}]
                }
    
    def _print_statistics(self, results):
        """打印统计信息"""
        total = len(results)
        passed = sum(1 for r in results if r.get('is_valid', False))
        avg_score = sum(r.get('score', 0) for r in results) / total if total > 0 else 0
        
        # 问题分类统计
        issue_stats = {}
        for result in results:
            for issue in result.get('issues', []):
                issue_type = issue.get('type', '未知')
                issue_stats[issue_type] = issue_stats.get(issue_type, 0) + 1
        
        print(f"\n{'='*70}")
        print("AI 检测统计报告")
        print(f"{'='*70}")
        print(f"总记录数：{total}")
        print(f"通过数：{passed} ({passed/total*100:.1f}%)")
        print(f"未通过数：{total - passed} ({(total-passed)/total*100:.1f}%)")
        print(f"平均评分：{avg_score:.1f}")
        print(f"\n问题分类统计:")
        for issue_type, count in sorted(issue_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue_type}: {count} 条")
        print(f"{'='*70}")
    
    def save_report(self, results, filename='ai_check_report.json'):
        """保存检测报告"""
        # 创建 reports 目录
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, filename)
        
        report = {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(results),
            'passed_count': sum(1 for r in results if r.get('is_valid', False)),
            'average_score': sum(r.get('score', 0) for r in results) / len(results) if results else 0,
            'results': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 检测报告已保存：{filepath}")
        
        return filepath
    
    def export_fixed_data(self, results, filename='fixed_parts_data.json'):
        """导出修复后的数据"""
        fixed_data = []
        
        for result in results:
            if 'fixed_data' in result and result['fixed_data']:
                fixed_data.append(result['fixed_data'])
            else:
                fixed_data.append(result.get('original_data', {}))
        
        # 保存到 data 目录
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 修复后数据已保存：{filepath}")
        print(f"  总计：{len(fixed_data)} 条记录")
        
        return filepath


def load_parts_from_json(filename='spare_parts_data.json'):
    """从 JSON 文件加载备件数据"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    filepath = os.path.join(data_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"✗ 文件不存在：{filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    print("="*70)
    print("硅基流动 AI - 备件数据质量检测工具")
    print("="*70)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 加载备件数据
    parts_data = load_parts_from_json()
    
    if not parts_data:
        print("✗ 没有检测到备件数据，请先生成数据")
        return
    
    print(f"已加载 {len(parts_data)} 条备件数据")
    
    # 创建检测器
    checker = AIPartsChecker()
    
    # 批量检测
    results = checker.check_batch(parts_data)
    
    # 保存报告
    checker.save_report(results)
    
    # 导出修复后的数据
    checker.export_fixed_data(results)
    
    print("\n" + "="*70)
    print("AI 检测完成！")
    print("="*70)
    print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    main()
