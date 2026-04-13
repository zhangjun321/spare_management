# 仓库管理模块增强 - 部署指南

## 部署时间
2026-04-10

## 部署范围
- 质检管理模块增强（第一阶段）
- 并发控制机制（第三阶段部分）

## 一、数据库迁移

### 1.1 备份数据库

**重要**: 在执行任何数据库操作之前，请先备份现有数据库！

```bash
# Windows 环境
cd d:\Trae\spare_management\instance
copy spare_management.db spare_management.db.backup_20260410

# 或者使用 mysqldump（如果使用 MySQL）
mysqldump -u root -p spare_management > backup_20260410.sql
```

### 1.2 执行迁移脚本

**方式 1: 使用 MySQL Workbench 或命令行工具**

```bash
# 进入数据库目录
cd d:\Trae\spare_management\database\migrations

# 执行迁移脚本
mysql -u root -p spare_management < enhance_warehouse_models.sql
```

**方式 2: 在 MySQL Workbench 中手动执行**

1. 打开 MySQL Workbench
2. 连接到数据库
3. 打开 `enhance_warehouse_models.sql` 文件
4. 执行整个脚本

**方式 3: 使用 Python 脚本执行**

```python
# 创建执行脚本 execute_migration.py
import mysql.connector

# 数据库配置
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'spare_management'
}

# 读取 SQL 文件
with open('database/migrations/enhance_warehouse_models.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# 执行 SQL
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# 执行每条 SQL 语句
for statement in sql_script.split(';'):
    statement = statement.strip()
    if statement:
        try:
            cursor.execute(statement)
        except Exception as e:
            print(f"执行错误：{e}")

conn.commit()
cursor.close()
conn.close()

print("迁移完成！")
```

### 1.3 验证迁移结果

执行以下 SQL 验证表结构：

```sql
-- 检查新增的表
SHOW TABLES LIKE '%quality%';
SHOW TABLES LIKE '%wave%';
SHOW TABLES LIKE '%inventory_check%';

-- 检查字段是否添加成功
DESC quality_check;
DESC quality_check_item;
DESC quality_check_standard;

-- 检查数据
SELECT COUNT(*) FROM quality_check_standard;
SELECT COUNT(*) FROM picking_wave;
SELECT COUNT(*) FROM wave_strategy;
```

## 二、代码部署

### 2.1 更新代码文件

需要更新的文件列表：

**模型文件**:
- ✅ `app/models/warehouse_v3/quality_check.py` - 质检模型增强
- ✅ `app/models/warehouse_v3/__init__.py` - 模型导出更新

**路由文件**:
- ✅ `app/routes/quality_check_enhanced.py` - 增强版质检 API（新增）
- ✅ `app/routes/quality_check_pages.py` - 质检页面路由（更新）

**模板文件**:
- ✅ `app/templates/warehouse_new/quality_check_enhanced.html` - 质检管理页面（新增）
- ✅ `app/templates/warehouse_new/quality_standard.html` - 质检标准页面（新增）

**数据库迁移**:
- ✅ `database/migrations/enhance_warehouse_models.sql` - 迁移脚本（新增）

### 2.2 注册路由蓝图

路由已在 `app/__init__.py` 中注册，无需修改。

### 2.3 安装依赖（如有需要）

```bash
cd d:\Trae\spare_management
pip install -r requirements.txt
```

## 三、启动服务

### 3.1 停止现有服务

如果服务正在运行，先停止它：

```bash
# 按 Ctrl+C 停止服务
```

### 3.2 重新启动服务

```bash
cd d:\Trae\spare_management
python run.py
```

### 3.3 验证服务启动

查看控制台输出，确认：
- ✅ 应用启动成功
- ✅ 没有报错
- ✅ 端口 5000 正常监听

## 四、功能验证

### 4.1 访问质检管理页面

打开浏览器访问：
```
http://localhost:5000/quality-check
```

**验证点**:
- ✅ 页面正常加载
- ✅ 统计卡片显示正确
- ✅ 质检单列表显示
- ✅ 创建按钮可点击

### 4.2 访问质检标准页面

打开浏览器访问：
```
http://localhost:5000/quality-standard
```

**验证点**:
- ✅ 页面正常加载
- ✅ 质检标准列表显示
- ✅ 新增标准按钮可点击

### 4.3 API 接口测试

**测试统计接口**:
```bash
curl http://localhost:5000/api/quality-check/stats
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "by_status": {
      "pending": 0,
      "inspecting": 0,
      "completed": 0,
      "cancelled": 0
    },
    "today_count": 0,
    "pass_rate": 0,
    "total_qualified": 0,
    "total_unqualified": 0
  }
}
```

**测试质检标准列表**:
```bash
curl http://localhost:5000/api/quality-check/standards
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "list": [...],
    "total": 4,
    "page": 1,
    "per_page": 50
  }
}
```

### 4.4 创建质检单测试

1. 访问质检管理页面
2. 点击"创建质检单"
3. 选择入库单（需要先有已完成的入库单）
4. 填写质检信息
5. 提交

**验证点**:
- ✅ 表单验证正常
- ✅ 提交成功
- ✅ 质检单号自动生成
- ✅ 质检明细自动创建

### 4.5 执行质检测试

1. 在质检单列表中点击"开始质检"
2. 点击"执行质检"
3. 录入质检结果
4. 提交结果
5. 完成质检

**验证点**:
- ✅ 状态流转正确
- ✅ 数量计算准确
- ✅ 合格率自动计算
- ✅ 质检结果自动判定

## 五、常见问题排查

### 问题 1: 表不存在错误

**错误信息**:
```
sqlalchemy.exc.ProgrammingError: (1146, "Table 'spare_management.quality_check_standard' doesn't exist")
```

**解决方案**:
- 确认数据库迁移脚本已执行
- 检查数据库连接配置
- 重新执行迁移脚本

### 问题 2: 字段不存在错误

**错误信息**:
```
sqlalchemy.exc.OperationalError: (1054, "Unknown column 'check_type' in 'field list'")
```

**解决方案**:
- 确认 ALTER TABLE 语句执行成功
- 检查表结构：`DESC quality_check;`
- 手动添加缺失字段

### 问题 3: 路由 404 错误

**错误信息**:
```
404 Not Found
```

**解决方案**:
- 确认路由蓝图已注册
- 重启 Flask 应用
- 检查 URL 拼写

### 问题 4: 模板不存在错误

**错误信息**:
```
jinja2.exceptions.TemplateNotFound: 'warehouse_new/quality_check_enhanced.html' not found
```

**解决方案**:
- 确认模板文件已创建
- 检查文件路径是否正确
- 确认文件编码为 UTF-8

### 问题 5: 外键约束错误

**错误信息**:
```
sqlalchemy.exc.IntegrityError: (1452, "Cannot add or update a child row: a foreign key constraint fails")
```

**解决方案**:
- 确保关联记录存在（如入库单、备件）
- 检查外键字段值
- 确认数据完整性

## 六、回滚方案

如果部署后发现问题严重，需要回滚：

### 6.1 数据库回滚

```bash
# 恢复备份
mysql -u root -p spare_management < backup_20260410.sql

# 或者删除新增的表
DROP TABLE IF EXISTS quality_check_standard;
DROP TABLE IF EXISTS picking_wave;
DROP TABLE IF EXISTS wave_strategy;
DROP TABLE IF EXISTS inventory_check_plan;
DROP TABLE IF EXISTS inventory_check_analysis;
DROP TABLE IF EXISTS warning_notification;

# 删除新增的字段（需要逐个删除）
ALTER TABLE quality_check DROP COLUMN check_type;
ALTER TABLE quality_check DROP COLUMN check_method;
# ... 依此类推
```

### 6.2 代码回滚

```bash
# 使用 Git 回滚（如果使用版本控制）
git checkout HEAD -- app/models/warehouse_v3/quality_check.py
git checkout HEAD -- app/routes/quality_check_pages.py

# 或者手动删除新增的文件
rm app/routes/quality_check_enhanced.py
rm app/templates/warehouse_new/quality_check_enhanced.html
rm app/templates/warehouse_new/quality_standard.html
```

## 七、性能优化建议

### 7.1 数据库索引优化

执行以下 SQL 添加索引：

```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_quality_check_created ON quality_check(created_at DESC);
CREATE INDEX idx_quality_check_result ON quality_check(result);
CREATE INDEX idx_quality_check_item_status ON quality_check_item(status);
CREATE INDEX idx_quality_check_standard_part ON quality_check_standard(part_id, is_active);
```

### 7.2 缓存配置

如果使用 Redis，可以配置缓存：

```python
# 在 config.py 中添加
CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = 'localhost'
CACHE_REDIS_PORT = 6379
CACHE_REDIS_DB = 0
```

## 八、下一步计划

### 8.1 待完成功能

- [ ] 盘点管理模块增强（第二阶段）
- [ ] Redis 分布式锁完整实现（第三阶段）
- [ ] 预警通知多渠道发送（第四阶段）
- [ ] 波次管理模块（第五阶段）

### 8.2 测试计划

- [ ] 单元测试编写
- [ ] 集成测试
- [ ] 性能测试
- [ ] 用户验收测试

### 8.3 培训计划

- [ ] 操作员培训（质检流程）
- [ ] 管理员培训（标准配置）
- [ ] 技术人员培训（系统维护）

## 九、联系支持

如遇到任何问题，请联系：
- 技术支持：[联系方式]
- 项目负责人：[联系方式]

---

**部署完成时间**: _______________  
**部署人员**: _______________  
**验证人员**: _______________  
**备注**: _______________
