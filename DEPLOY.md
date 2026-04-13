# 备件管理系统 - 部署快速参考

## 架构概览

```
Internet
    │
  [ Nginx :80 ]          ← 反向代理 + 静态资源 + 负载均衡
    │          └── /static/react/  React SPA 产物（直接返回）
    │          └── /uploads/       上传文件（直接返回）
    ├── /api/*  ──────────────────────────────────────────┐
    └── /*      ──────────────────────────────────────────┤
                                                          ▼
                        [ Flask/Gunicorn :5000 ] × N      ← 可横向扩展
                        (worker_class=sync, workers=CPU×2+1)
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
              [ MySQL :3306 ]             [ Redis :6379 ]
```

## 快速启动（本地开发）

```bash
# 1. 复制并编辑环境变量
cp .env.example .env
# 编辑 .env，填写 SECRET_KEY、数据库密码等

# 2. 启动所有服务（单实例）
docker compose up -d

# 3. 查看日志
docker compose logs -f backend

# 4. 访问
open http://localhost
```

## 生产部署

```bash
# 构建镜像
docker compose build

# 启动（后端 2 实例）
BACKEND_REPLICAS=2 docker compose up -d

# 横向扩展后端到 3 实例（零停机）
docker compose up -d --no-deps --scale backend=3 backend
```

## CI/CD 流水线

| 阶段 | 触发条件 | 说明 |
|------|---------|------|
| lint-backend | 所有 PR/push | flake8 + bandit |
| lint-frontend | 所有 PR/push | ESLint + Vite 构建验证 |
| test-backend | lint 通过后 | pytest（MySQL 服务容器） |
| build-push | main 分支 push | 构建并推送 Docker 镜像到 GHCR |
| deploy-staging | build 成功后 | 自动部署预发环境 |
| deploy-production | staging 部署后 | **需手动审批**（GitHub Environments） |

## GitHub Secrets 配置

```
SECRET_KEY              Flask 密钥
STAGING_HOST            预发服务器 IP
STAGING_USER            SSH 用户名
STAGING_SSH_KEY         SSH 私钥
PROD_HOST               生产服务器 IP
PROD_USER               SSH 用户名
PROD_SSH_KEY            SSH 私钥
```

## 横向扩展原则

- **无状态后端**：Session 存储在 Redis，上传文件挂载共享卷
- **Nginx upstream**：`least_conn` 算法 + Docker 内部 DNS 解析多实例
- **健康检查**：`GET /health` → 200 OK（验证 DB + Redis 可达性）
- **优雅重启**：`gunicorn graceful_timeout=30s`，滚动重启不丢请求
