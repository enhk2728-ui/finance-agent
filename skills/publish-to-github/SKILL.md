---
name: publish-to-github
description: Complete workflow to publish projects to GitHub — scan and remove sensitive info (API keys, personal data, local paths), audit git history, harden .gitignore, then create repo and push. Trigger on "上传到 GitHub""公开仓库""脱敏后上传"等。
---

# Publish to GitHub — 脱敏 + 上传

完整工作流：**扫描敏感信息 → 清除 → 创建仓库 → 推送**。一步到位。

---

## 第一阶段：扫描

### 1.1 文件扫描

```bash
# API 密钥/令牌
git ls-files | xargs grep -l -E '[A-Za-z0-9_-]{20,}' 2>/dev/null | grep -v -E '\.(png|jpg|jpeg|gif|bmp|ico|svg|ttf|woff|woff2|eot|pyc|lock)$'

# 本地路径（Windows / macOS）
git ls-files | xargs grep -l -E '([A-Z]:\\[^"'"'"'\n]*|/Users/[^/]+)' 2>/dev/null | grep -v -E '\.(png|jpg|jpeg|gif|bmp|ico|svg|ttf|woff|woff2|eot|pyc|lock)$'

# 被追踪的凭据/配置类文件
git ls-files | grep -iE '\.env|credential|secret|token|\.key|\.pem|\.p12|settings\.json'
```

### 1.2 Git 历史审计

```bash
# .env 是否曾被提交
git log --all --diff-filter=A -- '.env' '*.env.*'

# API 密钥模式是否出现在历史中
git log --all -p -S "sk-" -- '*.py' '*.json' '*.yaml' '*.yml' '*.toml'

# 本地路径是否出现在历史中
git log --all -p -S "\\" -- '*.py' '*.md' '*.json' | head -40
```

### 1.3 风险分级

| 等级 | 类别 | 示例 | 处理方式 |
|------|------|------|---------|
| 🔴 严重 | API 密钥/令牌 | `sk-*`、`ghp_*`、`AKIA*`、密码 | 清除历史 + 轮换密钥 |
| 🔴 严重 | 凭据文件 | `.env`、`credentials.json` | .gitignore + 清除历史 |
| 🟠 高 | 个人信息 | 姓名、地址、电话、健康档案 | 清除历史或删除文件 |
| 🟠 高 | 本地路径 | `C:\Users\xxx`、`/Users/xxx` | 替换为占位符/环境变量 |
| 🟡 中 | 内网地址 | 内网 API、IP、域名 | 替换为占位符 |
| 🟢 低 | 缓存/构建产物 | `__pycache__`、`.pytest_cache` | .gitignore + 取消追踪 |

---

## 第二阶段：清除

根据扫描结果选择方案。

### 方案 A：仅 1 个 commit（孤儿分支重建）

适用于仓库刚初始化、只有少量 commit 的场景。

```bash
# 1. 删除远程（如果已存在）
gh repo delete <owner>/<repo> --yes 2>/dev/null

# 2. 创建孤儿分支，丢弃全部历史
git checkout --orphan clean-branch

# 3. 重建 .gitignore（含脱敏规则）
cat > .gitignore << 'GITIGNORE'
# 凭据
.env
.env.*
*.key
*.pem
credentials.json

# 本地配置
settings.json
settings.local.json
.vscode/
.idea/

# 个人数据
memory/
notes/
private/

# 缓存与构建产物
__pycache__/
*.pyc
.pytest_cache/
.superpowers/
.streamlit/

# 环境
venv/
.venv/
dist/
build/
GITIGNORE

# 4. 添加公开文件
git add <public-files>   # 逐个添加，不要 git add -A
git commit -m "Initial commit (sanitized)"

# 5. 创建 GitHub 仓库并推送
gh repo create <owner>/<repo> --public --source=. --remote=origin --push
```

### 方案 B：多 commit，保留历史（git filter-repo）

```bash
# 安装
pip install git-filter-repo

# 移除特定文件
git filter-repo --path .env --path credentials.json --invert-paths

# 替换敏感字符串
echo "sk-abc123==>sk-PLACEHOLDER" > replacements.txt
git filter-repo --replace-text replacements.txt
```

### 方案 C：仅清理当前追踪

```bash
git rm -r --cached <dir>
echo "<pattern>" >> .gitignore
git add .gitignore
git commit -m "chore: 移除敏感文件追踪"
```

---

## 第三阶段：上传 GitHub

### 3.1 前置检查

```bash
# gh CLI 是否可用
gh --version

# 是否已认证
gh auth status
```

若未认证：

```bash
gh auth login
# 选择 "Login with a web browser"
# 复制 one-time code，打开 https://github.com/login/device 输入
```

### 3.2 创建仓库

```bash
# 公开仓库
gh repo create <owner>/<repo> --public --source=. --remote=origin --push

# 私有仓库
gh repo create <owner>/<repo> --private --source=. --remote=origin --push
```

> `<owner>/<repo>` 举例：`enhk2728-ui/gold-trading-assistant`。
> 如果当前目录已是 git 仓库，`--source=.` 会保留已有历史。

### 3.3 推送已有仓库（仓库已创建，尚未推送）

```bash
git remote add origin https://github.com/<owner>/<repo>.git
git branch -M main
git push -u origin main

# 如果有标签
git push --tags
```

### 3.4 设置代理（如在中国大陆）

```bash
# 配置 HTTP 代理（以 127.0.0.1:6738 为例）
git config http.proxy http://127.0.0.1:6738
git config https.proxy http://127.0.0.1:6738

# 验证
curl -I https://github.com --proxy http://127.0.0.1:6738
```

代理只需配置一次，保存在本地 git config 中，后续自动生效。

---

## 第四阶段：最终验证

```bash
# 验证可见性
gh repo view --json name,url,visibility

# 确认无敏感文件被追踪
git ls-files | grep -iE '\.env|credential|secret|token' || echo "✅ 无敏感文件"

# 确认无 API 密钥模式
git ls-files | xargs grep -lE '[A-Za-z0-9_-]{20,}' 2>/dev/null | head -5 || echo "✅ 无密钥模式"

# 确认无本地路径
git ls-files | xargs grep -lE '([A-Z]:\\|/Users/)' 2>/dev/null | head -5 || echo "✅ 无本地路径"
```

---

## 完整流程示例（黄金分析项目）

```bash
# 1. 扫描
git ls-files | xargs grep -lE 'sk-|AKIA|ghp_' 2>/dev/null
git log --all --diff-filter=A -- '.env'

# 2. 清除 — 方案 C（仅取消追踪 .env）
echo ".env" >> .gitignore
git rm -r --cached .env 2>/dev/null
git add .gitignore
git commit -m "chore: 移除 .env 追踪"
git push origin main

# 3. 设置代理
git config http.proxy http://127.0.0.1:6738
git config https.proxy http://127.0.0.1:6738

# 4. 创建仓库并推送
gh repo create enhk2728-ui/gold-trading-assistant --public --source=. --remote=origin --push
git push --tags

# 5. 验证
gh repo view --json name,url,visibility
```

---

## 补充操作

### 删除远程仓库

```bash
gh repo delete <owner>/<repo> --yes
```

### 已有仓库改可见性

```bash
gh repo edit <owner>/<repo> --visibility public --accept-visibility-change-consequences
gh repo edit <owner>/<repo> --visibility private --accept-visibility-change-consequences
```

### 从 Git 历史恢复误删内容

```bash
git checkout -b recovered refs/original/refs/heads/main
```

---

## 安全原则

1. **已泄露的密钥必须轮换**，删除历史不等于密钥安全
2. **先备份再操作** filter-repo，该操作不可逆
3. **不要用 `git add -A`** 重建仓库时，逐个确认要公开的文件
4. **提交者邮箱**使用 GitHub 的 noreply 邮箱：`用户名@users.noreply.github.com`
5. **memory/** 之类个人目录加 .gitignore，本地保留不影响公开仓库
