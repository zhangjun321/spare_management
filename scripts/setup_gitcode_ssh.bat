@echo off
chcp 65001
echo ========================================
echo GitCode SSH 密钥配置脚本
echo ========================================
echo.

echo [1/4] 生成 SSH 密钥...
ssh-keygen -t ed25519 -C "Orion41717654@noreply.gitcode.com" -f "%USERPROFILE%\.ssh\gitcode_ed25519" -N ""

echo.
echo [2/4] 显示公钥内容（请复制以下内容）...
echo ========================================
type "%USERPROFILE%\.ssh\gitcode_ed25519.pub"
echo ========================================
echo.

echo [3/4] 配置 SSH 配置文件...
(
echo Host gitcode.com
echo    HostName gitcode.com
echo    PreferredAuthentications publickey
echo    IdentityFile ~/%USERPROFILE%/.ssh/gitcode_ed25519
) > "%USERPROFILE%\.ssh\config"

echo.
echo [4/4] 添加 SSH 密钥到 ssh-agent...
start ssh-agent
ssh-add "%USERPROFILE%\.ssh\gitcode_ed25519"

echo.
echo ========================================
echo 配置完成！
echo ========================================
echo.
echo 下一步操作：
echo 1. 复制上面的公钥内容（以 ssh-ed25519 开头）
echo 2. 访问：https://gitcode.com/profile/keys
echo 3. 点击"添加 SSH 公钥"
echo 4. 粘贴公钥内容并保存
echo.
echo 然后运行：git push -u origin main
echo.
pause
