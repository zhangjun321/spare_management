<<<<<<< HEAD
# 备件管理系统 (Spare Management System)

专业的备件管理系统，基于 Flask 框架开发，支持多用户权限管理。

## 项目结构

```
spare_management/
├── app/                      # 应用主目录
│   ├── __init__.py          # 应用工厂
│   ├── config.py            # 配置文件
│   ├── extensions.py        # 扩展初始化
│   ├── models/              # 数据模型
│   ├── routes/              # 路由
│   ├── services/            # 业务逻辑
│   ├── forms/               # 表单
│   ├── templates/           # 模板
│   ├── static/              # 静态资源
│   ├── utils/               # 工具函数
│   └── errors/              # 错误处理
├── scripts/                  # 脚本文件
│   ├── init_db.py           # 数据库初始化脚本
│   └── create_tables.sql    # SQL 建表脚本
├── migrations/               # 数据库迁移
├── tests/                    # 测试文件
├── logs/                     # 日志目录
├── .env                      # 环境变量配置
├── .gitignore               # Git 忽略文件
├── requirements.txt         # Python 依赖
└── run.py                   # 应用启动入口
```

## 安装步骤

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+
- Redis (可选，用于缓存)

### 2. 安装 Python 依赖

```bash
cd spare_management
pip install -r requirements.txt
```

### 3. 配置环境变量

编辑 `.env` 文件:

```env
# Flask 配置
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=spare_parts_db
MYSQL_USER=root
MYSQL_PASSWORD=你的 MySQL 密码

# 其他配置
DEBUG=True
```

### 4. 初始化数据库

**重要**: 由于安全原因，需要手动执行数据库初始化。

#### 方法一：使用 MySQL Workbench 或命令行

打开 MySQL Workbench 或命令行工具，执行:

```sql
-- 1. 创建数据库
CREATE DATABASE spare_parts_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 使用数据库
USE spare_parts_db;

-- 3. 执行 SQL 脚本
-- 将 scripts/create_tables.sql 文件内容复制粘贴执行
```

#### 方法二：使用提供的 Python 脚本

```bash
# 确保 .env 文件中的数据库密码正确
python scripts/init_db.py
```

如果提示密码错误，请修改 `.env` 文件中的 `MYSQL_PASSWORD`。

### 5. 启动应用

```bash
# 开发模式
python run.py

# 或者使用 Flask 命令
flask run
```

访问 http://localhost:5000

### 6. 默认管理员账户

- 用户名：`admin`
- 密码：`admin123`

**首次登录后请立即修改密码!**

## 功能模块

### 核心模块

- ✅ 用户认证与权限管理
- ✅ 备件管理
- ✅ 批次管理
- ✅ 仓库管理
- ✅ 交易管理 (入库/出库)
- ✅ 设备管理
- ✅ 维修管理
- ✅ 采购管理
- ✅ 供应商管理
- ✅ 报表统计

### 辅助模块

- ✅ 告警管理
- ✅ 通知系统
- ✅ 日志管理
- ✅ API 接口

## 数据库表

系统共包含 29 个数据表:

### 用户与权限 (4 个)
- user - 用户表
- role - 角色表
- department - 部门表
- user_role - 用户角色关联表

### 备件管理 (3 个)
- spare_part - 备件表
- category - 分类表
- batch - 批次表

### 仓库管理 (3 个)
- warehouse - 仓库表
- warehouse_location - 库位表
- serial_number - 序列号表

### 交易管理 (2 个)
- transaction - 交易表
- transaction_detail - 交易明细表

### 设备管理 (1 个)
- equipment - 设备表

### 维修管理 (4 个)
- maintenance_order - 维修工单表
- maintenance_task - 维修任务表
- maintenance_record - 维修记录表
- maintenance_cost - 维修成本表

### 采购管理 (4 个)
- purchase_plan - 采购计划表
- purchase_request - 采购申请表
- purchase_order - 采购订单表
- purchase_quote - 报价表

### 供应商管理 (2 个)
- supplier - 供应商表
- supplier_evaluation - 供应商评估表

### 系统管理 (5 个)
- tag - 标签表
- alert - 告警表
- alert_rule - 告警规则表
- notification - 通知表
- email_config - 邮件配置表

### 日志管理 (2 个)
- deletion_log - 删除日志表
- system_log - 系统日志表

## 权限角色

系统预定义 6 个角色:

1. **admin** - 系统管理员 (所有权限)
2. **warehouse_manager** - 仓库管理员 (库存管理权限)
3. **purchaser** - 采购员 (采购管理权限)
4. **maintenance_manager** - 维修管理员 (维修管理权限)
5. **accountant** - 财务人员 (查看和导出权限)
6. **normal_user** - 普通用户 (基础查看权限)

## 开发指南

### 添加新模型

1. 在 `app/models/` 目录创建新的模型文件
2. 在 `app/models/__init__.py` 中导入
3. 运行数据库迁移或手动创建表

### 添加新路由

1. 在 `app/routes/` 目录创建新的路由文件
2. 创建 Blueprint:
   ```python
   from flask import Blueprint
   
   module_bp = Blueprint('module', __name__, template_folder='templates')
   
   @module_bp.route('/')
   def index():
       return 'Hello'
   ```
3. 在 `app/__init__.py` 中注册蓝图

### 添加新模板

1. 在 `app/templates/` 目录创建对应模块的子目录
2. 继承基础模板 `base.html`
3. 使用 Jinja2 语法编写模板

## 版本管理

项目使用 Git 进行版本管理，遵循 Git Flow 工作流:

```bash
# 主分支
main          # 生产环境
develop       # 开发环境

# 功能分支
feature/xxx   # 新功能开发

# 发布分支
release/v1.0  # 版本发布

# 热修复分支
hotfix/xxx    # 紧急修复
```

## 备份策略

### 代码备份

```bash
# 推送到远程仓库
git push origin develop

# 本地备份
python scripts/backup_code.py
```

### 数据库备份

```bash
# 使用 mysqldump
mysqldump -uroot -p spare_parts_db > backup.sql

# 或使用提供的脚本
python scripts/backup_database.py
```

## 常见问题

### 1. 数据库连接失败

检查 `.env` 文件中的数据库配置:
- MYSQL_HOST
- MYSQL_PORT
- MYSQL_USER
- MYSQL_PASSWORD
- MYSQL_DATABASE

### 2. 依赖安装失败

确保使用 Python 3.10+:
```bash
python --version
```

升级 pip:
```bash
python -m pip install --upgrade pip
```

### 3. 端口被占用

修改启动端口:
```bash
# 在 .env 文件中添加
PORT=5001
```

## 安全建议

1. **修改默认密码**: 首次登录后立即修改 admin 密码
2. **生产环境配置**: 修改 SECRET_KEY
3. **HTTPS**: 生产环境使用 HTTPS
4. **定期备份**: 定期备份数据库和代码
5. **日志监控**: 定期检查系统日志

## 技术支持

- Flask 文档：https://flask.palletsprojects.com/
- SQLAlchemy 文档：https://www.sqlalchemy.org/
- Bootstrap 文档：https://getbootstrap.com/

## 许可证

本项目仅供学习和内部使用。

## 更新日志

### v1.0.0 (2026-03-18)
- 初始版本发布
- 完成所有核心功能
- 包含 29 个数据表
- 支持 6 种角色权限
=======
# spare_parts_management

备件管理系统开发
>>>>>>> 056103ca037440deb20edc3c4d7ade878da4e83d
