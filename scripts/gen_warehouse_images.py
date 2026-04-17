"""批量生成仓库管理轮播图 - 使用百度千帆 flux.1-schnell 模型"""
import requests
import json
import os
import time

FULL_TOKEN = "bce-v3/ALTAK-06RS7waJjHzlq49W2wP9L/22ef1c83017f0c82f77bcf967d947eba4cc8df17"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {FULL_TOKEN}"}
URL = "https://qianfan.baidubce.com/v2/images/generations"
OUT_DIR = "app/static/images/carousel"

# 6张仓库管理轮播图提示词 - 与spare_parts专业商业摄影风格一致
PROMPTS = [
    (
        "warehouse_01.jpg",
        "Ultra high resolution commercial photography, panoramic view of a modern intelligent warehouse facility, "
        "multiple rows of tall metal shelving racks up to ceiling, organized boxes and spare parts on shelves with "
        "barcoded labels, professional warehouse staff in safety yellow vests scanning inventory with handheld devices, "
        "bright industrial LED lighting from above, clean concrete floor with yellow safety markings, forklift in "
        "background, wide angle lens, photorealistic, sharp and detailed, enterprise industrial setting, no blur, "
        "high clarity"
    ),
    (
        "warehouse_02.jpg",
        "Ultra high resolution commercial photography, warehouse shelf location management system close-up, "
        "rows of metal racks with clear alphanumeric location codes A1-Z99 on yellow labels, neatly organized "
        "spare parts boxes in different sizes, professional warehouse worker using tablet to scan QR codes on shelf "
        "locations, barcode scanners, warehouse management system display on screen, bright industrial lighting, "
        "photorealistic, ultra sharp details, professional industrial style, high clarity"
    ),
    (
        "warehouse_03.jpg",
        "Ultra high resolution commercial photography, warehouse receiving and inbound operations scene, "
        "professional workers in orange safety vests unloading boxes from delivery truck at loading dock, "
        "industrial shelving racks in background, boxes with shipping labels being checked on receiving table, "
        "supervisor reviewing paperwork on clipboard, bright warehouse lighting, organized professional workflow, "
        "photorealistic, sharp facial details on workers, commercial industrial style, high clarity"
    ),
    (
        "warehouse_04.jpg",
        "Ultra high resolution commercial photography, warehouse order fulfillment and outbound picking operations, "
        "professional worker in safety gear picking spare parts from organized tall shelving racks, handheld barcode "
        "scanner glowing screen, parts sorted on packing table, boxes being labeled for shipping, modern warehouse "
        "background with high ceilings, bright LED lighting, photorealistic, sharp crisp details, enterprise "
        "warehouse professional style, high clarity"
    ),
    (
        "warehouse_05.jpg",
        "Ultra high resolution commercial photography, warehouse annual inventory audit and cycle counting scene, "
        "professional team of workers systematically counting and verifying spare parts on tall shelving racks, "
        "tablet devices displaying live inventory data with charts, barcode scanners, organized labeled boxes, "
        "supervisor with digital clipboard, large warehouse space with industrial lighting overhead, photorealistic, "
        "sharp clear details, commercial professional style, high clarity"
    ),
    (
        "warehouse_06.jpg",
        "Ultra high resolution commercial photography, modern smart warehouse management control center, "
        "large curved digital display screens showing real-time WMS dashboard with inventory statistics charts and "
        "3D warehouse heat maps, warehouse operations manager and analyst reviewing data at workstations with "
        "multiple monitors, automated alert panels, clean modern industrial office environment, professional attire, "
        "photorealistic, sharp facial and screen details, enterprise digital transformation style, high clarity"
    ),
]


def generate_image(fname, prompt):
    data = {
        "model": "flux.1-schnell",
        "prompt": prompt,
        "size": "1792x1024",
        "n": 1,
    }
    resp = requests.post(URL, headers=HEADERS, json=data, timeout=60)
    r = resp.json()
    if "data" in r and r["data"]:
        img_url = r["data"][0].get("url", "")
        if img_url:
            img_resp = requests.get(img_url, timeout=30)
            out_path = os.path.join(OUT_DIR, fname)
            with open(out_path, "wb") as f:
                f.write(img_resp.content)
            return out_path, len(img_resp.content)
    raise ValueError(f"No image in response: {json.dumps(r, ensure_ascii=False)[:200]}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, (fname, prompt) in enumerate(PROMPTS, 1):
        print(f"[{i}/6] Generating {fname}...", flush=True)
        try:
            out_path, size = generate_image(fname, prompt)
            print(f"  -> Saved: {out_path} ({size // 1024}KB)", flush=True)
        except Exception as e:
            print(f"  -> ERROR: {e}", flush=True)
        if i < len(PROMPTS):
            time.sleep(2)
    print("All done!")


if __name__ == "__main__":
    main()
