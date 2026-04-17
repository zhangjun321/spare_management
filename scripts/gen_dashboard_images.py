"""
为仓库仪表盘页面生成6张高分辨率科技感轮播图
风格：智能驾驶舱 / 数字孪生 / 暗色调科技蓝紫渐变
分辨率：2048x1152 (2K+, 16:9)
"""
import requests
import json
import os
import time

FULL_TOKEN = 'bce-v3/ALTAK-06RS7waJjHzlq49W2wP9L/22ef1c83017f0c82f77bcf967d947eba4cc8df17'
HEADERS = {'Content-Type': 'application/json', 'Authorization': f'Bearer {FULL_TOKEN}'}
URL = 'https://qianfan.baidubce.com/v2/images/generations'
OUT_DIR = 'app/static/images/carousel'

# 6张仪表盘风格轮播图提示词
# 风格：暗色调、蓝紫霓虹光、数字孪生、全息投影、科技感强
PROMPTS = [
    # dashboard_01: 智能仓库数字孪生全景
    (
        'dashboard_01.jpg',
        'Ultra high resolution 2K cinematic digital art, smart warehouse digital twin holographic visualization, '
        'dark atmospheric warehouse interior with glowing blue neon data overlays, floating 3D holographic shelf maps '
        'and inventory statistics panels in mid-air, real-time data streams with glowing particle effects, '
        'futuristic teal and purple gradient ambient lighting, dark background with bright neon blue holographic UI elements, '
        'ultra sharp 8K detail, sci-fi enterprise technology aesthetic, no people, deep atmospheric perspective, '
        'volumetric light rays through warehouse ceiling, photorealistic with digital effects'
    ),
    # dashboard_02: AI智能分析驾驶舱
    (
        'dashboard_02.jpg',
        'Ultra high resolution 2K digital art, AI-powered warehouse intelligence command center cockpit, '
        'massive curved holographic display wall showing real-time warehouse analytics dashboard, '
        'glowing neon blue and purple KPI charts, bar graphs, pie charts, line graphs floating in 3D space, '
        'deep dark room with dramatic blue ambient lighting, data visualization particles and flowing data streams, '
        'futuristic enterprise control room aesthetic, holographic UI panels, sharp ultra-detailed, '
        'cinematic composition, no people, sci-fi technology style'
    ),
    # dashboard_03: 实时库存监控大屏
    (
        'dashboard_03.jpg',
        'Ultra high resolution 2K cinematic render, smart inventory monitoring system visualization, '
        'dark warehouse space with giant transparent holographic inventory grid showing colored status indicators, '
        'green amber red glow status lights on shelving rack locations, real-time stock level bar charts '
        'projected in blue neon light, 3D warehouse floor plan overlay, glowing data numbers floating above shelves, '
        'dramatic dark background with vibrant neon accent lighting in blue cyan and orange, '
        'ultra sharp photorealistic render, no people, futuristic industrial style'
    ),
    # dashboard_04: 出入库流量智能看板
    (
        'dashboard_04.jpg',
        'Ultra high resolution 2K digital art, warehouse logistics flow intelligence dashboard visualization, '
        'dark atmospheric scene with glowing blue holographic flow charts and animated logistics pathways, '
        'inbound outbound freight flow diagram with neon arrows and particle streams, '
        'connected nodes graph showing supply chain network in blue and purple gradients, '
        'transparent 3D bar charts showing daily weekly statistics with glowing edges, '
        'dramatic cinematic dark background with volumetric blue light rays, ultra detailed sharp, '
        'futuristic enterprise data visualization, no people, sci-fi industrial aesthetic'
    ),
    # dashboard_05: 预警与异常智能检测
    (
        'dashboard_05.jpg',
        'Ultra high resolution 2K cinematic digital art, warehouse AI anomaly detection and alert system visualization, '
        'dark warehouse environment with dramatic red and orange warning holographic alert indicators '
        'projected on specific shelf locations, AI neural network visualization overlay with glowing connections, '
        'smart sensor data streams with amber warning pulses, predictive analytics forecast chart in blue neon, '
        'contrast of cool blue data interface with hot warning red orange accent lights, '
        'ultra sharp detailed render, futuristic enterprise safety technology, no people, '
        'cinematic depth of field, atmospheric dark sci-fi aesthetic'
    ),
    # dashboard_06: 数字化仓库运营全貌
    (
        'dashboard_06.jpg',
        'Ultra high resolution 2K cinematic render, next-generation smart warehouse operations center panoramic view, '
        'sweeping bird-eye architectural visualization of vast automated warehouse facility, '
        'glowing blue neon grid lines mapping every aisle and shelf zone, holographic status overlays on each zone, '
        'autonomous robot vehicles with blue light trails on floor, entire warehouse rendered in deep dark tones '
        'with vibrant cyan blue purple neon accent lighting, massive scale digital infrastructure, '
        'ultra sharp 8K photorealistic with digital holographic overlay effects, no people, '
        'futuristic logistics enterprise, God-view composition, sci-fi industrial masterpiece'
    ),
]


def generate_image(fname, prompt, attempt=1):
    print(f'[{attempt}] Generating {fname}...')
    data = {
        'model': 'flux.1-schnell',
        'prompt': prompt,
        'size': '2048x1152',
        'n': 1
    }
    try:
        resp = requests.post(URL, headers=HEADERS, json=data, timeout=90)
        r = resp.json()
        if 'data' in r and r['data']:
            img_url = r['data'][0].get('url', '')
            if img_url:
                img_resp = requests.get(img_url, timeout=60)
                out_path = os.path.join(OUT_DIR, fname)
                with open(out_path, 'wb') as f:
                    f.write(img_resp.content)
                size_kb = len(img_resp.content) // 1024
                print(f'  -> Saved {out_path} ({size_kb}KB)')
                return True
            else:
                print(f'  -> No URL in response: {r}')
        else:
            err = json.dumps(r, ensure_ascii=False)[:300]
            print(f'  -> Error: {err}')
            # 如果是内容过滤，用备用提示词
            if 'content_policy' in err or 'audit' in err.lower() or 'block' in err.lower():
                return 'blocked'
    except Exception as e:
        print(f'  -> Exception: {e}')
    return False


# 备用提示词（更简洁，避免过滤）
FALLBACK_PROMPTS = {
    'dashboard_01.jpg': (
        'Ultra high resolution 2K render, smart warehouse digital twin visualization, '
        'dark interior with blue neon holographic data overlays, floating 3D inventory panels, '
        'futuristic teal purple gradient lighting, sci-fi technology aesthetic, no people, photorealistic'
    ),
    'dashboard_02.jpg': (
        'Ultra high resolution 2K render, AI warehouse intelligence command center, '
        'massive holographic display wall with analytics charts and KPI dashboards, '
        'dark room with dramatic blue ambient lighting, data visualization, no people, futuristic'
    ),
    'dashboard_03.jpg': (
        'Ultra high resolution 2K render, smart inventory monitoring visualization, '
        'dark warehouse with holographic inventory grid and colored status indicators, '
        'real-time stock charts in blue neon light, 3D floor plan overlay, no people, futuristic'
    ),
    'dashboard_04.jpg': (
        'Ultra high resolution 2K render, warehouse logistics flow dashboard visualization, '
        'dark atmospheric scene with glowing blue holographic flow charts and logistics pathways, '
        'neon arrows and connected nodes graph, 3D bar charts with glowing edges, no people, futuristic'
    ),
    'dashboard_05.jpg': (
        'Ultra high resolution 2K render, warehouse AI monitoring system visualization, '
        'dark environment with warning indicator lights and sensor data streams, '
        'predictive analytics forecast chart in blue neon, dramatic dark sci-fi aesthetic, no people'
    ),
    'dashboard_06.jpg': (
        'Ultra high resolution 2K render, smart warehouse aerial panoramic view, '
        'vast automated warehouse facility with blue neon grid lines mapping aisles and zones, '
        'holographic status overlays, deep dark tones with cyan blue neon accent lighting, '
        'futuristic logistics, God-view composition, no people, photorealistic'
    ),
}


os.makedirs(OUT_DIR, exist_ok=True)

for fname, prompt in PROMPTS:
    result = generate_image(fname, prompt)
    if result == 'blocked':
        print(f'  -> Retrying with fallback prompt...')
        time.sleep(2)
        generate_image(fname, FALLBACK_PROMPTS.get(fname, prompt), attempt=2)
    elif not result:
        print(f'  -> Failed, retrying with fallback...')
        time.sleep(3)
        generate_image(fname, FALLBACK_PROMPTS.get(fname, prompt), attempt=2)
    time.sleep(2)

print('\nAll done!')
