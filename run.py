"""
应用启动入口
"""

import os
from dotenv import load_dotenv

# 加载环境变量
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import create_app

# 创建应用
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # 获取配置
    debug = app.config.get('DEBUG', False)
    host = '0.0.0.0' if not debug else '127.0.0.1'
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 80)
    print("备件管理系统启动")
    print("=" * 80)
    print(f"环境：{'开发' if debug else '生产'}")
    print(f"地址：http://{host}:{port}")
    print(f"调试模式：{'开启' if debug else '关闭'}")
    print("=" * 80)
    
    # 启动应用
    app.run(host=host, port=port, debug=debug)
