# 快手 Kolors 文生图模型配置指南

## 📋 模型介绍

**Kolors（可图）** 是快手团队开发的开源文生图大模型

### 核心特点
- ✅ **中英文双语支持**：基于 GLM 大语言模型
- ✅ **超高清画质**：支持 8K 分辨率
- ✅ **开源免费**：Apache 2.0 协议，可商用
- ✅ **质量优秀**：效果比肩 Midjourney-v6
- ✅ **语义理解强**：复杂场景描述准确

---

## 💰 费用说明

### 是否永久免费？

**答案**：模型开源免费，但使用方式决定费用

| 使用方式 | 费用 | 说明 |
|---------|------|------|
| **本地部署** | ✅ 完全免费 | 一次性配置，永久使用，需 GPU |
| **硅基流动 API** | 🆓 免费额度 | 约 1000-2000 次/月，超出后 ~0.02 元/张 |
| **快手官方 API** | 🆓 有限免费 | 有一定免费调用次数 |

### 硅基流动免费额度

- **新用户**：注册即送免费额度（约值 10-20 元）
- **每月赠送**：约 1000-2000 次调用（1024x1024）
- **超出后**：约 0.02 元/张（非常便宜）
- **适合场景**：100 条备件图片生成完全够用

---

## 🔧 快速配置（推荐：硅基流动 API）

### 步骤 1：获取 API Key

1. **访问硅基流动官网**
   - 网址：https://cloud.siliconflow.cn/

2. **注册账号**
   - 使用手机号或邮箱注册
   - 完成实名认证（可能需要）

3. **创建 API Key**
   - 登录后进入"控制台"
   - 点击"API Keys"
   - 创建新的 API Key
   - 复制并保存（只显示一次）

### 步骤 2：配置到项目

编辑 `.env` 文件（位于 `d:\Trae\spare_management\.env`）：

```bash
# 在文件末尾添加
SILICONFLOW_API_KEY=您的 API_Key
```

**注意**：项目中已有 `SILICONFLOW_API_KEY`，直接修改值即可

### 步骤 3：测试运行

```bash
cd d:\Trae\spare_management
python scripts\generate_kolors_thumbnails.py
```

如果看到 `✅ API Key 已配置`，说明配置成功！

---

## 📝 使用示例

### 测试生成（前 3 条）

```bash
python scripts\generate_kolors_thumbnails.py
```

### 批量生成所有备件

编辑脚本末尾，取消注释：

```python
if __name__ == "__main__":
    # 批量生成所有备件
    generate_thumbnails_for_all(batch_size=10)
```

然后运行：

```bash
python scripts\generate_kolors_thumbnails.py
```

---

## 🎯 本地部署方案（完全免费）

如果您有 GPU（8GB+ 显存），可以本地部署，完全免费使用

### 使用 ComfyUI 部署

#### 1. 安装 ComfyUI

```bash
# 克隆仓库
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI

# 安装依赖
pip install -r requirements.txt
```

#### 2. 下载 Kolors 模型

访问以下任一地址下载：

- **Hugging Face**：https://huggingface.co/Kwai-Kolors/Kolors
- **魔搭社区**：https://modelscope.cn/models/Kwai-Kolors/Kolors

下载文件：
- `Kolors.safetensors`

放到目录：
```
ComfyUI/models/checkpoints/Kolors.safetensors
```

#### 3. 启动 ComfyUI

```bash
python main.py
```

浏览器访问：http://127.0.0.1:8188

#### 4. 创建工作流

1. 加载 Kolors 节点
2. 配置提示词
3. 设置输出路径
4. 批量生成

---

## 📊 对比分析

| 特性 | 硅基流动 API | 本地部署 |
|------|-------------|---------|
| **费用** | 免费额度 + 按量付费 | 完全免费 |
| **配置难度** | ⭐ 简单 | ⭐⭐⭐⭐ 复杂 |
| **硬件要求** | 无 | GPU 8GB+ |
| **生成速度** | 快（云端 GPU） | 取决于本地 GPU |
| **数据隐私** | 云端处理 | 本地处理 |
| **适用场景** | 中小批量 | 大批量、长期使用 |

---

## 💡 推荐建议

### 适合使用 API 的场景
- ✅ 偶尔生成图片
- ✅ 没有 GPU 或显存不足
- ✅ 不想折腾配置
- ✅ 快速测试验证

### 适合本地部署的场景
- ✅ 频繁生成图片
- ✅ 有高性能 GPU
- ✅ 注重数据隐私
- ✅ 长期使用、大批量

---

## 🔗 相关资源

### 官方链接
- [硅基流动官网](https://cloud.siliconflow.cn/)
- [Kolors GitHub](https://github.com/Kwai-Kolors/Kolors)
- [Kolors Hugging Face](https://huggingface.co/Kwai-Kolors/Kolors)
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)

### 文档教程
- [Kolors 论文](https://arxiv.org/abs/2406.11633)
- [ComfyUI 使用教程](https://blenderneko.github.io/NODES-docs/)

---

## ❓ 常见问题

### Q1: 免费额度用完了怎么办？
- 方案 1：等待下月重置
- 方案 2：充值（很便宜，约 0.02 元/张）
- 方案 3：切换本地部署

### Q2: 生成失败怎么办？
- 检查 API Key 是否正确
- 检查网络连接
- 查看错误日志
- 调整提示词

### Q3: 图片质量不满意？
- 优化提示词描述
- 增加生成步数（28→40）
- 调整 seed 值
- 使用负面提示词

### Q4: 本地部署需要多大显存？
- 最低：6GB（可能慢）
- 推荐：8GB-12GB
- 最佳：16GB+

---

## 📞 技术支持

- 硅基流动客服：官网在线咨询
- Kolors 社区：GitHub Issues
- ComfyUI 论坛：https://comfyui.org/

---

**最后更新**：2025-03-18
