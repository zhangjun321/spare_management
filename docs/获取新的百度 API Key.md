# 百度千帆 API Key 获取指南

## 问题分析

您提供的 API Key 格式是 `bce-v3/ALTAK-xxx`，这是百度千帆的**新格式凭证**。

但是这个 Key 似乎已过期或无效（返回 "Access token invalid or no longer valid"）。

## 解决方案

### 方法 1：获取新的 API Key（推荐）

1. **访问百度千帆控制台**
   - 网址：https://console.bce.baidu.com/qianfan/
   - 使用百度账号登录

2. **创建/查看应用**
   - 点击左侧菜单 "应用管理"
   - 如果没有应用，点击"创建应用"
   - 填写应用名称和描述
   - 选择需要的服务（包括"文心一格"图像生成服务）

3. **获取 API Key 和 Secret Key**
   - 进入应用详情页
   - 找到"凭证信息"或"API Key"部分
   - 复制 `API Key` 和 `Secret Key`
   - **注意**：应该是两串不同的字符，不是 bce-v3 格式

4. **配置到项目**
   
   编辑 `.env` 文件：
   ```bash
   # 百度千帆 API 配置
   BAIDU_API_KEY=你的新 API_Key
   BAIDU_SECRET_KEY=你的新 Secret_Key
   ```

5. **重启服务器**
   - 停止当前运行的服务
   - 重新启动：`python start_server.py`

### 方法 2：使用安全认证页面的 AK/SK

1. **访问安全认证页面**
   - 网址：https://console.bce.baidu.com/iam/#/iam/security
   - 或从控制台 -> 用户头像 -> 安全认证 进入

2. **创建 Access Key**
   - 点击"新建 Access Key"
   - 系统会生成一对密钥：
     - `Access Key ID` (AK)
     - `Secret Access Key` (SK)
   - **重要**：立即复制并保存 SK，关闭页面后无法再查看

3. **配置到项目**
   ```bash
   BAIDU_API_KEY=你的 Access_Key_ID
   BAIDU_SECRET_KEY=你的 Secret_Access_Key
   ```

### 方法 3：检查现有 Key 是否有效

如果您认为现有的 Key 应该有效，可以：

1. **检查 Key 是否过期**
   - 登录千帆控制台
   - 查看应用状态是否正常
   - 检查账户是否欠费

2. **重置 API Key**
   - 在应用详情页
   - 点击"重置密钥"
   - 获取新的 API Key 和 Secret Key

## 验证配置

配置完成后，运行测试脚本：

```bash
python test_updated_service.py
```

如果显示 `[SUCCESS] Image generation successful!` 则配置成功。

## 常见问题

### Q: 为什么 bce-v3 格式的 Key 无效？

A: bce-v3 格式的 Key 通常是临时访问令牌，有效期较短（几小时到几天）。
建议使用应用管理页面获取的长期 API Key 和 Secret Key。

### Q: 免费额度是多少？

A: 
- 新注册用户通常有免费测试额度
- 文心一格服务一般有少量免费生成次数
- 具体额度请在控制台查看

### Q: 如何查看使用量？

A: 在千帆控制台 -> 费用中心 -> 用量统计 中查看

## 需要帮助？

- 百度智能云客服：95198
- 在线客服：https://cloud.baidu.com/support.html
