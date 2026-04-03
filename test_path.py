"""
测试路径问题
"""
import os
from flask import Flask

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/images'

# 模拟备件代码
part_code = 'SKFX-A-001-001-L4I'

# 测试不同的路径组合
print("测试路径组合：")
print(f"1. 相对路径：{app.config['UPLOAD_FOLDER']}")
print(f"   是否存在：{os.path.exists(app.config['UPLOAD_FOLDER'])}")

print(f"\n2. 使用 join: {os.path.join(app.config['UPLOAD_FOLDER'], part_code)}")
print(f"   是否存在：{os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], part_code))}")

# 使用绝对路径
abs_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
print(f"\n3. 绝对路径：{abs_path}")
print(f"   是否存在：{os.path.exists(abs_path)}")

part_dir = os.path.join(abs_path, part_code)
print(f"\n4. 完整路径：{part_dir}")
print(f"   是否存在：{os.path.exists(part_dir)}")

if os.path.exists(part_dir):
    print(f"\n5. 目录内容：{os.listdir(part_dir)}")
