# Git 版本管理快速入门指南

## 📋 当前状态

✅ **本地 Git 仓库已初始化**
- 仓库位置：`D:\Trae\spare_management`
- 当前分支：`main`
- 最新提交：`feat: 初始版本 - 备件管理系统 v1.0.0`
- 提交数量：84 个文件

---

## 🚀 日常开发流程

### 1. 开始新功能

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline

# 创建并切换到新功能分支
git checkout -b feature/your-feature-name

# 例如：创建备件导入功能分支
git checkout -b feature/spare-part-import
```

### 2. 开发和提交

```bash
# 编辑代码后，添加更改
git add .                    # 添加所有更改
# 或
git add app/routes/spare_parts.py  # 添加特定文件

# 提交更改
git commit -m "feat(备件): 添加 Excel 导入功能"

# 推送到远程仓库（如果已配置）
git push -u origin feature/spare-part-import
```

### 3. 提交信息规范

**格式**：`type(scope): subject`

**常用类型**：
- `feat` - 新功能
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 代码格式
- `refactor` - 重构
- `test` - 测试
- `chore` - 构建/工具

**示例**：
```bash
git commit -m "feat(备件): 添加批量导入功能"
git commit -m "fix(库存): 修复库存计算错误"
git commit -m "docs: 更新 API 文档"
git commit -m "style(代码): 格式化 user.py"
git commit -m "refactor(用户): 重构认证逻辑"
```

---

## 🌿 分支管理

### 查看分支

```bash
# 查看本地分支
git branch

# 查看所有分支（包括远程）
git branch -a

# 当前所在分支会有 * 标记
```

### 切换分支

```bash
# 切换到现有分支
git checkout develop

# 切换并创建新分支
git checkout -b feature/new-feature
```

### 合并分支

```bash
# 切换到目标分支
git checkout main

# 合并功能分支
git merge feature/new-feature

# 解决冲突后（如果有）
git add .
git commit -m "merge: 合并新功能"
```

---

## 📊 查看和回滚

### 查看提交历史

```bash
# 简洁视图
git log --oneline

# 详细视图
git log

# 图形化视图
git log --graph --oneline --all
```

### 查看更改

```bash
# 查看工作区更改
git status

# 查看具体更改
git diff

# 查看某次提交的更改
git show <commit-id>
```

### 撤销更改

```bash
# 撤销工作区更改（未 add）
git checkout -- filename.py

# 撤销暂存区更改（已 add，未 commit）
git reset HEAD filename.py

# 撤销最后一次提交（已 commit，未 push）
git reset --soft HEAD~1

# 撤销并删除更改
git reset --hard HEAD~1
```

---

## 🔄 与远程仓库协作

### 添加远程仓库

```bash
# 添加 GitCode 远程仓库
git remote add origin https://gitcode.net/your-username/spare-parts-management.git

# 验证
git remote -v
```

### 推送代码

```bash
# 推送 main 分支
git push -u origin main

# 推送功能分支
git push -u origin feature/your-feature

# 推送所有分支
git push --all origin

# 推送标签
git push --tags origin
```

### 拉取代码

```bash
# 拉取并合并
git pull origin main

# 仅下载不合并
git fetch origin

# 查看远程分支
git fetch origin
git branch -r
```

---

## 🏷️ 版本标签

### 创建标签

```bash
# 创建轻量标签
git tag v1.0.0

# 创建附注标签（推荐）
git tag -a v1.0.0 -m "发布版本 v1.0.0"
```

### 查看标签

```bash
# 查看所有标签
git tag

# 查看标签详情
git show v1.0.0
```

### 推送标签

```bash
# 推送单个标签
git push origin v1.0.0

# 推送所有标签
git push --tags origin
```

---

## 🔧 常见问题解决

### Q1: 提交时提示文件未跟踪

```bash
# 添加文件到 Git
git add <filename>

# 或添加所有文件
git add .
```

### Q2: 合并冲突

```bash
# 1. 查看冲突文件
git status

# 2. 编辑冲突文件，解决冲突标记
# <<<<<<< HEAD
# 你的更改
# =======
# 他人的更改
# >>>>>>>

# 3. 标记为解决
git add <resolved-file>

# 4. 完成合并
git commit -m "merge: 解决冲突"
```

### Q3: 误删文件

```bash
# 恢复被删除的文件
git checkout -- <filename>

# 或
git restore <filename>
```

### Q4: 查看谁修改了某行代码

```bash
# 使用 git blame
git blame -L 10,20 filename.py

# 查看第 10-20 行的修改历史
```

---

## 📁 备份和恢复

### 手动备份

```bash
# 运行备份脚本
cd D:\Trae\spare_management\scripts
backup.bat
```

### 从备份恢复

```bash
# 运行恢复脚本
cd D:\Trae\spare_management\scripts
restore.bat E:\Backup\spare_management\spare_management_backup_20260318.zip
```

### Git 恢复

```bash
# 从远程仓库恢复
git clone https://gitcode.net/your-username/spare-parts-management.git
```

---

## 📝 最佳实践

### ✅ 应该做的

1. **频繁提交**：每完成一个小功能就提交
2. **清晰的提交信息**：说明做了什么和为什么
3. **使用分支**：新功能在独立分支开发
4. **及时拉取**：开始工作前先拉取最新代码
5. **代码审查**：合并前进行 Code Review
6. **备份代码**：定期运行备份脚本

### ❌ 不应该做的

1. **不要提交敏感信息**：密码、密钥、配置文件
2. **不要直接推送到 main**：通过 MR/PR 合并
3. **不要提交大文件**：使用 Git LFS 或外部存储
4. **不要忽略冲突**：立即解决合并冲突
5. **不要强制推送**：除非你确定后果

---

## 🛠️ Git 配置

### 查看配置

```bash
# 查看所有配置
git config --list

# 查看全局配置
git config --global --list

# 查看当前仓库配置
git config --local --list
```

### 修改配置

```bash
# 修改用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 修改默认分支
git config --global init.defaultBranch main

# 设置换行符（Windows）
git config --global core.autocrlf true
```

---

## 📞 获取帮助

```bash
# 查看 Git 帮助
git help

# 查看具体命令帮助
git help <command>
# 例如
git help commit
git help merge
```

---

## 🎯 下一步

1. **注册 GitCode 账号**：https://gitcode.net/
2. **创建远程仓库**：创建私有仓库 `spare-parts-management`
3. **关联远程仓库**：
   ```bash
   git remote add origin https://gitcode.net/your-username/spare-parts-management.git
   git push -u origin main
   ```
4. **配置 SSH 密钥**（可选但推荐）：
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   ```

---

**文档版本**: v1.0.0  
**创建日期**: 2026-03-18  
**最后更新**: 2026-03-18
