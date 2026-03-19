# -*- coding: utf-8 -*-
"""
测试 AI 检测功能 - 检测 10 条测试数据
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('SILICONFLOW_API_KEY', 'sk-ojhphrjqyigzgskcackiaixmsznscynmhydoiayelgpmmitn')
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-72B-Instruct"


def load_test_data():
    """加载测试数据"""
    filepath = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_parts_data.json')
    
    if not os.path.exists(filepath):
        print("✗ 测试数据文件不存在")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_single_part(part_data):
    """检测单个备件"""
    prompt = f"""
请检测以下备件数据的准确性和规范性：

备件信息：
{json.dumps(part_data, ensure_ascii=False, indent=2)}

检测项：
1. 数据完整性（必填字段是否完整）
2. 命名规范性（名称格式是否正确）
3. 分类准确性（分类代码是否匹配）
4. 编码正确性（编码格式是否规范）
5. 参数合理性（尺寸、重量、价格是否合理）
6. 供应商可信度（供应商是否正规）

输出格式：JSON
{{
  "is_valid": true/false,
  "score": 0-100,
  "issues": [
    {{
      "type": "问题类型",
      "description": "问题描述",
      "severity": "高/中/低",
      "suggestion": "修复建议"
    }}
  ],
  "summary": "总体评价"
}}
"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是工业备件数据质量专家，负责检测和修复备件数据问题。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 提取 JSON
        import re
        json_pattern = r'\{.*?\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        
        if matches:
            return json.loads(matches[0])
        else:
            return {'is_valid': False, 'score': 0, 'error': '解析失败'}
            
    except Exception as e:
        return {'is_valid': False, 'score': 0, 'error': str(e)}


def main():
    """主函数"""
    print("="*70)
    print("硅基流动 AI - 备件数据质量检测（测试 10 条）")
    print("="*70)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    parts_data = load_test_data()
    
    if not parts_data:
        print("✗ 没有检测到测试数据")
        return
    
    print(f"\n已加载 {len(parts_data)} 条测试数据\n")
    
    results = []
    
    for i, part in enumerate(parts_data, 1):
        print(f"[{i}/{len(parts_data)}] 检测：{part['part_name']}")
        
        result = check_single_part(part)
        results.append(result)
        
        score = result.get('score', 0)
        is_valid = result.get('is_valid', False)
        issues_count = len(result.get('issues', []))
        
        if is_valid and score >= 90:
            print(f"  ✓ 通过 - 评分：{score} - 问题数：{issues_count}")
        elif score >= 70:
            print(f"  ⚠ 需要改进 - 评分：{score} - 问题数：{issues_count}")
        else:
            print(f"  ✗ 存在问题 - 评分：{score} - 问题数：{issues_count}")
        
        # 显示问题
        if issues_count > 0:
            for issue in result.get('issues', [])[:2]:  # 只显示前 2 个问题
                print(f"    - {issue.get('type')}: {issue.get('description', '')[:50]}")
        
        print()
    
    # 统计
    total = len(results)
    passed = sum(1 for r in results if r.get('is_valid', False))
    avg_score = sum(r.get('score', 0) for r in results) / total if total > 0 else 0
    
    print("="*70)
    print("AI 检测统计")
    print("="*70)
    print(f"总记录数：{total}")
    print(f"通过数：{passed} ({passed/total*100:.1f}%)")
    print(f"未通过数：{total - passed} ({(total-passed)/total*100:.1f}%)")
    print(f"平均评分：{avg_score:.1f}")
    print("="*70)
    
    # 保存报告
    report = {
        'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': total,
        'passed_count': passed,
        'average_score': avg_score,
        'results': results
    }
    
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    filepath = os.path.join(reports_dir, 'test_ai_check_report.json')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 检测报告已保存：{filepath}")
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    main()
