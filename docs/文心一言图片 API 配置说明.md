# 百度文心一言图片生成 API 配置说明

## ⚠️ 当前问题

错误信息：`unknown client id` / `invalid_client`

**原因**：百度文心一言的图片生成 API（SD-XL）需要使用**配对的 API Key 和 Secret Key**，而您目前只配置了 API Key。

## 🔑 获取 Secret Key 的步骤

### 方法一：百度智能云控制台（推荐）

1. **访问百度智能云控制台**
   - 网址：https://console.bce.baidu.com/aiplatform/

2. **进入应用列表**
   - 点击左侧菜单"应用管理"
   - 找到您创建的文心一言应用

3. **查看应用详情**
   - 点击应用名称
   - 在"应用信息"页面可以看到：
     - **API Key**（已有）
     - **Secret Key**（需要复制这个）

4. **配置到项目**
   - 复制 Secret Key
   - 添加到 `.env` 文件：
   ```
   BAIDU_SECRET_KEY=您的 Secret_Key
   ```

### 方法二：千帆大模型平台

如果您使用的是千帆平台：

1. **访问千帆平台**
   - 网址：https://console.bce.baidu.com/qianfan/

2. **进入应用管理**
   - 点击左侧"应用管理"
   - 找到您的应用

3. **获取凭证**
   - 点击"凭证管理"
   - 查看 API Key 和 Secret Key

## 📝 配置示例

编辑 `.env` 文件：

```bash
# 百度文心一言 API 配置
BAIDU_API_KEY=bce-v3/ALTAK-EVlLy1mZSq6rcJVi45qjo/ddb0f76edd018597420cfcee1dc32b50db3a1664
BAIDU_SECRET_KEY=这里填写您从控制台复制的 Secret Key
```

## 🔍 验证配置

配置完成后，运行测试脚本：

```bash
cd d:\Trae\spare_management
python scripts\test_auth.py
```

如果认证成功，会显示：
```
✅ Access Token 获取成功：xxxxx...
```

## ⚡ 快速测试

配置好 Secret Key 后，重新运行图片生成：

```bash
python scripts\generate_part_thumbnails.py
```

## 📞 常见问题

### Q1: 找不到 Secret Key 怎么办？
- 确保创建应用时选择了"文心一言"服务
- 检查应用状态是否为"启用"
- 联系百度智能云客服

### Q2: 有 API Key 但没有 Secret Key？
- 可能是旧版 API，需要重新创建应用
- 或者使用的是简化的认证方式（不支持图片生成）

### Q3: 图片生成是否需要额外权限？
- 是的，部分高级功能需要企业认证
- 个人开发者可以使用基础功能

## 🎯 替代方案

如果百度文心一言图片生成无法使用，可以考虑：

1. **通义万相**（阿里云）- 有免费额度
2. **腾讯混元** - 支持产品图片生成
3. **Stable Diffusion** - 开源免费，可本地部署

## 📞 联系支持

- 百度智能云客服：400-800-8888
- 在线工单：https://console.bce.baidu.com/iam/ticket
