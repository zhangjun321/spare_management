# -*- coding: utf-8 -*-
"""
使用硅基流动 API 生成剩余的轮播图图片
"""

import os
import requests
import time
from datetime import datetime

# 硅基流动 API 配置
API_KEY = "sk-ojhphrjqyigzgskcackiaixmsznscynmhydoiayelgpmmitn"
API_URL = "https://api.siliconflow.cn/v1/images/generations"

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'images', 'carousel')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 剩余需要生成的图片提示词
REMAINING_IMAGES = [
    # 维修管理（剩余 4 张）
    ("maintenance_03.jpg", "专业维修团队工作场景，多名技术人员协作维修大型设备，现代化车间，蓝绿色渐变背景，团队协作，专业技能，8K 高清"),
    ("maintenance_04.jpg", "维修记录追溯系统，历史维修档案查询，维修过程照片，蓝色数据流渐变背景，知识管理，经验沉淀，专业摄影"),
    ("maintenance_05.jpg", "质量验收检测环节，精密检测仪器测量设备参数，实验室环境，蓝紫色渐变光效，严格质量标准，专业检测，高分辨率"),
    ("maintenance_06.jpg", "维修绩效分析报表，MTTR/MTBF 指标图表，维修效率趋势，蓝色科技渐变背景，绩效考核，持续改进，8K 商业摄影"),
    
    # 交易管理（6 张）
    ("transaction_01.jpg", "入库交易管理，货物卸货验收场景，叉车搬运，现代化仓库月台，蓝色科技渐变背景，规范入库流程，8K 专业摄影"),
    ("transaction_02.jpg", "出库交易流程，拣货员使用 PDA 拣选货物，传送带分拣，蓝紫色渐变光效，高效出库，物流管理，高分辨率"),
    ("transaction_03.jpg", "库存调拨作业，仓库间货物转运，货车装卸，蓝绿色渐变背景，灵活库存调配，供应链优化，专业摄影"),
    ("transaction_04.jpg", "交易追溯系统，区块链溯源技术，交易记录不可篡改，蓝色数据流渐变背景，完整追溯链，责任到人，8K 高清"),
    ("transaction_05.jpg", "库存调整操作，盘点差异处理，财务人员审核，现代化办公，蓝紫色渐变光效，账实相符，精细化管理，专业摄影"),
    ("transaction_06.jpg", "交易报表分析，出入库汇总图表，交易明细查询界面，蓝色科技渐变背景，数据驱动决策，智能分析，高分辨率"),
    
    # 采购管理（6 张）
    ("purchase_01.jpg", "智能采购申请界面，安全库存预警提示，自动生成采购建议，蓝色科技渐变背景，智能算法推荐，数智化采购，8K 摄影"),
    ("purchase_02.jpg", "供应商管理场景，商务洽谈会议，供应商评估打分，现代化会议室，蓝紫色渐变光效，合作伙伴关系，专业商业摄影"),
    ("purchase_03.jpg", "采购订单管理，电子合同签署，订单审批流程，数字化办公，蓝绿色渐变背景，规范采购行为，智能审批，8K 高清"),
    ("purchase_04.jpg", "采购合同管理，合同电子归档系统，履约进度跟踪，蓝色数据流渐变背景，合同全生命周期，风险管理，专业摄影"),
    ("purchase_05.jpg", "到货验收环节，质检人员抽样检测，精密仪器测量，实验室环境，蓝紫色渐变光效，严格质量控制，高分辨率"),
    ("purchase_06.jpg", "采购成本分析，价格趋势曲线图，成本对比分析，蓝色科技渐变背景，数据驱动决策，降低采购成本，8K 商业摄影"),
    
    # 报表统计（6 张）
    ("report_01.jpg", "库存统计报表，多维度库存分析，库存周转率图表，蓝色科技渐变背景，数据可视化，智能分析，8K 专业摄影"),
    ("report_02.jpg", "业务趋势分析，出入库趋势曲线，消耗预测模型，蓝紫色渐变光效，大数据分析，辅助决策，高分辨率商业摄影"),
    ("report_03.jpg", "成本分析报表，采购成本、库存成本、维修成本对比，饼图柱状图组合，蓝绿色渐变背景，全面成本管控，专业摄影"),
    ("report_04.jpg", "绩效考核报表，部门绩效排名，人员 KPI 指标，供应商评估，蓝色科技渐变背景，绩效管理，激励机制，8K 高清"),
    ("report_05.jpg", "数据可视化大屏，多维度图表展示，饼图柱状图折线图组合，蓝紫色渐变光效，商业智能 BI，数据分析，专业摄影"),
    ("report_06.jpg", "报表导出分享功能，Excel、PDF 格式导出，定时推送设置，蓝色数据流渐变背景，灵活数据分享，协同办公，8K 摄影")
]


def generate_image(filename, prompt, max_retries=5):
    """
    调用硅基流动 API 生成图片，带重试机制
    """
    print(f"\n正在生成：{filename}")
    print(f"提示词：{prompt[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Kwai-Kolors/Kolors",
        "prompt": prompt,
        "n": 1,
        "size": "1920x600",
        "quality": "hd"
    }
    
    for attempt in range(max_retries):
        try:
            print(f"尝试 {attempt + 1}/{max_retries}...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            
            # 处理 429 限流错误
            if response.status_code == 429:
                wait_time = (attempt + 1) * 15  # 指数退避：15s, 30s, 45s, 60s, 75s
                print(f"⚠ 遇到限流（429），等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            
            # 处理 500 服务器错误
            if response.status_code >= 500:
                wait_time = (attempt + 1) * 10
                print(f"⚠ 服务器错误（{response.status_code}），等待{wait_time}秒...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            result = response.json()
            
            # 获取生成的图片 URL
            if "data" in result and len(result["data"]) > 0:
                image_url = result["data"][0]["url"]
                
                # 下载图片
                print("正在下载图片...")
                image_response = requests.get(image_url, timeout=60)
                image_response.raise_for_status()
                
                # 保存图片到本地
                output_path = os.path.join(OUTPUT_DIR, filename)
                with open(output_path, "wb") as f:
                    f.write(image_response.content)
                
                print(f"✓ 成功保存：{filename}")
                return True
            else:
                print(f"✗ API 返回数据异常")
                return False
                
        except requests.exceptions.Timeout:
            print(f"✗ 请求超时")
            if attempt < max_retries - 1:
                time.sleep(5)
            continue
        except requests.exceptions.RequestException as e:
            print(f"✗ 请求失败：{str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(5)
            continue
        except Exception as e:
            print(f"✗ 发生错误：{str(e)[:100]}")
            return False
    
    print(f"✗ 超过最大重试次数，跳过")
    return False


def main():
    """
    主函数：生成剩余图片
    """
    print("=" * 80)
    print("硅基流动 AI - 生成剩余轮播图图片")
    print("=" * 80)
    print(f"输出目录：{OUTPUT_DIR}")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"需要生成：{len(REMAINING_IMAGES)} 张图片")
    print("=" * 80)
    
    total = len(REMAINING_IMAGES)
    success = 0
    failed = 0
    
    for i, (filename, prompt) in enumerate(REMAINING_IMAGES, 1):
        # 检查是否已存在
        output_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(output_path):
            print(f"\n⏭ [{i}/{total}] 跳过已存在的：{filename}")
            success += 1
            continue
        
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(filename, prompt):
            success += 1
        else:
            failed += 1
        
        # 每张图片之间延迟，避免限流
        print("等待 3 秒...")
        time.sleep(3)
    
    print("\n" + "=" * 80)
    print("生成完成！")
    print("=" * 80)
    print(f"总计：{total} 张")
    print(f"成功：{success} 张")
    print(f"失败：{failed} 张")
    print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
