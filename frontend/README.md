# 智能仓库管理系统 - React 前端

## 📦 项目简介

这是智能仓库管理系统的 React 前端项目，采用渐进式迁移策略，从传统的 Bootstrap + 原生 JavaScript 迁移到现代化的 React 框架。

## 🚀 技术栈

- **React 18.2** - 前端框架
- **Vite 5.0** - 构建工具
- **React Router 6** - 路由管理
- **Zustand 4.4** - 轻量级状态管理
- **Axios 1.6** - HTTP 客户端
- **React Bootstrap 2.9** - UI 组件库
- **Bootstrap 5.3** - CSS 框架
- **Chart.js 4.4** - 图表库
- **React Icons 4.12** - 图标库

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/     # 通用组件
│   ├── pages/         # 页面组件
│   ├── layouts/       # 布局组件
│   ├── stores/        # 状态管理
│   ├── services/      # API 服务
│   ├── hooks/         # 自定义 Hooks
│   ├── utils/         # 工具函数
│   ├── App.jsx        # 应用入口
│   ├── main.jsx       # 入口文件
│   └── index.css      # 全局样式
├── public/            # 静态资源
├── index.html         # HTML 模板
├── package.json       # 依赖配置
└── vite.config.js     # Vite 配置
```

## 🎯 已完成的功能

### ✅ 第一阶段：基础架构

1. **开发环境搭建**
   - Vite + React 项目初始化
   - ESLint + Prettier 配置
   - 路径别名配置（@）
   - 开发服务器代理配置

2. **基础组件**
   - MainLayout - 主布局组件
   - Sidebar - 侧边栏导航（可折叠）
   - Header - 顶部导航栏
   - Dashboard - 智能仓库驾驶舱页面

3. **服务层**
   - API 客户端封装（Axios）
   - CSRF Token 自动处理
   - 请求/响应拦截器
   - 仓库管理服务
   - AI 分析服务

4. **状态管理**
   - Zustand 状态管理
   - 仓库状态 store
   - UI 状态 store

## 📊 已迁移页面

### 智能仓库驾驶舱 (Dashboard)

**功能特性：**
- ✅ 6 个统计卡片（今日入库、今日出库、库存品种、低库存预警、缺货预警、AI 分析建议）
- ✅ AI 智能洞察展示
- ✅ 4 个数据图表（库存状态分布、出入库趋势、仓库利用率、库存周转分析）
- ✅ 待处理任务列表
- ✅ 一键刷新功能
- ✅ 响应式设计
- ✅ 现代化 UI（渐变色卡片、悬停动画）

**访问地址：** http://localhost:3000/warehouse/dashboard

## 🛠️ 开发指南

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 代码格式化

```bash
npm run format
```

### 代码检查

```bash
npm run lint
```

## 📝 下一步计划

### 待迁移页面

1. **入库管理列表** - 优先级：高
2. **出库管理列表** - 优先级：高
3. **库存管理列表** - 优先级：高
4. **备件管理模块** - 优先级：中
5. **其他业务模块** - 优先级：低

### 待开发组件

- 通用表格组件
- 表单组件（Input, Select, Form）
- 模态框组件
- 分页组件
- 搜索组件
- 加载更多组件

## 🔧 代理配置

开发服务器已配置代理到 Flask 后端（http://localhost:5000）：

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  },
  '/static': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  },
}
```

## 📄 代码规范

- 使用 ES6+ 语法
- 组件使用函数式写法 + Hooks
- 使用 Prettier 格式化代码
- 遵循 ESLint 规则
- 组件文件使用 PascalCase 命名
- 工具函数使用 camelCase 命名

## 🎨 UI 设计规范

- 保持与现有 Bootstrap 风格一致
- 使用统一的配色方案
- 响应式设计（移动端适配）
- 统一的间距系统（Bootstrap spacing）
- 渐变色卡片设计
- 悬停动画效果

## 📞 开发团队

如有任何问题，请联系开发团队。

---

**最后更新：** 2024-06-06
