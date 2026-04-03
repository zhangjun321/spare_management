import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 获取API Key
api_key = os.getenv("BAIDU_API_KEY")

print("=" * 50)
print("使用OpenAI SDK测试百度千帆文生图")
print("=" * 50)
print(f"使用的API Key: {api_key}")
print()

# 创建OpenAI客户端
client = OpenAI(
    base_url='https://qianfan.baidubce.com/v2',
    api_key=api_key
)

print("测试文生图功能 (qwen-image)")
print("-" * 50)
try:
    response = client.images.generate(
        model="qwen-image",
        prompt="生成三张苹果手机的正面侧面和详细图",
        size="1024x768",
        n=1,
        extra_body={
            "steps": 50,
            "guidance": 4,
            "negative_prompt": "",
            "prompt_extend": True
        }
    )
    
    print("[SUCCESS] 文生图测试成功!")
    print("响应:", response)
    
    # 保存图片
    if response.data and len(response.data) > 0:
        import base64
        import requests
        
        image_url = response.data[0].url
        if image_url:
            # 下载图片
            image_response = requests.get(image_url)
            with open("test_qwen_image.png", "wb") as f:
                f.write(image_response.content)
            print("图片已保存为: test_qwen_image.png")
            
except Exception as e:
    print(f"[ERROR] 文生图测试失败: {str(e)}")
    import traceback
    print("详细错误信息:")
    print(traceback.format_exc())

print()
print("=" * 50)
print("测试完成")
print("=" * 50)
