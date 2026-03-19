# 文心一言 AI 备件缩略图生成说明

## 📋 功能概述

使用文心一言 AI 为备件管理系统的每条记录生成 6 张高清图片（正面、侧面、俯视、结构、细节、电路），并从正面图生成缩略图。

## ⚠️ API 限制说明

**重要提示**：百度文心一言的图片生成 API（SD-XL）目前需要特殊权限，普通 API Key 无法直接使用。

### 当前状态
- ✅ 文本生成 API：正常工作（用于分析备件信息）
- ❌ 图片生成 API：需要申请企业权限

## 🔧 解决方案

### 方案一：使用其他 AI 图片生成服务（推荐）

#### 1. **通义万相**（阿里云）
- 有免费额度
- 支持产品图片生成
- API 文档：https://help.aliyun.com/zh/dashscope/

#### 2. **腾讯混元**
- 支持图片生成
- 有免费试用额度

#### 3. **Stable Diffusion API**
- 开源免费
- 可本地部署
- 或使用第三方 API 服务

### 方案二：使用占位图片（临时方案）

系统已实现完整的图片显示功能，可以：

1. **使用默认占位图**：
   - 系统会自动显示灰色占位图标
   - 适用于没有图片的备件

2. **手动上传图片**：
   - 在备件编辑页面添加图片上传功能
   - 图片存储在 `D:\Trae\spare_management\uploads\images\`

3. **批量导入现有图片**：
   - 如果有备件图片资源，可以批量导入
   - 按备件编码组织文件夹结构

## 📁 图片存储结构

```
D:\Trae\spare_management\uploads\images\
├── SKFX-A-001-001-EHD/
│   ├── front.jpg       # 正面图
│   ├── side.jpg        # 侧面图
│   ├── top.jpg         # 俯视图
│   ├── structure.jpg   # 结构图
│   ├── detail.jpg      # 细节图
│   ├── circuit.jpg     # 电路图（如有）
│   └── thumbnail.jpg   # 缩略图（从正面图生成）
├── FAGX-A-002-002-PWP/
└── ...
```

## ✅ 已完成的功能

### 1. 数据库
- ✅ SparePart 模型已有 `image_url` 字段
- ✅ 支持存储缩略图路径

### 2. 前端显示
- ✅ 备件列表第一列显示缩略图
- ✅ 点击缩略图可查看大图（模态框）
- ✅ 无图片时显示占位图标
- ✅ 支持图片预览和放大

### 3. 脚本功能
- ✅ 备件信息分析
- ✅ AI 提示词生成
- ✅ 图片文件夹自动创建
- ✅ 缩略图生成（PIL）
- ✅ 数据库自动更新

## 🚀 后续步骤

### 立即可以使用的功能

1. **查看备件列表**
   - 访问：http://127.0.0.1:5000/spare_parts/
   - 第一列显示缩略图（目前为空，显示占位符）

2. **手动添加图片**
   - 编辑备件
   - 上传图片
   - 系统自动显示在列表中

### 如需启用 AI 图片生成

1. **获取图片生成 API 权限**
   - 选项 1：申请百度文心一言企业权限
   - 选项 2：使用通义万相 API（推荐）
   - 选项 3：本地部署 Stable Diffusion

2. **修改脚本**
   - 更新 `generate_wenxin_image()` 函数
   - 使用新的 API 接口

3. **批量生成**
   - 运行脚本生成所有备件图片
   - 系统自动更新数据库

## 📝 代码位置

- **生成脚本**：`scripts/generate_part_thumbnails.py`
- **模板文件**：`app/templates/spare_parts/list.html`
- **数据库模型**：`app/models/spare_part.py`
- **图片目录**：`D:\Trae\spare_management\uploads\images\`

## 💡 建议

1. **短期方案**：使用占位图，手动上传重要备件图片
2. **中期方案**：申请通义万相 API，批量生成图片
3. **长期方案**：本地部署 Stable Diffusion，完全自主控制

## 🔗 相关资源

- [通义万相 API](https://help.aliyun.com/zh/dashscope/)
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- [百度文心一言](https://cloud.baidu.com/product/wenxinworkshop)
