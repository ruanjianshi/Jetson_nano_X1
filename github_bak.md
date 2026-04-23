好的，已将完整的 Git 上传流程、连接超时排查及解决方案整理为 Markdown 文档，便于保存和查阅。

```markdown
# 将本地代码上传至 GitHub 仓库完整指南

> 适用于仓库地址：`https://github.com/ruanjianshi/Jetson_nano_X1.git`

## 一、基础上传步骤

### 情况 1：本地还没有 Git 仓库（全新项目）

```bash
# 1. 进入项目目录
cd /你的/项目/路径

# 2. 初始化本地仓库
git init

# 3. 添加所有文件到暂存区
git add .

# 4. 提交第一个版本
git commit -m "first commit"

# 5. 重命名分支为 main（GitHub 推荐）
git branch -M main

# 6. 关联远程仓库
git remote add origin https://github.com/ruanjianshi/Jetson_nano_X1.git

# 7. 推送至 GitHub（-u 设置默认上游分支）
git push -u origin main
```

### 情况 2：本地已有 Git 仓库，仅需关联远程

```bash
# 1. 进入已有仓库目录
cd /你的/项目/路径

# 2. 查看当前远程配置（可选）
git remote -v

# 3. 添加远程地址（若已存在 origin，可先删除：git remote remove origin）
git remote add origin https://github.com/ruanjianshi/Jetson_nano_X1.git

# 4. 确保本地分支名为 main（旧仓库若为 master，需重命名）
git branch -M main

# 5. 推送
git push -u origin main
```

---

## 二、常见问题处理

### 1. 认证方式说明

- **HTTPS 地址**：推送时需要输入用户名和 **Personal Access Token (PAT)**，而非网站登录密码。
- **SSH 地址**：需提前配置 SSH 公钥（见后文），推送时无需输入密码。

### 2. 远程仓库已有内容冲突

若 GitHub 上已存在 README.md 等文件，推送前需先合并：

```bash
git pull origin main --allow-unrelated-histories
# 解决冲突后
git push -u origin main
```

### 3. 忽略不需要上传的文件

在项目根目录创建 `.gitignore` 文件，写入规则示例：

```
__pycache__/
*.pyc
*.log
.env
*.pth
*.tar
```

---

## 三、推送无响应 / 超时排查（针对 Jetson Nano 等设备）

### 错误示例

```
fatal: unable to access 'https://github.com/...': Operation timed out after 300002 milliseconds with 0 out of 0 bytes received
```

### 步骤 1：测试网络连通性

```bash
# 检查 DNS 解析
nslookup github.com

# 检查 HTTPS 443 端口是否可达
curl -v https://github.com
```

- 若 `nslookup` 无响应 → DNS 问题。
- 若 `curl` 长时间卡住 → 防火墙/网络阻断。

### 步骤 2：根据测试结果修复

#### 修复 DNS 解析失败

```bash
sudo sh -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
sudo sh -c 'echo "nameserver 114.114.114.114" >> /etc/resolv.conf'
```

#### 配置 Git 使用代理（如有代理环境）

```bash
# 假设代理地址为 http://127.0.0.1:7890（替换为实际端口）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

取消代理：
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

#### 强制使用 IPv4（IPv6 路由异常时）

```bash
git config --global http.version HTTP/1.1
```

### 步骤 3：终极方案 —— 切换为 SSH 协议

**3.1 生成 SSH 密钥并添加至 GitHub**

```bash
# 生成密钥（一路回车）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 查看公钥内容（全选复制）
cat ~/.ssh/id_ed25519.pub
```

登录 GitHub → Settings → SSH and GPG keys → New SSH key，粘贴公钥保存。

**3.2 修改远程地址为 SSH**

```bash
git remote set-url origin git@github.com:ruanjianshi/Jetson_nano_X1.git
```

**3.3 测试 SSH 连接**

```bash
ssh -vT git@github.com
```

若显示 `You've successfully authenticated` 即表示成功。

**3.4 重新推送**

```bash
git push -u origin main
```

### 步骤 4：系统时间同步

SSL 证书验证依赖正确时间，若时间偏差过大也会导致连接失败。

```bash
# 查看当前时间
date

# 安装 ntpdate 并同步时间
sudo apt install ntpdate -y
sudo ntpdate ntp.ubuntu.com
```

---

## 四、附录：Git 常用操作速查

| 操作 | 命令 |
|------|------|
| 查看提交历史 | `git log --oneline` |
| 退出 `git log` 分页 | 按 `q` |
| 显示推送进度 | `git push --progress` |
| 查看远程仓库信息 | `git remote show origin` |
| 强制覆盖远程分支 | `git push -u origin main --force`（⚠️ 慎用） |

---

> **提示**：在 Jetson Nano 等性能有限的设备上推送大文件（如模型权重）时，即使网络正常也可能耗时较长。建议使用 `git push --progress` 观察传输状态，耐心等待。
```