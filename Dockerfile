# ============================================================
# 备件管理系统 - Flask 后端 Dockerfile
# 多阶段构建：builder 安装依赖，runtime 运行应用
# ============================================================

# ---------- Stage 1: 依赖安装 ----------
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装编译依赖（bcrypt / Pillow 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    default-libmysqlclient-dev \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---------- Stage 2: 运行时镜像 ----------
FROM python:3.11-slim AS runtime

# 运行时系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libmagic1 \
    default-libmysqlclient-dev \
 && rm -rf /var/lib/apt/lists/*

# 拷贝安装好的 Python 包
COPY --from=builder /install /usr/local

WORKDIR /app

# 拷贝应用代码（.dockerignore 负责过滤）
COPY . .

# 创建非 root 运行用户
RUN groupadd -r appuser && useradd -r -g appuser appuser \
 && mkdir -p /app/uploads /app/logs \
 && chown -R appuser:appuser /app

USER appuser

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# 启动命令：使用 gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
