"""
测试备件代码中的特殊字符
"""
import os

part_codes = [
    'SKFX-A-001-001-EHD',
    'FAGX-A-002-002-PWP',
    'NSKX-A-003-003-8ZP'
]

base_dir = r'D:\Trae\spare_management\uploads\images'

print("测试备件代码中的特殊字符...")
for code in part_codes:
    print(f"\n测试: {code}")
    
    # 测试创建目录
    try:
        part_dir = os.path.join(base_dir, code)
        print(f"  目录路径: {part_dir}")
        
        if not os.path.exists(part_dir):
            os.makedirs(part_dir, exist_ok=True)
            print(f"  目录创建成功")
        else:
            print(f"  目录已存在")
    except Exception as e:
        print(f"  错误: {str(e)}")
    
    # 测试路径拼接
    try:
        test_path = f"/uploads/images/{code}/thumbnail.jpg"
        print(f"  测试URL路径: {test_path}")
    except Exception as e:
        print(f"  错误: {str(e)}")

print("\n所有测试完成！")
