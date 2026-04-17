"""
使用百度千帆 v2 API + OpenAI SDK 生成入库管理轮播图
"""
import sys
import os
import time
import base64
import requests

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 百度千帆 v2 API 配置
API_KEY = "bce-v3/ALTAK-06RS7waJjHzlq49W2wP9L/22ef1c83017f0c82f77bcf967d947eba4cc8df17"

# 初始化客户端
client = OpenAI(
    base_url='https://qianfan.baidubce.com/v2',
    api_key=API_KEY
)

# 入库管理 6 个场景的提示词
inbound_prompts = [
    {
        "filename": "inbound_01.jpg",
        "title": "高效入库协同",
        "prompt": "2K 高清摄影作品，现代智能仓库入库场景，自动化立体仓库，AGV 机器人正在搬运货物，传送带系统高效运转，仓库管理员使用手持终端扫描货物条码，背景是整齐的高层货架，蓝色和银色的金属质感，科技感十足，明亮的 LED 照明，景深效果，专业商业摄影，超高清细节，8K 分辨率，电影级调色"
    },
    {
        "filename": "inbound_02.jpg",
        "title": "批次追溯管理",
        "prompt": "2K 高清摄影作品，仓库批次管理场景，特写镜头展示货物上的 RFID 标签和二维码，背景虚化的现代化仓库，数字化追溯系统界面悬浮显示，蓝色科技感光效，货物包装箱整齐排列，扫码枪正在读取批次信息，未来感十足的仓储管理系统，专业商业摄影，精细细节，高分辨率"
    },
    {
        "filename": "inbound_03.jpg",
        "title": "智能收货分拣",
        "prompt": "2K 高清摄影作品，智能分拣中心，高速自动分拣机正在工作，包裹在传送带上快速移动，机械臂精准抓取货物，LED 显示屏显示分拣信息，现代化物流中心，干净明亮的环境，蓝色和白色主色调，科技感强烈，动态模糊效果展现速度感，专业工业摄影，超清画质"
    },
    {
        "filename": "inbound_04.jpg",
        "title": "质检流程闭环",
        "prompt": "2K 高清摄影作品，仓库质检区域，质检员正在使用精密仪器检测货物质量，现代化质检工作台，电脑屏幕显示质检数据和图表，背景是待检区和合格品区标识清晰，专业质检设备，明亮的无影灯照明，严谨的工作氛围，蓝色和白色主色调，商业摄影级别，高清晰度"
    },
    {
        "filename": "inbound_05.jpg",
        "title": "库位上架优化",
        "prompt": "2K 高清摄影作品，自动化立体仓库内部，堆垛机正在将货物精准放置到高层货架，智能库位分配系统界面展示，LED 指示灯显示库位状态，整齐划一的货架系统，银灰色金属质感，蓝色科技光带，现代物流科技感，仰视视角展现震撼效果，专业建筑摄影，超高分辨率"
    },
    {
        "filename": "inbound_06.jpg",
        "title": "实时入库看板",
        "prompt": "2K 高清摄影作品，仓库指挥中心，巨型 LED 显示屏墙展示实时入库数据看板，可视化图表和动态数据流，工作人员在监控台前工作，多屏幕显示系统，深色背景下蓝色和绿色的数据图表发光效果，科技感十足的智慧大脑概念，未来感场景，专业商业摄影，精细画质，8K 超清"
    }
]

def generate_image(prompt_text, output_path):
    """调用百度千帆 AI 生成图片"""
    
    try:
        print(f"  正在调用百度千帆文生图 API...")
        print(f"  提示词长度：{len(prompt_text)} 字符")
        
        response = client.images.generate(
            model="qwen-image",
            prompt=prompt_text,
            size="2048x1024",  # 2K 分辨率
            n=1,
            extra_body={
                "steps": 50,
                "guidance": 4,
                "negative_prompt": "模糊，低质量，失真，变形，文字，水印，签名，丑陋，粗糙，低分辨率，噪点，过曝，欠曝",
                "prompt_extend": True
            }
        )
        
        print(f"  API 响应：{response}")
        
        # 获取图片 URL
        if response.data and len(response.data) > 0:
            image_url = response.data[0].url
            print(f"  图片 URL: {image_url}")
            
            # 下载图片
            img_response = requests.get(image_url, timeout=60)
            if img_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"  ✅ 图片已保存：{output_path}")
                return True
            else:
                print(f"  ❌ 下载失败：{img_response.status_code}")
                return False
        else:
            print(f"  ❌ 生成失败：无图片数据")
            return False
            
    except Exception as e:
        print(f"  ❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("开始生成入库管理轮播图")
    print("=" * 80)
    
    # 输出目录
    output_dir = "app/static/images/carousel"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📋 将生成 {len(inbound_prompts)} 张图片")
    print(f"📁 保存目录：{output_dir}")
    print(f"🎨 分辨率：2048x1024 (2K)")
    print(f"🔑 使用百度千帆 v2 API")
    print(f"🤖 模型：qwen-image")
    print()
    
    # 生成每张图片
    success_count = 0
    for i, item in enumerate(inbound_prompts, 1):
        print(f"\n[{i}/{len(inbound_prompts)}] 生成：{item['title']}")
        print(f"提示词：{item['prompt'][:60]}...")
        
        output_path = os.path.join(output_dir, item['filename'])
        
        # 如果文件已存在，先删除
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"  已删除旧文件：{output_path}")
        
        # 生成图片
        if generate_image(item['prompt'], output_path):
            success_count += 1
            print(f"  ✨ 生成成功！")
        else:
            print(f"  ⚠️ 生成失败")
        
        # 避免请求过快，每次生成后等待 3 秒
        if i < len(inbound_prompts):
            time.sleep(3)
    
    print("\n" + "=" * 80)
    print(f"生成完成！成功：{success_count}/{len(inbound_prompts)}")
    print("=" * 80)
    
    if success_count > 0:
        print(f"\n✅ 成功生成 {success_count} 张图片，请在入库管理页面查看效果")
        print(f"📁 图片位置：{output_dir}")

if __name__ == "__main__":
    main()
