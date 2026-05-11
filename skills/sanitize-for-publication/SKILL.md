---
name: sanitize-for-publication
description: Scan projects for sensitive information (API keys, personal data, local paths) before pushing to public repos. Covers file content scanning, git history auditing, .gitignore hardening, and rewriting history when needed.
---

# 项目脱敏 Skill

## 适用场景

准备将项目上传到公开仓库前，扫描并清除敏感信息：

- API 密钥、令牌、密码
- 个人信息（姓名、地址、健康档案、用户画像）
- 本地绝对路径（`C:\`、`D:\`、`/Users/`）
- 环境特定配置（`.env`、`settings.json`、凭据文件）
- Git 历史中已提交的敏感数据
- 不应公开的业务逻辑/策略细节

## 工作流

### 第一阶段：文件扫描

```bash
# 1. 扫描 API 密钥模式
git ls-files | xargs grep -l -E '[A-Za-z0-9_-]{20,}' 2>/dev/null | grep -v -E '\.(png|jpg|jpeg|gif|bmp|ico|svg|ttf|woff|woff2|eot|pyc|lock)$'

# 2. 扫描本地路径
git ls-files | xargs grep -l -E '([A-Z]:\\[^"'"'"'\n]*|/Users/[^/]+)' 2>/dev/null | grep -v -E '\.(png|jpg|jpeg|gif|bmp|ico|svg|ttf|woff|woff2|eot|pyc|lock)$'

# 3. 扫描 .env / credentials 类文件是否被追踪
git ls-files | grep -iE '\.env|credential|secret|token|\.key|\.pem|\.p12'
```

### 第二阶段：Git 历史审计

```bash
# 检查历史中是否有 .env 文件被提交
git log --all --diff-filter=A -- '.env' '*.env.*' '.token' 'credentials*'

# 检查历史中是否有 API 密钥模式
git log --all -p -S "sk-" -- '*.py' '*.json' '*.yaml' '*.yml' '*.toml' '*.cfg'

# 检查历史中是否有本地路径
git log --all -p -S "\\" -- '*.py' '*.md' '*.json' '*.cfg'
```

### 第三阶段：识别敏感文件清单

按风险等级分类：

| 等级 | 类别 | 示例 | 处理方式 |
|------|------|------|---------|
| 🔴 严重 | API 密钥/令牌 | `sk-*`、`ghp_*`、`AKIA*` | 必须清除历史 + 轮换密钥 |
| 🔴 严重 | 凭据文件 | `.env`、`credentials.json` | .gitignore + 清除历史 |
| 🟠 高 | 个人身份信息 | 姓名、地址、电话、健康档案 | 清除历史或删除文件 |
| 🟠 高 | 本地绝对路径 | `C:\Users\xxx`、`/Users/xxx` | 替换为占位符或环境变量 |
| 🟡 中 | 配置中的 URL/域名 | 内网地址、API 端点 | 替换为占位符 |
| 🟡 中 | 作者/提交者信息 | git config user 信息 | 使用 GitHub noreply 邮箱 |
| 🟢 低 | 注释中的路径 | 开发环境路径注释 | 清理注释 |
| 🟢 低 | 日志/缓存目录 | `__pycache__`、`.pytest_cache` | .gitignore + 从追踪中移除 |

### 第四阶段：选择清除策略

#### 方案 A：仅 1 个 commit（新建仓库）

```bash
# 1. 删除远程仓库
gh repo delete <owner>/<repo> --yes

# 2. 创建孤儿分支（丢弃全部历史）
git checkout --orphan clean-branch

# 3. 重新添加公开文件
git add <public-files>
git commit -m "Initial commit (sanitized)"

# 4. 重新创建仓库并推送
gh repo create <owner>/<repo> --public --source=. --remote=origin --push
```

#### 方案 B：多个 commit，需要保留历史

```bash
# 方案 B1：使用 git filter-branch 移除特定文件
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch <path/to/sensitive-file>' \
  --prune-empty --tag-name-filter cat -- --all

# 方案 B2：使用 git filter-repo（推荐，需先安装）
# pip install git-filter-repo
git filter-repo --path <sensitive-file> --invert-paths

# 方案 B3：替换字符串（如 API 密钥）
git filter-repo --replace-text <replacements.txt>
# replacements.txt 格式：
# sk-abc123def456==>sk-PLACEHOLDER
```

#### 方案 C：仅清理当前追踪，不碰历史

```bash
# 从追踪中移除但不删除本地文件
git rm -r --cached <directory>
git rm --cached <file>

# 加入 .gitignore
echo "<pattern>" >> .gitignore

# 提交
git add .gitignore
git commit -m "chore: remove sensitive files from tracking"
```

### 第五阶段：加固 .gitignore

根据扫描结果追加忽略规则：

```gitignore
# 凭据与密钥
.env
.env.*
*.key
*.pem
credentials.json
service-account.json

# 本地配置
settings.json
settings.local.json
.vscode/
.idea/
*.sublime-*

# 个人数据
memory/
notes/

# 缓存与构建
__pycache__/
*.pyc
.pytest_cache/
.superpowers/
.streamlit/

# 环境特定
venv/
.venv/
```

### 第六阶段：最终验证

```bash
# 验证不再有敏感文件被追踪
git ls-files | grep -iE '\.env|credential|secret|token'

# 验证 API 密钥模式不再出现
git ls-files | xargs grep -lE '[A-Za-z0-9_-]{20,}' 2>/dev/null | head -10

# 验证本地路径
git ls-files | xargs grep -lE '([A-Z]:\\|/Users/)' 2>/dev/null | head -10

# 验证可见性
gh repo view --json visibility
```

## 恢复操作

如果误清除：

```bash
# 从 git 的 reflog 找回引用
git reflog

# 恢复被 filter-branch 备份的原始引用
git checkout -b recovered-backup refs/original/refs/heads/main
```

## 注意事项

1. **先备份，再操作**：处理历史前备份整个仓库目录
2. **已泄露的密钥必须轮换**：删除提交历史不等于密钥安全，密钥已被公开过
3. **filter-repo 不可逆**：操作后需要所有协作者重新 clone
4. **大文件**：用 `git filter-repo --strip-blobs-bigger-than 10M` 清理大文件
5. **提交者信息**：`git filter-repo --name-callback 'return name.replace(b"旧用户名", b"新用户名")'`
