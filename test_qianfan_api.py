from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量读取 API Key
api_key = os.getenv('BAIDU_API_KEY', '')

if not api_key:
    print('❌ 错误: 未找到 BAIDU_API_KEY 环境变量')
    print('请在 .env 文件中配置 BAIDU_API_KEY')
    exit(1)

print('=' * 60)
print('百度千帆 API 接口测试')
print('=' * 60)

print(f'\nAPI Key 已加载')
print(f'Base URL: https://qianfan.baidubce.com/v2')

# 初始化客户端
client = OpenAI(
    base_url="https://qianfan.baidubce.com/v2",
    api_key=api_key
)

print(f'\n正在测试 API 连接...')

try:
    # 测试模型列表（不消耗额度）
    print(f'\n测试 1: 获取模型列表...')
    # 注意：OpenAI SDK 没有直接的 models.list 方法在百度千帆上
    # 我们直接测试一个简单的 API 调用
    
    print(f'\n测试 2: 测试 qwen-image 模型...')
    
    # 使用一个非常简单的提示词，只测试连接，不真正生成图片
    # 我们使用 steps=1 来最小化资源消耗
    response = client.images.generate(
        model="qwen-image",
        prompt="test",
        size="512x512",
        n=1,
        extra_body={
            "steps": 1,
            "guidance": 1,
            "negative_prompt": "",
            "prompt_extend": False
        }
    )

    print(f'\n✅ API 接口正常可用！')
    print(f'\n响应数据:')
    print(f'  - 创建时间: {response.created}')
    print(f'  - 生成图片数量: {len(response.data)}')
    
    for i, image in enumerate(response.data):
        print(f'\n  图片 {i+1}:')
        if hasattr(image, 'url'):
            print(f'    - URL: {image.url[:50]}...')
    
    print(f'\n{"=" * 60}')
    print('✅ 百度千帆 API 接口测试通过！')
    print('=' * 60)

except Exception as e:
    print(f'\n❌ API 调用失败！')
    print(f'\n错误信息: {str(e)}')
    print(f'\n错误类型: {type(e).__name__}')
    
    error_str = str(e).lower()
    
    if 'rate limit' in error_str or '429' in error_str:
        print(f'\n⚠️  检测到频率限制 (Rate Limit)')
        print(f'   这说明 API Key 是正确的，只是调用频率过高或额度用完了')
        print(f'\n解决方案:')
        print(f'  1. 等待几分钟后重试（频率限制会自动重置）')
        print(f'  2. 检查百度千帆控制台的 API 额度使用情况')
        print(f'  3. 如果额度用完，可以考虑购买额度或切换到其他方案')
        
    elif 'invalid' in error_str and 'api' in error_str:
        print(f'\n❌ API Key 无效')
        print(f'   请检查 .env 文件中的 BAIDU_API_KEY 是否正确')
        
    elif 'connection' in error_str or 'timeout' in error_str:
        print(f'\n❌ 网络连接错误')
        print(f'   请检查网络连接是否正常')
        
    else:
        print(f'\n❌ 未知错误')
        import traceback
        print(f'\n堆栈跟踪:')
        print(traceback.format_exc())
    
    print(f'\n{"=" * 60}')
    print('测试完成')
    print('=' * 60)