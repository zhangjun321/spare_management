# 高德地图 API Key 配置指南

## 🚀 快速开始（5 分钟搞定）

### 第一步：申请高德地图 API Key

#### 1. 访问高德开放平台
打开网址：**https://lbs.amap.com/**

#### 2. 注册/登录账号
- 使用高德账号登录（可用淘宝/支付宝账号）
- 如果没有账号，先注册

#### 3. 进入控制台
- 点击右上角 **"控制台"**

#### 4. 创建应用
- 点击 **"应用管理"** → **"我的应用"**
- 点击 **"+ 创建新应用"**

#### 5. 填写应用信息
```
应用名称：备件管理系统
应用类型：Web 端（JS API）
```

#### 6. 添加 Key
- 创建应用后，点击 **"+ 添加 Key"**
- 填写：
  ```
  Key 名称：dashboard_key
  服务平台：Web 端（JS API）
  ```
- **白名单**：
  - 开发环境：`localhost`
  - 或填写：`*`（测试用，生产环境要改）

#### 7. 获取 API Key
- 创建成功后，会显示您的 **Key**
- 格式类似：`a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

---

### 第二步：配置到系统中

#### 方法一：直接修改模板（最简单）

1. 打开文件：`app/templates/equipment/dashboard_amap.html`

2. 找到第 8-11 行：
```html
<script type="text/javascript">
window._AMapSecurityConfig = {
    securityJsCode: '您的安全密钥'
}
</script>
<script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key=您的 API Key"></script>
```

3. 替换为您的实际 Key：
```html
<script type="text/javascript">
window._AMapSecurityConfig = {
    securityJsCode: '您的安全密钥'
}
</script>
<script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"></script>
```

4. 保存文件，刷新页面即可！

---

#### 方法二：使用配置文件（推荐生产环境）

1. 在 `app/config.py` 中添加：
```python
class Config:
    # ... 其他配置 ...
    AMAP_API_KEY = os.environ.get('AMAP_API_KEY', '')
    AMAP_SECURITY_CODE = os.environ.get('AMAP_SECURITY_CODE', '')
```

2. 在 `.env` 文件中设置：
```
AMAP_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
AMAP_SECURITY_CODE=您的安全密钥
```

3. 修改模板使用配置：
```html
<script type="text/javascript">
window._AMapSecurityConfig = {
    securityJsCode: '{{ config.AMAP_SECURITY_CODE }}'
}
</script>
<script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key={{ config.AMAP_API_KEY }}"></script>
```

---

## 🔍 获取安全密钥（重要！）

从 2021 年开始，高德地图要求 Web 端同时配置 **API Key** 和 **安全密钥**：

### 步骤：
1. 在应用管理页面，找到您的应用
2. 点击应用名称查看详情
3. 在 **Key 详情** 页面，找到 **"安全密钥"**
4. 复制安全密钥（一串随机字符）
5. 配置到代码中

---

## ✅ 验证配置

### 访问设备仪表盘
```
http://localhost:5000/equipment/dashboard
```

### 预期结果：
- ✅ 看到中国地图
- ✅ 看到 13 个设备标记点
- ✅ 点击标记显示设备信息
- ✅ 右侧显示"有位置设备：13"

### 如果失败：
- ❌ 地图空白 → 检查 API Key 是否正确
- ❌ 提示"Key 非法" → 检查 Key 是否复制完整
- ❌ 提示"Referer 校验失败" → 检查白名单设置

---

## 📊 配额说明

### 个人开发者（免费）：
- **日配额**：5 万次/天
- **QPS 限制**：50 次/秒
- **月配额**：150 万次/月

### 对于设备仪表盘：
- 每次访问加载一次地图 ≈ 1 次请求
- 5 万次/天 = 每天可访问 5 万次
- 完全够用！

---

## 🆚 高德 vs 百度地图对比

| 对比项 | 高德地图 | 百度地图 |
|--------|----------|----------|
| **API 申请** | ✅ 简单 | ✅ 简单 |
| **免费配额** | ✅ 5 万次/天 | ✅ 30 万次/天 |
| **国内精度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **文档质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **安全密钥** | ⚠️ 需要 | ❌ 不需要 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**结论**：两者都可以，高德文档更友好，百度配额更大。

---

## 💡 常见问题

### Q1: 安全密钥在哪里？
**A**: 在应用管理 → Key 详情页面，找到"安全密钥"或"Security Code"

### Q2: 白名单怎么设置？
**A**: 
- 开发环境：`localhost`
- 生产环境：`yourdomain.com`
- 测试：`*`（不推荐）

### Q3: 提示"Key 非法"怎么办？
**A**: 
1. 检查 Key 是否复制完整（32 位字符）
2. 检查 Key 是否已启用
3. 检查服务平台是否选择"Web 端（JS API）"

### Q4: 地图加载很慢？
**A**: 
1. 检查网络连接
2. 检查浏览器 Console 是否有错误
3. 尝试清除浏览器缓存

---

## 📞 技术支持

高德地图官方文档：
- Web API: https://lbs.amap.com/api/javascript-api/summary
- 常见问题：https://lbs.amap.com/faq/

---

## 🎯 快速测试

配置完成后，访问：
```
http://localhost:5000/equipment/dashboard
```

应该看到：
- 🗺️ 高德地图
- 📍 13 个设备标记
- 📊 设备统计信息

---

**最后更新**: 2026 年 4 月 18 日
