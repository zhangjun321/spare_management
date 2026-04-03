# -*- coding: utf-8 -*-
"""最简单的启动脚本"""

import sys
import io

# 强制使用 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("Starting server...")

from app import create_app

app = create_app()

print("=" * 80)
print("Spare Parts Management System")
print("=" * 80)
print("Environment: Development")
print("URL: http://127.0.0.1:5000")
print("Debug Mode: ON")
print("=" * 80)

app.run(host='127.0.0.1', port=5000, debug=True)
