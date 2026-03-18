# GitCode 配置指南

## 📋 您的 GitCode 信息

- **用户名**: `Orion41717654`
- **仓库地址**: `https://gitcode.com/Orion41717654/spare_parts_management`
- **邮箱**: `Orion41717654@noreply.gitcode.com`
- **远程仓库**: 已配置

---

## 🔑 配置 SSH 密钥（推荐）

### 步骤 1：生成 SSH 密钥

打开 **Git Bash** 或 **PowerShell**，运行：

```bash
ssh-keygen -t ed25519 -C "Orion41717654@noreply.gitcode.com"
```

**提示输入时直接按回车**（使用默认设置）

### 步骤 2：查看并复制公钥

```bash
cat ~/.ssh/id_ed25519.pub
```

**复制输出内容**（以 `ssh-ed25519` 开头的完整一行）

### 步骤 3：添加到 GitCode

1. 访问：https://gitcode.com/profile/keys
2. 点击 **"添加 SSH 公钥"**
3. 粘贴刚才复制的公钥内容
4. 标题填写：`My Computer`
5. 点击 **"确定"**

### 步骤 4：测试连接

```bash
ssh -T git@gitcode.com
```

如果看到欢迎信息，说明配置成功！

---

## 🚀 推送代码到 GitCode

### 方法一：使用 SSH（推荐）

```bash
# 切换到 main 分支
cd D:\Trae\spare_management
git branch -M main

# 推送代码
git push -u origin main
```

### 方法二：使用 HTTPS

```bash
# 切换到 main 分支
cd D:\Trae\spare_management
git branch -M main

# 推送代码（会提示输入用户名和密码）
git push -u origin main
```

**用户名**: `Orion41717654`  
**密码**: 您的 GitCode 登录密码（或访问令牌）

---

## 📝 验证配置

### 查看远程仓库

```bash
git remote -v
```

应该显示：
```
origin  https://gitcode.com/Orion41717654/spare_parts_management.git (fetch)
origin  https://gitcode.com/Orion41717654/spare_parts_management.git (push)
```

### 查看当前分支

```bash
git branch
```

应该显示：
```
* main
```

### 查看提交历史

```bash
git log --oneline
```

应该显示您的 3 次提交。

---

## 🔄 日常使用

### 推送代码

```bash
# 提交更改后
git add .
git commit -m "feat: 添加新功能"
git push origin main
```

### 拉取代码

```bash
git pull origin main
```

### 查看状态

```bash
git status
```

---

## ⚠️ 常见问题

### Q1: 推送时提示 403 错误

**解决方案 1**：使用 SSH 方式（推荐）
```bash
# 更改远程仓库为 SSH 地址
git remote set-url origin git@gitcode.com:Orion41717654/spare_parts_management.git
git push -u origin main
```

**解决方案 2**：使用访问令牌
- 访问：https://gitcode.com/profile/tokens
- 创建个人访问令牌
- 使用令牌代替密码

### Q2: 找不到 SSH 密钥

```bash
# 检查是否存在
ls -la ~/.ssh/

# 重新生成
ssh-keygen -t ed25519 -C "Orion41717654@noreply.gitcode.com"
```

### Q3: 权限被拒绝

确保：
1. SSH 公钥已正确添加到 GitCode
2. 您是仓库的成员或所有者
3. SSH 配置文件正确（~/.ssh/config）

---

## 📞 获取帮助

- **GitCode 文档**: https://help.gitcode.com/
- **SSH 配置指南**: https://help.gitcode.com/ssh.html
- **仓库管理**: https://help.gitcode.com/repo/

---

**配置日期**: 2026-03-18  
**文档版本**: v1.0.0
