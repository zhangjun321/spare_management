#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪表盘优化测试脚本
验证性能优化、数据库兼容性和功能完整性
"""

import sys
import time
import requests
import json
from datetime import datetime

class DashboardTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()

    def log(self, test_name, status, details="", duration=0):
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} {test_name}: {status}")
        if details:
            print(f"   详情: {details}")
        if duration > 0:
            print(f"   耗时: {duration:.3f}秒")

    def test_api_endpoint(self, endpoint, description, expected_status=200):
        """测试单个API端点"""
        start_time = time.time()
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == expected_status:
                data = response.json() if 'application/json' in response.headers.get('content-type', '') else None
                self.log(description, "PASS", f"响应时间: {duration:.3f}秒", duration)
                return True, data
            else:
                self.log(description, "FAIL", f"状态码: {response.status_code}", duration)
                return False, None
        except Exception as e:
            duration = time.time() - start_time
            self.log(description, "FAIL", f"异常: {str(e)}", duration)
            return False, None

    def test_database_compatibility(self):
        """测试数据库兼容性"""
        print("\n" + "="*60)
        print("测试1: 数据库兼容性验证")
        print("="*60)
        
        # 测试基础统计API（验证数据库查询）
        success, data = self.test_api_endpoint(
            "/api/stats", 
            "基础统计数据API", 
            expected_status=200
        )
        
        if success and data:
            # 验证数据结构
            expected_keys = ['spare_parts_count', 'equipment_count']
            missing_keys = [k for k in expected_keys if k not in data]
            if missing_keys:
                self.log("数据结构验证", "WARN", f"缺少字段: {missing_keys}")
            else:
                self.log("数据结构验证", "PASS", "所有必需字段都存在")

    def test_performance_optimization(self):
        """测试性能优化"""
        print("\n" + "="*60)
        print("测试2: 性能优化验证")
        print("="*60)
        
        # 测试多次请求，验证缓存效果
        print("\n测试缓存机制（连续3次请求）:")
        durations = []
        
        for i in range(3):
            start = time.time()
            try:
                self.session.get(f"{self.base_url}/api/stats", timeout=5)
                dur = time.time() - start
                durations.append(dur)
                print(f"  请求{i+1}: {dur:.3f}秒")
            except Exception as e:
                print(f"  请求{i+1}失败: {e}")
        
        if len(durations) >= 2:
            # 检查后序请求是否更快（缓存效果）
            if durations[-1] < durations[0] * 0.8:
                self.log("缓存性能提升", "PASS", 
                        f"首次: {durations[0]:.3f}s, 末次: {durations[-1]:.3f}s")
            else:
                self.log("缓存性能提升", "WARN", 
                        "缓存效果不明显或未启用")
        
        # 测试其他API端点的响应时间
        api_endpoints = [
            ("/api/maintenance-status", "维修状态API"),
            ("/api/spare-part-value", "备件价值API"),
            ("/api/transaction-trend", "交易趋势API")
        ]
        
        for endpoint, desc in api_endpoints:
            self.test_api_endpoint(endpoint, desc)

    def test_new_features(self):
        """测试新功能"""
        print("\n" + "="*60)
        print("测试3: 新功能验证")
        print("="*60)
        
        # 测试新增的分析API
        new_apis = [
            ("/api/analysis/inventory-turnover", "库存周转率分析"),
            ("/api/analysis/equipment-oee", "设备OEE分析"),
            ("/api/analysis/stock-age", "库龄分析"),
            ("/api/alerts/active", "活跃告警"),
            ("/api/trend/comparison", "趋势对比"),
            ("/api/ai/demand-forecast", "AI需求预测"),
            ("/api/ai/abc-analysis", "ABC分类分析")
        ]
        
        for endpoint, desc in new_apis:
            self.test_api_endpoint(endpoint, desc)

    def test_static_resources(self):
        """测试静态资源"""
        print("\n" + "="*60)
        print("测试4: 静态资源验证")
        print("="*60)
        
        static_files = [
            ("/static/css/dashboard-optimized.css", "优化CSS文件"),
            ("/static/js/dashboard-optimizer.js", "性能优化JS"),
            ("/static/js/dashboard-interactions.js", "交互增强JS")
        ]
        
        for path, desc in static_files:
            try:
                start = time.time()
                response = self.session.get(f"{self.base_url}{path}", timeout=5)
                duration = time.time() - start
                
                if response.status_code == 200:
                    size_kb = len(response.content) / 1024
                    self.log(desc, "PASS", f"大小: {size_kb:.2f}KB", duration)
                else:
                    self.log(desc, "FAIL", f"状态码: {response.status_code}", duration)
            except Exception as e:
                self.log(desc, "FAIL", str(e))

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("测试报告汇总")
        print("="*60)
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        total = len(self.results)
        
        print(f"\n总计: {total} 个测试")
        print(f"通过: {passed} ✅")
        print(f"警告: {warned} ⚠️")
        print(f"失败: {failed} ❌")
        
        avg_duration = sum(r["duration"] for r in self.results if r["duration"] > 0) / max(1, passed)
        print(f"\n平均响应时间: {avg_duration:.3f}秒")
        
        # 保存详细报告
        report_file = "dashboard-test-report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "warned": warned,
                    "average_duration": avg_duration
                },
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        return failed == 0

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始仪表盘优化测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标地址: {self.base_url}")
        
        try:
            # 等待服务器响应
            print("\n等待服务器启动...")
            for i in range(10):
                try:
                    requests.get(self.base_url, timeout=2)
                    break
                except:
                    time.sleep(1)
            
            # 运行各项测试
            self.test_database_compatibility()
            self.test_performance_optimization()
            self.test_new_features()
            self.test_static_resources()
            
            # 生成报告
            return self.generate_report()
            
        except Exception as e:
            print(f"\n❌ 测试过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="仪表盘优化测试工具")
    parser.add_argument("--url", default="http://127.0.0.1:5000", 
                       help="测试服务器地址 (默认: http://127.0.0.1:5000)")
    
    args = parser.parse_args()
    
    tester = DashboardTester(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
