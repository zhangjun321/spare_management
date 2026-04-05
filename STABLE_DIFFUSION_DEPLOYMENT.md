# Stable Diffusion WebUI 部署指南

## 系统要求

### 最低配置
- **显卡**: NVIDIA GPU，显存 ≥ 4GB
- **系统**: Windows 10/11 或 Linux
- **Python**: 3.10 或更高版本
- **磁盘空间**: 至少 10GB（模型文件 + 依赖）

### 推荐配置
- **显卡**: NVIDIA GPU，显存 ≥ 8GB
- **系统**: Windows 10/11
- **Python**: 3.10
- **磁盘空间**: 20GB 以上

---

## 部署步骤

### 步骤 1：克隆 Stable Diffusion WebUI 项目

打开命令行（CMD 或 PowerShell），进入您想存放项目的目录：

```bash
cd D:\Trae
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
```

如果没有安装 Git，可以直接从 GitHub 下载 ZIP 包：
https://github.com/AUTOMATIC1111/stable-diffusion-webui/archive/refs/heads/master.zip

下载后解压到 `D:\Trae\stable-diffusion-webui`

---

### 步骤 2：下载模型文件

#### 推荐模型（适合工业产品图）：

1. **Realistic Vision V6.0 B1**（推荐）
   - 下载地址: https://civitai.com/models/4201/realistic-vision-v60-b1
   - 文件名: `realisticVisionV60B1_v60B1.safetensors`
   - 大小: 约 2GB

2. **其他可选模型**：
   - SD 1.5 基础模型: https://huggingface.co/runwayml/stable-diffusion-v1-5
   - Deliberate V3: https://civitai.com/models/4823/deliberate

#### 放置模型文件：

将下载的 `.safetensors` 或 `.ckpt` 文件放到：

```
D:\Trae\stable-diffusion-webui\models\Stable-diffusion\
```

---

### 步骤 3：启动 Stable Diffusion WebUI（启用 API 模式）

进入项目目录：

```bash
cd D:\Trae\stable-diffusion-webui
```

启动 WebUI（**重要：必须启用 API 模式**）：

```bash
webui.bat --api --listen
```

#### 参数说明：
- `--api`: 启用 API 接口（必需）
- `--listen`: 允许局域网访问（可选）

#### 首次启动会自动：
1. 下载 Python 依赖包
2. 下载 Stable Diffusion 基础模型（如果没有）
3. 配置运行环境

#### 等待启动完成：

看到类似以下输出表示启动成功：

```
Running on local URL: http://127.0.0.1:7860
```

---

### 步骤 4：测试 WebUI

在浏览器中打开：
http://127.0.0.1:7860

您应该能看到 Stable Diffusion WebUI 的界面。

#### 简单测试：
1. 在提示词框输入：`a high precision mechanical bearing part`
2. 点击"Generate"按钮
3. 等待生成完成

---

### 步骤 5：测试 API 接口

WebUI 启动成功后，回到您的备件管理项目目录，运行测试脚本：

```bash
cd D:\Trae\spare_management
python test_stable_diffusion.py
```

如果测试成功，会生成测试图片到 `sd_test_output` 目录。

---

## 集成到您的备件管理系统

一旦 Stable Diffusion WebUI 部署成功，我可以帮您修改代码，将文生图服务从百度千帆切换到本地 Stable Diffusion。

### 需要修改的文件：
- `app/services/image_generation_service.py`

### 主要改动：
1. 将 `_generate_single_image` 方法中的百度千帆 API 调用替换为 Stable Diffusion API 调用
2. 使用 `requests` 库调用 `http://127.0.0.1:7860/sdapi/v1/txt2img`
3. 处理 base64 编码的图片数据

---

## 常见问题

### Q1: 启动时提示 CUDA 错误？
**A**: 确保安装了最新的 NVIDIA 显卡驱动。

### Q2: 显存不足怎么办？
**A**: 
- 使用更小的图片尺寸（512x512）
- 使用 `--medvram` 或 `--lowvram` 参数启动
- 使用更小的模型

### Q3: 下载模型太慢？
**A**: 使用国内镜像站或使用下载工具（如 IDM）。

### Q4: 如何选择合适的模型？
**A**:
- 真实感产品图: Realistic Vision、Deliberate
- 工业风格: SD 1.5 基础模型 + 工业风格 LoRA

---

## 下一步

部署完成后，请告诉我，我会帮您：
1. 修改 `image_generation_service.py`，集成 Stable Diffusion API
2. 测试备件图片生成功能
3. 确保所有功能正常工作

---

## 快速开始命令汇总

```bash
# 1. 克隆项目
cd D:\Trae
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git

# 2. 下载模型文件到 models/Stable-diffusion/ 目录

# 3. 启动 WebUI（启用 API）
cd D:\Trae\stable-diffusion-webui
webui.bat --api --listen

# 4. 测试 API（在另一个终端）
cd D:\Trae\spare_management
python test_stable_diffusion.py
```

祝部署顺利！如有问题请告诉我！