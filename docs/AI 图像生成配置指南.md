# AI 图像生成 - 配置指南

## 问题说明

当前提示"API 连接失败：无法获取访问令牌"是因为还没有配置百度千帆 API 的访问凭证。

## 解决方案

### 方案一：配置百度 API（推荐）

#### 1. 获取百度 API 凭证

1. **访问百度智能云平台**
   - 网址：https://cloud.baidu.com/product/wenxinworkshop
   - 注册/登录百度账号

2. **创建应用**
   - 进入"千帆大模型平台"
   - 点击"应用管理" → "创建应用"
   - 选择"文心一格"服务
   - 填写应用信息（名称、描述等）
   - 提交创建

3. **获取凭证**
   - 应用创建成功后，进入应用详情
   - 复制 `API Key` 和 `Secret Key`

#### 2. 配置到项目

**方式 A：使用 .env 文件（推荐）**

在项目根目录的 `.env` 文件中添加：

```bash
# 百度千帆 API 配置
BAIDU_API_KEY=你的 API_KEY
BAIDU_SECRET_KEY=你的 SECRET_KEY
```

**方式 B：使用环境变量**

```bash
# Windows PowerShell
$env:BAIDU_API_KEY="你的 API_KEY"
$env:BAIDU_SECRET_KEY="你的 SECRET_KEY"

# Linux/Mac
export BAIDU_API_KEY="你的 API_KEY"
export BAIDU_SECRET_KEY="你的 SECRET_KEY"
```

#### 3. 重启应用

配置完成后，重启 Flask 应用使配置生效：

```bash
# 停止当前运行的应用（Ctrl+C）
# 然后重新启动
python run.py
```

#### 4. 测试连接

1. 访问 `/ai-image/` 页面
2. 点击"测试 API 连接"按钮
3. 如果显示"API 连接测试成功"，则配置完成

### 方案二：使用本地 Stable Diffusion（高级）

如果不想使用百度 API，可以部署本地 Stable Diffusion：

#### 1. 安装 Stable Diffusion WebUI

```bash
# 克隆项目
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui

# 运行（首次会自动下载模型）
./webui.sh  # Linux/Mac
webui-user.bat  # Windows
```

#### 2. 修改服务配置

修改 `app/services/baidu_image_service.py`，添加本地 SD 支持：

```python
def generate_warehouse_image(self, prompt, ...):
    # 检测是否使用本地 SD
    if os.getenv("USE_LOCAL_SD", "false").lower() == "true":
        return self._generate_with_local_sd(prompt, ...)
    else:
        return self._generate_with_baidu(prompt, ...)
```

#### 3. 配置本地 SD

在 `.env` 文件中添加：

```bash
USE_LOCAL_SD=true
LOCAL_SD_URL=http://127.0.0.1:7860
```

### 方案三：使用其他云服务商（备选）

#### 1. 阿里通义万相

- 官网：https://tongyi.aliyun.com/wanxiang/
- 价格：按量计费
- 优势：国内访问速度快

#### 2. 腾讯混元 AI

- 官网：https://cloud.tencent.com/product/hunyuan-aigc
- 价格：按量计费
- 优势：与微信生态集成

#### 3. Midjourney（海外）

- 官网：https://www.midjourney.com/
- 价格：订阅制
- 优势：图像质量高

## 费用说明

### 百度千帆定价

**文心一格**服务按生成次数计费：

- **标准版**：约 0.1-0.3 元/次
- **高级版**：约 0.3-0.8 元/次
- **定制版**：面议

**免费额度**：
- 新注册用户通常有少量免费测试额度
- 具体以官网政策为准

### 成本估算

假设每个仓库生成 5 张图（不同视角）：

- 单次生成：0.2 元
- 单仓库成本：5 × 0.2 = 1 元
- 100 个仓库：100 元

### 优化建议

1. **缓存机制** - 已生成的图像不重复生成
2. **批量生成** - 批量操作降低成本
3. **闲时生成** - 夜间自动生成，避免高峰
4. **混合架构** - 常用图本地生成，特殊图云端生成

## 常见问题

### Q1: 提示"API Key 无效"？

**A**: 检查以下几点：
- API Key 是否复制完整（无空格）
- 应用是否已创建并启用
- 是否选择了正确的服务（文心一格）

### Q2: 提示"余额不足"？

**A**: 
- 登录百度智能云控制台
- 进入"费用中心"
- 充值账户余额

### Q3: 生成速度慢？

**A**: 
- 检查网络连接
- 选择较低分辨率（512x512）
- 避免高峰时段

### Q4: 图像质量不理想？

**A**: 
- 优化提示词（更详细描述）
- 调整生成参数（steps 增加到 30-40）
- 使用更高分辨率
- 尝试不同风格

### Q5: 没有 .env 文件？

**A**: 在项目根目录创建：

```bash
# Windows PowerShell
New-Item -Path ".env" -ItemType File

# Linux/Mac
touch .env
```

然后编辑文件添加配置。

## 快速测试（无需配置）

如果只是想快速测试功能，可以使用以下临时方案：

### 使用示例图片

修改 `app/routes/ai_image_routes.py`，在测试函数中返回示例图片：

```python
@ai_image_bp.route('/api/test/')
@login_required
def test_api():
    # 返回示例图片（base64）
    return jsonify({
        'success': True,
        'images': ['data:image/png;base64,iVBORw0KG...'],
        'message': '示例图片（未配置 API）'
    })
```

### 使用占位图服务

```python
def generate_warehouse_image(self, prompt, ...):
    # 如果未配置 API，返回占位图
    if not self.api_key or not self.secret_key:
        return {
            'success': True,
            'images': [f'https://via.placeholder.com/1024x768?text={prompt[:50]}'],
            'message': '占位图（未配置 API）'
        }
    
    # 正常调用百度 API
    ...
```

## 下一步

配置完成后：

1. ✅ 测试 API 连接
2. ✅ 生成单张图像
3. ✅ 尝试批量生成
4. ✅ 优化提示词
5. ✅ 应用到实际场景

---

**需要帮助？** 
- 百度智能云客服：95198
- 技术支持邮箱：support@baidu.com
- 文档中心：https://cloud.baidu.com/doc/index.html
