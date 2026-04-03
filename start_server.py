# -*- coding: utf-8 -*-
"""简单的服务器启动脚本"""

import sys
import os

print("=" * 80)
print("开始启动服务器...")
print("=" * 80)
print(f"Python 版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print("=" * 80)

try:
    from app import create_app
    print("[OK] 成功导入 create_app")
    
    app = create_app()
    print("[OK] 成功创建应用")
    
    print("=" * 80)
    print("备件管理系统启动")
    print("=" * 80)
    print(f"环境：{'开发' if app.config.get('DEBUG', False) else '生产'}")
    print(f"地址：http://127.0.0.1:5000")
    print(f"调试模式：{'开启' if app.config.get('DEBUG', False) else '关闭'}")
    print("=" * 80)
    
    # 启动应用
    app.run(host='127.0.0.1', port=5000, debug=True)
    
except Exception as e:
    print(f"[ERROR] 错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
