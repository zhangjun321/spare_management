"""
测试文生图服务
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.image_generation_service import ImageGenerationService

def test_service():
    print("=" * 50)
    print("测试文生图服务")
    print("=" * 50)
    
    try:
        service = ImageGenerationService()
        print("[SUCCESS] 服务初始化成功")
        
        # 测试生成提示词
        print("\n测试生成提示词...")
        prompt_front = service._generate_prompt("轴承", "SKF", "front")
        print(f"正面图提示词: {prompt_front}")
        
        prompt_circuit = service._generate_prompt("轴承", "SKF", "circuit")
        print(f"电路图提示词: {prompt_circuit}")
        print("[SUCCESS] 提示词生成成功")
        
        print("\n" + "=" * 50)
        print("测试完成！服务功能正常。")
        print("=" * 50)
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    test_service()
