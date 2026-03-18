# -*- coding: utf-8 -*-
"""
使用硅基流动 API 生成轮播图图片
为每个页面生成 6 张高质量、专业、有渐变背景的图片
"""

import os
import requests
import base64
from datetime import datetime

# 硅基流动 API 配置
API_KEY = "sk-ojhphrjqyigzgskcackiaixmsznscynmhydoiayelgpmmitn"
API_URL = "https://api.siliconflow.cn/v1/images/generations"

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'images', 'carousel')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 每个页面的图片生成提示词（6 张/页面）
PAGE_PROMPTS = {
    "spare_parts": [
        {
            "filename": "spare_parts_01.jpg",
            "prompt": "现代化智能仓储内部，高大的自动化立体仓库货架，整齐排列的工业备件，蓝色科技渐变背景，专业摄影，高分辨率，8K，工业 4.0，数智化管理"
        },
        {
            "filename": "spare_parts_02.jpg",
            "prompt": "工作人员使用扫码枪扫描备件条码，特写镜头，蓝紫色渐变光效，现代化仓库环境，专业工作场景，高清摄影，数智化追溯系统"
        },
        {
            "filename": "spare_parts_03.jpg",
            "prompt": "质检人员检查工业备件质量，精密测量仪器，实验室环境，蓝色科技渐变背景，专业严谨，高分辨率，质量控制流程"
        },
        {
            "filename": "spare_parts_04.jpg",
            "prompt": "自动化分拣流水线，传送带上的工业零件，机械臂自动分拣，蓝绿色渐变光效，现代化工厂，智能制造，8K 高清"
        },
        {
            "filename": "spare_parts_05.jpg",
            "prompt": "二维码追溯系统界面，扫描设备特写，数字孪生技术，蓝色数据流渐变背景，科技感，工业物联网，高分辨率商业摄影"
        },
        {
            "filename": "spare_parts_06.jpg",
            "prompt": "仓库管理员使用平板电脑进行库存盘点，数字化管理系统界面，蓝紫色渐变光效，现代化仓储，智能库存管理，专业摄影"
        }
    ],
    "dashboard": [
        {
            "filename": "dashboard_01.jpg",
            "prompt": "智能仓储管理控制中心，大型数据可视化屏幕，实时监控库存数据，蓝色科技渐变背景，指挥大厅，数智化驾驶舱，8K 高清"
        },
        {
            "filename": "dashboard_02.jpg",
            "prompt": "数据可视化大屏，多维度分析图表，动态数据流，蓝紫色渐变背景，商业智能 BI，数据分析仪表盘，专业摄影，高分辨率"
        },
        {
            "filename": "dashboard_03.jpg",
            "prompt": "工业设备监控中心，多屏幕显示设备运行状态，物联网传感器数据，蓝色科技光效，智能制造监控系统，8K 专业摄影"
        },
        {
            "filename": "dashboard_04.jpg",
            "prompt": "供应链采购管理界面，全球供应商网络地图，数据连线可视化，蓝绿色渐变背景，数字化供应链，智能采购系统，高清商业摄影"
        },
        {
            "filename": "dashboard_05.jpg",
            "prompt": "现代化办公团队协作场景，开放式办公区，多屏幕工作站，蓝色渐变光效，高效团队合作，专业办公环境，高分辨率"
        },
        {
            "filename": "dashboard_06.jpg",
            "prompt": "移动办公场景，平板电脑显示管理系统界面，远程监控仓库，蓝紫色科技渐变背景，灵活办公，数智化移动应用，8K 摄影"
        }
    ],
    "warehouse": [
        {
            "filename": "warehouse_01.jpg",
            "prompt": "智能立体仓库全景，高层自动化货架系统，AGV 机器人穿梭其中，蓝色科技渐变背景，现代化物流仓储，8K 高清摄影"
        },
        {
            "filename": "warehouse_02.jpg",
            "prompt": "仓库货架管理系统，RFID 标签特写，智能货位识别，蓝紫色渐变光效，物联网技术应用，专业仓储管理，高分辨率"
        },
        {
            "filename": "warehouse_03.jpg",
            "prompt": "AGV 搬运机器人自动运输货物，智能导航系统，现代化仓库地面，蓝绿色科技渐变背景，无人化物流，机器人自动化，8K 摄影"
        },
        {
            "filename": "warehouse_04.jpg",
            "prompt": "温湿度监控系统界面，传感器网络，环境数据实时显示，蓝色数据流渐变背景，智能环境监控，仓储安全保障，专业摄影"
        },
        {
            "filename": "warehouse_05.jpg",
            "prompt": "自动化分拣线高速运行，包裹智能分类，机械臂精准操作，蓝紫色渐变光效，现代物流分拣中心，高效率作业，8K 高清"
        },
        {
            "filename": "warehouse_06.jpg",
            "prompt": "仓储数据报表分析，大屏幕显示库存周转率图表，数据可视化，蓝色科技渐变背景，智能分析决策，专业商业摄影"
        }
    ],
    "equipment": [
        {
            "filename": "equipment_01.jpg",
            "prompt": "工业设备档案管理系统，设备三维模型展示，数字孪生技术，蓝色科技渐变背景，全生命周期管理，8K 专业摄影"
        },
        {
            "filename": "equipment_02.jpg",
            "prompt": "设备运行监控大屏，实时参数曲线图，异常预警提示，蓝紫色渐变光效，工业物联网监控，智能制造，高分辨率"
        },
        {
            "filename": "equipment_03.jpg",
            "prompt": "预防性保养计划界面，设备维护日历，智能提醒系统，蓝绿色渐变背景，预测性维护，设备健康管理，专业摄影"
        },
        {
            "filename": "equipment_04.jpg",
            "prompt": "工程师使用平板电脑进行设备点巡检，检查清单界面，现代化车间，蓝色科技渐变背景，标准化巡检流程，8K 高清"
        },
        {
            "filename": "equipment_05.jpg",
            "prompt": "设备故障分析报表，故障树分析图，历史数据统计，蓝紫色渐变光效，可靠性工程，维修决策支持，专业商业摄影"
        },
        {
            "filename": "equipment_06.jpg",
            "prompt": "设备备件关联图，BOM 结构可视化，备件库存联动，蓝色数据流渐变背景，智能备件管理，数智化系统，高分辨率"
        }
    ],
    "maintenance": [
        {
            "filename": "maintenance_01.jpg",
            "prompt": "维修工单管理界面，工单流转流程图，状态实时跟踪，蓝色科技渐变背景，闭环管理，智能工单系统，8K 专业摄影"
        },
        {
            "filename": "maintenance_02.jpg",
            "prompt": "快速响应维修场景，维修人员携带工具包快速赶赴现场，动态模糊效果，蓝紫色渐变光效，紧急维修，专业服务，高清摄影"
        },
        {
            "filename": "maintenance_03.jpg",
            "prompt": "专业维修团队工作场景，多名技术人员协作维修大型设备，现代化车间，蓝绿色渐变背景，团队协作，专业技能，8K 高清"
        },
        {
            "filename": "maintenance_04.jpg",
            "prompt": "维修记录追溯系统，历史维修档案查询，维修过程照片，蓝色数据流渐变背景，知识管理，经验沉淀，专业摄影"
        },
        {
            "filename": "maintenance_05.jpg",
            "prompt": "质量验收检测环节，精密检测仪器测量设备参数，实验室环境，蓝紫色渐变光效，严格质量标准，专业检测，高分辨率"
        },
        {
            "filename": "maintenance_06.jpg",
            "prompt": "维修绩效分析报表，MTTR/MTBF 指标图表，维修效率趋势，蓝色科技渐变背景，绩效考核，持续改进，8K 商业摄影"
        }
    ],
    "transaction": [
        {
            "filename": "transaction_01.jpg",
            "prompt": "入库交易管理，货物卸货验收场景，叉车搬运，现代化仓库月台，蓝色科技渐变背景，规范入库流程，8K 专业摄影"
        },
        {
            "filename": "transaction_02.jpg",
            "prompt": "出库交易流程，拣货员使用 PDA 拣选货物，传送带分拣，蓝紫色渐变光效，高效出库，物流管理，高分辨率"
        },
        {
            "filename": "transaction_03.jpg",
            "prompt": "库存调拨作业，仓库间货物转运，货车装卸，蓝绿色渐变背景，灵活库存调配，供应链优化，专业摄影"
        },
        {
            "filename": "transaction_04.jpg",
            "prompt": "交易追溯系统，区块链溯源技术，交易记录不可篡改，蓝色数据流渐变背景，完整追溯链，责任到人，8K 高清"
        },
        {
            "filename": "transaction_05.jpg",
            "prompt": "库存调整操作，盘点差异处理，财务人员审核，现代化办公，蓝紫色渐变光效，账实相符，精细化管理，专业摄影"
        },
        {
            "filename": "transaction_06.jpg",
            "prompt": "交易报表分析，出入库汇总图表，交易明细查询界面，蓝色科技渐变背景，数据驱动决策，智能分析，高分辨率"
        }
    ],
    "purchase": [
        {
            "filename": "purchase_01.jpg",
            "prompt": "智能采购申请界面，安全库存预警提示，自动生成采购建议，蓝色科技渐变背景，智能算法推荐，数智化采购，8K 摄影"
        },
        {
            "filename": "purchase_02.jpg",
            "prompt": "供应商管理场景，商务洽谈会议，供应商评估打分，现代化会议室，蓝紫色渐变光效，合作伙伴关系，专业商业摄影"
        },
        {
            "filename": "purchase_03.jpg",
            "prompt": "采购订单管理，电子合同签署，订单审批流程，数字化办公，蓝绿色渐变背景，规范采购行为，智能审批，8K 高清"
        },
        {
            "filename": "purchase_04.jpg",
            "prompt": "采购合同管理，合同电子归档系统，履约进度跟踪，蓝色数据流渐变背景，合同全生命周期，风险管理，专业摄影"
        },
        {
            "filename": "purchase_05.jpg",
            "prompt": "到货验收环节，质检人员抽样检测，精密仪器测量，实验室环境，蓝紫色渐变光效，严格质量控制，高分辨率"
        },
        {
            "filename": "purchase_06.jpg",
            "prompt": "采购成本分析，价格趋势曲线图，成本对比分析，蓝色科技渐变背景，数据驱动决策，降低采购成本，8K 商业摄影"
        }
    ],
    "report": [
        {
            "filename": "report_01.jpg",
            "prompt": "库存统计报表，多维度库存分析，库存周转率图表，蓝色科技渐变背景，数据可视化，智能分析，8K 专业摄影"
        },
        {
            "filename": "report_02.jpg",
            "prompt": "业务趋势分析，出入库趋势曲线，消耗预测模型，蓝紫色渐变光效，大数据分析，辅助决策，高分辨率商业摄影"
        },
        {
            "filename": "report_03.jpg",
            "prompt": "成本分析报表，采购成本、库存成本、维修成本对比，饼图柱状图组合，蓝绿色渐变背景，全面成本管控，专业摄影"
        },
        {
            "filename": "report_04.jpg",
            "prompt": "绩效考核报表，部门绩效排名，人员 KPI 指标，供应商评估，蓝色科技渐变背景，绩效管理，激励机制，8K 高清"
        },
        {
            "filename": "report_05.jpg",
            "prompt": "数据可视化大屏，多维度图表展示，饼图柱状图折线图组合，蓝紫色渐变光效，商业智能 BI，数据分析，专业摄影"
        },
        {
            "filename": "report_06.jpg",
            "prompt": "报表导出分享功能，Excel、PDF 格式导出，定时推送设置，蓝色数据流渐变背景，灵活数据分享，协同办公，8K 摄影"
        }
    ]
}


def generate_image(prompt, filename, max_retries=3):
    """
    调用硅基流动 API 生成图片，带重试机制
    """
    print(f"\n正在生成：{filename}")
    print(f"提示词：{prompt}")
    
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
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            
            # 处理 429 限流错误
            if response.status_code == 429:
                wait_time = (attempt + 1) * 10  # 指数退避：10s, 20s, 30s
                print(f"⚠ 遇到限流（429），等待{wait_time}秒后重试...（第{attempt + 1}次）")
                import time
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            result = response.json()
            
            # 获取生成的图片 URL
            if "data" in result and len(result["data"]) > 0:
                image_url = result["data"][0]["url"]
                
                # 下载图片
                image_response = requests.get(image_url, timeout=60)
                image_response.raise_for_status()
                
                # 保存图片到本地
                output_path = os.path.join(OUTPUT_DIR, filename)
                with open(output_path, "wb") as f:
                    f.write(image_response.content)
                
                print(f"✓ 图片已保存：{output_path}")
                return True
            else:
                print(f"✗ 生成失败：API 返回数据异常")
                print(f"响应内容：{result}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"✗ 请求超时，请检查网络连接")
            if attempt < max_retries - 1:
                print(f"等待 5 秒后重试...")
                import time
                time.sleep(5)
            continue
        except requests.exceptions.RequestException as e:
            print(f"✗ 请求失败：{str(e)}")
            if attempt < max_retries - 1:
                print(f"等待 5 秒后重试...")
                import time
                time.sleep(5)
            continue
        except Exception as e:
            print(f"✗ 发生错误：{str(e)}")
            return False
    
    print(f"✗ 超过最大重试次数，跳过此图片")
    return False


def main():
    """
    主函数：生成所有轮播图图片
    """
    print("=" * 60)
    print("硅基流动 AI 轮播图图片生成工具")
    print("=" * 60)
    print(f"输出目录：{OUTPUT_DIR}")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    total_count = 0
    success_count = 0
    
    # 遍历每个页面
    for page_name, images in PAGE_PROMPTS.items():
        print(f"\n{'='*60}")
        print(f"正在处理：{page_name} 页面")
        print(f"{'='*60}")
        
        for image_info in images:
            total_count += 1
            filename = image_info["filename"]
            prompt = image_info["prompt"]
            
            # 检查图片是否已存在
            output_path = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(output_path):
                print(f"\n⏭ 跳过已存在的图片：{filename}")
                success_count += 1
                continue
            
            if generate_image(prompt, filename):
                success_count += 1
            
            # 添加延迟，避免 API 限流
            import time
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)
    print(f"总图片数：{total_count}")
    print(f"成功：{success_count}")
    print(f"失败：{total_count - success_count}")
    print(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
