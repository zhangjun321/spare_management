"""
Gunicorn 生产配置
支持横向扩展：多 worker 进程 + 异步 worker
"""

import multiprocessing
import os

# ── 绑定地址 ──────────────────────────────────────────────
bind = "0.0.0.0:5000"

# ── Worker 进程数（CPU核数×2+1，支持横向扩展） ────────────
# 容器化部署时可通过环境变量 GUNICORN_WORKERS 覆盖
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# ── Worker 类型 ────────────────────────────────────────────
# gevent 异步 worker，处理高并发 IO
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")

# 每个 worker 的线程数（sync worker 使用多线程）
threads = int(os.environ.get("GUNICORN_THREADS", 2))

# ── 超时配置 ────────────────────────────────────────────────
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))      # worker 超时（秒）
keepalive = 5                                                # keep-alive 连接保持时间
graceful_timeout = 30                                        # 优雅关闭超时

# ── 连接队列 ────────────────────────────────────────────────
backlog = 2048

# ── 日志配置 ────────────────────────────────────────────────
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")      # "-" 表示 stdout
errorlog  = os.environ.get("GUNICORN_ERROR_LOG", "-")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ── 进程管理 ────────────────────────────────────────────────
preload_app = True           # 预加载应用（减少启动时间，节省内存，COW 优化）
max_requests = 1000          # worker 处理 N 个请求后自动重启（防内存泄漏）
max_requests_jitter = 100    # 加入随机抖动，避免所有 worker 同时重启

# ── 环境变量 ────────────────────────────────────────────────
raw_env = [
    f"FLASK_ENV={os.environ.get('FLASK_ENV', 'production')}",
]

# ── 钩子函数 ────────────────────────────────────────────────
def on_starting(server):
    server.log.info("备件管理系统 Gunicorn 启动中...")

def worker_exit(server, worker):
    server.log.info(f"Worker {worker.pid} 退出")
