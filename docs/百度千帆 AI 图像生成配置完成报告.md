# 百度千帆 AI 图像生成配置完成报告

## ✅ 配置成功！

您提供的新 API Key 已成功配置并测试通过。

---

## 🎯 完成的配置

### 1. API Key 配置
- **位置**: `d:\Trae\spare_management\.env`
- **API Key**: `bce-v3/ALTAK-pZgpOBUYyuTHH8cixa6n6/4eb0a45244d35100b8f413e9c1cdfb533b44ac75`
- **格式**: BCE-V3（新格式）
- **状态**: ✅ 已验证有效

### 2. 服务集成方式
- **方法**: 使用 OpenAI SDK 调用百度千帆 API
- **模型**: `qwen-image`
- **SDK**: `openai` Python 库（已安装）

### 3. 代码修改
修改了 `app/services/baidu_image_service.py`:
- ✅ 使用 OpenAI SDK 替代了旧的 requests 方式
- ✅ 支持 BCE-V3 格式的 API Key
- ✅ 配置了正确的 API 端点：`https://qianfan.baidubce.com/v2`
- ✅ 优化了参数配置（steps, guidance, negative_prompt 等）

### 4. 配置文件
创建了 `app/config.py`:
- ✅ Flask 应用配置
- ✅ 数据库连接配置
- ✅ Redis 配置
- ✅ 日志配置

---

## 🧪 测试结果

### 测试脚本
运行 `test_new_sdk.py` 的结果：

```
API Key configured: True
API Key format: BCE-V3
[INFO] 百度千帆 OpenAI 客户端初始化成功

[OK] OpenAI 客户端初始化成功！

Testing Image Generation:
[SUCCESS] 图像生成成功！
图像数量：1
图像 URL: http://qianfan-modelbuilder-img-gen.bj.bcebos.com/...
```

### 服务器状态
- ✅ 服务器已启动
- ✅ 地址：http://127.0.0.1:5000
- ✅ AI 图像生成页面：http://127.0.0.1:5000/ai-image/
- ✅ 百度千帆客户端初始化成功

---

## 🚀 如何使用

### 1. 访问 AI 图像生成页面
打开浏览器，访问：
```
http://127.0.0.1:5000/ai-image/
```

### 2. 选择仓库
从下拉列表中选择一个仓库

### 3. 设置生成参数
- **图像风格**: 写实风格
- **视角焦点**: 自动选择
- **分辨率**: 1024x1024（高清）

### 4. 点击"生成图像"
等待几秒钟，AI 将自动生成仓库实景图

### 5. 批量生成（可选）
点击"批量生成（5 个视角）"按钮，一次生成 5 张不同角度的图像

---

## 📊 功能特性

### 支持的生成参数
- **prompt**: 自动根据仓库数据生成提示词
- **negative_prompt**: 自动添加负面描述（模糊、低质量等）
- **style**: 
  - photorealistic（写实）- guidance: 4
  - anime（动漫）- guidance: 7
  - artistic（艺术）- guidance: 5
- **resolution**: 可调整（512x512, 1024x1024 等）
- **steps**: 生成步数（默认 50）
- **prompt_extend**: 自动扩展提示词（已启用）

### 图像生成流程
1. 用户选择仓库和参数
2. 系统自动构建仓库描述提示词
3. 调用百度千帆 API
4. 返回生成的图像 URL
5. 在页面中展示结果

---

## 💰 费用说明

### 百度千帆定价
- **新注册用户**: 通常有免费测试额度
- **按量计费**: 约 0.1-0.3 元/张（根据分辨率）
- **查看用量**: 登录千帆控制台 -> 费用中心 -> 用量统计

### 优化建议
1. **缓存机制**: 已生成的图像不重复生成
2. **批量操作**: 批量生成可降低成本
3. **闲时生成**: 夜间自动生成，避免高峰

---

## 🔧 技术细节

### API 调用方式
```python
from openai import OpenAI

client = OpenAI(
    base_url='https://qianfan.baidubce.com/v2',
    api_key='bce-v3/ALTAK-xxx'
)

response = client.images.generate(
    model="qwen-image",
    prompt="现代化仓库内部，整洁有序，高清摄影",
    size="1024x1024",
    n=1,
    extra_body={
        "steps": 50,
        "guidance": 4,
        "negative_prompt": "模糊，低质量",
        "prompt_extend": True
    }
)
```

### 响应处理
```python
if response.data and len(response.data) > 0:
    image_url = response.data[0].url
    # 返回图像 URL
```

---

## ⚠️ 注意事项

### 1. API Key 安全
- ✅ 已保存在 `.env` 文件中
- ✅ 不会提交到版本控制
- ⚠️ 不要分享给他人

### 2. 账户余额
- 定期检查账户余额
- 避免欠费导致服务中断
- 可在千帆控制台设置余额预警

### 3. 图像质量
- 提示词质量影响生成效果
- 可适当调整 steps 参数（建议 30-50）
- 不同风格需要不同的 guidance 值

---

## 🐛 故障排查

### 问题 1: 提示"客户端未初始化"
**原因**: API Key 未配置或 openai 库未安装  
**解决**: 
```bash
# 检查 .env 文件
pip install openai
```

### 问题 2: 提示"Access token invalid"
**原因**: API Key 过期或无效  
**解决**: 重新获取新的 API Key

### 问题 3: 生成速度慢
**原因**: 网络或服务器负载高  
**解决**: 
- 检查网络连接
- 选择较低分辨率
- 避免高峰时段

### 问题 4: 图像质量不理想
**原因**: 提示词不够准确  
**解决**:
- 优化提示词描述
- 调整 steps 参数（增加到 50-70）
- 尝试不同风格

---

## 📞 支持资源

### 百度千帆官方
- **控制台**: https://console.bce.baidu.com/qianfan/
- **文档**: https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html
- **客服**: 95198

### 项目相关
- **测试脚本**: `test_new_sdk.py`
- **服务代码**: `app/services/baidu_image_service.py`
- **路由代码**: `app/routes/ai_image_routes.py`

---

## ✨ 下一步

1. ✅ 测试单张图像生成
2. ✅ 测试批量生成
3. ✅ 优化提示词
4. ✅ 应用到实际仓库场景
5. ✅ 添加图像缓存机制

---

**配置完成时间**: 2026-04-05  
**配置状态**: ✅ 成功  
**服务器状态**: ✅ 运行中  
**API 状态**: ✅ 正常

🎉 恭喜！您现在可以使用 AI 图像生成功能了！
