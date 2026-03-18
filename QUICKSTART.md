# 备件管理系统 - 快速启动指南

## 项目当前状态

✅ **已完成的工作**:

1. ✅ 项目目录结构创建完成
2. ✅ Flask 应用工厂和配置文件
3. ✅ 所有 29 个数据表的 SQL 脚本
4. ✅ 核心数据模型 (部分)
5. ✅ 数据库初始化脚本
6. ✅ 环境变量配置
7. ✅ Python 依赖配置 (requirements.txt)
8. ✅ 项目文档 (README.md)

## 下一步操作

### 第一步：安装 Python 依赖

打开命令行，执行:

```bash
cd d:\Trae\spare_management
pip install -r requirements.txt
```

如果遇到依赖安装问题，可以只安装核心依赖:

```bash
pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF Flask-Migrate PyMySQL bcrypt python-dotenv
```

### 第二步：配置数据库

**重要**: 由于数据库密码验证问题，需要手动配置。

#### 方法 1: 使用 MySQL Workbench (推荐)

1. 打开 MySQL Workbench
2. 连接到您的 MySQL 服务器 (root / Kra@211314.)
3. 执行以下 SQL:

```sql
-- 1. 创建数据库
CREATE DATABASE spare_parts_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 切换到该数据库
USE spare_parts_db;

-- 3. 执行建表脚本
-- 打开 d:\Trae\spare_management\scripts\create_tables.sql 文件
-- 复制所有内容并执行
```

4. 验证表是否创建成功:

```sql
SHOW TABLES;
-- 应该显示 29 个表
```

#### 方法 2: 使用命令行

```bash
# 1. 登录 MySQL
mysql -uroot -p"Kra@211314."

# 2. 创建数据库
CREATE DATABASE spare_parts_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE spare_parts_db;

# 3. 执行 SQL 脚本
source d:/Trae/spare_management/scripts/create_tables.sql;

# 4. 验证
SHOW TABLES;
```

### 第三步：修改数据库密码配置

编辑 `d:\Trae\spare_management\.env` 文件:

```env
# 找到这一行
MYSQL_PASSWORD=Kra@211314.

# 如果您的密码不同，请修改为正确的密码
# 注意：根据您的消息，密码是 Kra@211314 (没有最后的点)
# 或者 Kr@211314
# 请使用您实际能登录的密码
```

### 第四步：启动应用

```bash
cd d:\Trae\spare_management
python run.py
```

如果看到以下输出，说明启动成功:

```
================================================================================
备件管理系统启动
================================================================================
环境：开发
地址：http://127.0.0.1:5000
调试模式：开启
================================================================================
```

### 第五步：访问系统

1. 打开浏览器，访问：http://127.0.0.1:5000
2. 使用默认管理员账户登录:
   - 用户名：`admin`
   - 密码：`admin123`

**重要**: 首次登录后请立即修改密码!

## 常见问题解决

### 问题 1: 数据库连接失败

**错误信息**: `Access denied for user 'root'@'localhost'`

**解决方法**:
1. 确认 MySQL 密码正确
2. 编辑 `.env` 文件，修改 `MYSQL_PASSWORD`
3. 确认 MySQL 服务已启动

### 问题 2: 端口被占用

**错误信息**: `Address already in use`

**解决方法**:
1. 修改 `.env` 文件，添加: `PORT=5001`
2. 或者关闭占用 5000 端口的程序

### 问题 3: 依赖安装失败

**解决方法**:
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 4: Flask 版本不兼容

**解决方法**:
```bash
# 安装指定版本
pip install Flask==2.3.3
pip install Flask-SQLAlchemy==3.0.5
```

## 项目目录说明

```
spare_management/
├── app/                    # 应用主目录
│   ├── models/            # 数据模型 (需要继续创建)
│   ├── routes/            # 路由 (需要继续创建)
│   ├── templates/         # HTML 模板 (需要继续创建)
│   ├── static/            # 静态资源 (CSS, JS, 图片)
│   ├── forms/             # 表单定义
│   ├── services/          # 业务逻辑层
│   └── utils/             # 工具函数
├── scripts/               # 脚本文件
│   ├── init_db.py        # 数据库初始化
│   └── create_tables.sql # 建表 SQL
├── .env                   # 环境变量
├── requirements.txt       # Python 依赖
└── run.py                # 启动文件
```

## 后续开发任务

以下模块需要继续创建:

### 高优先级

1. ⏳ 用户认证模块 (路由 + 表单 + 模板)
2. ⏳ 备件管理模块
3. ⏳ 库存管理模块
4. ⏳ 仪表盘页面

### 中优先级

5. ⏳ 设备管理模块
6. ⏳ 维修管理模块
7. ⏳ 采购管理模块
8. ⏳ 前端基础模板

### 低优先级

9. ⏳ 报表统计模块
10. ⏳ 系统管理模块
11. ⏳ 告警和通知模块

## 开发建议

### 1. 先完成核心功能

建议按以下顺序开发:

1. 用户认证 (登录/登出)
2. 基础布局模板
3. 仪表盘
4. 备件管理 (CRUD)
5. 库存管理 (入库/出库)

### 2. 使用 Git 进行版本控制

```bash
cd d:\Trae\spare_management
git init
git add .
git commit -m "初始提交：项目框架和数据库设计"
```

### 3. 定期备份

- 代码备份到 Git 仓库
- 数据库定期导出 SQL

## 联系和支持

如有问题，请查看:
- 项目文档：`README.md`
- 开发文档：`d:/Trae/备件管理系统开发文档.md`
- 数据库设计：`d:/Trae/数据库表结构设计详细文档.md`

---

**祝您开发顺利!** 🚀
