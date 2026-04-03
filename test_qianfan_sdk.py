import os
from dotenv import load_dotenv
import qianfan

# 加载环境变量
load_dotenv()

# 配置API Key
api_key = os.getenv("BAIDU_API_KEY")
os.environ["QIANFAN_ACCESS_KEY"] = api_key

print("=" * 50)
print("测试千帆SDK")
print("=" * 50)
print(f"使用的API Key: {api_key}")
print()

# 1. 测试文本对话功能
print("1. 测试文本对话功能 (ERNIE-3.5-8K)")
print("-" * 50)
try:
    chat_comp = qianfan.ChatCompletion()
    resp = chat_comp.do(
        model="ERNIE-3.5-8K",
        messages=[{
            "role": "user",
            "content": "你好，请简单介绍一下你自己"
        }]
    )
    print("✅ 文本对话测试成功!")
    print("回复:", resp["result"])
except Exception as e:
    print(f"❌ 文本对话测试失败: {str(e)}")

print()

# 2. 测试文生图功能
print("2. 测试文生图功能 (Stable-Diffusion-XL)")
print("-" * 50)
try:
    text2image = qianfan.Text2Image()
    resp = text2image.do(
        prompt="一只可爱的小猫坐在草地上",
        width=512,
        height=512,
        image_num=1,
        model="Stable-Diffusion-XL"
    )
    
    print("✅ 文生图测试成功!")
    print("任务ID:", resp.get("id", "N/A"))
    print("状态:", resp.get("status", "N/A"))
    
    # 保存图片
    if resp.get("data") and len(resp["data"]) > 0:
        import base64
        image_data = resp["data"][0]["b64_image"]
        with open("test_image_sdk.png", "wb") as f:
            f.write(base64.b64decode(image_data))
        print("图片已保存为: test_image_sdk.png")
except Exception as e:
    print(f"❌ 文生图测试失败: {str(e)}")
    import traceback
    print("详细错误信息:")
    print(traceback.format_exc())

print()
print("=" * 50)
print("测试完成")
print("=" * 50)
