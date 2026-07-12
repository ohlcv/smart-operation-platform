# SSH 密钥免密码登录服务器

## 概述

SSH 密钥是一种更安全、更方便的服务器登录方式。与密码登录相比:

- **更安全**: 密钥是 2048 位或 4096 位的加密,无法暴力破解
- **更方便**: 配置一次,永久免密码登录

---

## 快速上手(5分钟配置完成)

```bash
# 1. 检查是否已有密钥
ls -la ~/.ssh/

# 2. 生成新密钥(如没有)
ssh-keygen -t ed25519 -C "meow-mac"

# 3. 上传公钥到服务器
ssh-copy-id root@服务器IP

# 4. 验证免密码登录
ssh root@服务器IP

docker compose -f docker-compose.my.yml up -d --build
```

---

## 核心概念

### 密钥工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                      SSH 密钥配对原理                       │
└─────────────────────────────────────────────────────────────┘

  Mac 本地(客户端)                          服务器(远程)
  ─────────────────                        ──────────────

  ┌────────────────┐                      ┌────────────────┐
  │   id_ed25519    │                      │ authorized_keys │
  │   (私钥,保密)    │ ←─── 请求登录 ──────│   (公钥列表)    │
  │                 │ ─── 验证成功 ────→  │                │
  └────────────────┘                      └────────────────┘
       留在本地                                     服务器端

  ┌────────────────┐                      ┌────────────────┐
  │  id_ed25519.pub │ ←─── 上传 ────────→│ authorized_keys │
  │   (公钥,可公开)  │                      │                │
  └────────────────┘                      └────────────────┘
```

### 配对验证流程

```
1. Mac: "我要用私钥登录服务器"
2. 服务器: 随机生成一个数字,用公钥加密后发给 Mac
3. Mac: 用私钥解密,得到数字,发回给服务器
4. 服务器: 验证成功,允许登录 ✓
```

---

## 一、生成 SSH 密钥对

### 1.1 检查是否已有密钥

```bash
ls -la ~/.ssh/
```

**已有密钥的输出:**
```
-rw-------   1 meow  staff   411 Jun 12 20:31 id_ed25519        # 私钥 ✓
-rw-r--r--   1 meow  staff    97 Jun 12 20:31 id_ed25519.pub    # 公钥 ✓
-rw-r--r--   1 meow  staff  1760 Jul 12 13:31 known_hosts      # 服务器指纹
```

> **提示**: 如果已经有 `id_ed25519` 和 `id_ed25519.pub`,可以直接跳到上传公钥步骤。

### 1.2 生成新的密钥对

```bash
ssh-keygen -t ed25519 -C "备注信息"
```

**交互式输入(全部直接回车):**
```
Generating public/private ed25519 key pair.
Enter file in which to save the key (/Users/meow/.ssh/id_ed25519):  ← 直接回车
Enter passphrase (empty for no passphrase):                         ← 直接回车
Enter same passphrase again:                                         ← 直接回车
```

**⚠️ 重要: 第一个提示问保存路径时,直接按回车,不要输入任何内容!**

如果输入了其他内容(如 `ssh-copy-id root@150.158.53.137`),密钥会保存到当前目录而不是 `~/.ssh/`,导致后续无法使用。

### 1.3 密钥文件存放路径

| 文件 | 路径 | 权限 | 说明 |
|------|------|------|------|
| 私钥 | `~/.ssh/id_ed25519` | 600 | **保密!绝对不要上传或分享** |
| 公钥 | `~/.ssh/id_ed25519.pub` | 644 | 可公开,用于上传到服务器 |
| 服务器指纹 | `~/.ssh/known_hosts` | 644 | 自动记录已连接的服务器 |
| 授权列表 | 服务器 `~/.ssh/authorized_keys` | 600 | 存放所有授权的公钥 |

### 1.4 查看密钥内容

```bash
# 查看公钥(用于复制粘贴到服务器)
cat ~/.ssh/id_ed25519.pub

# 查看私钥(不要分享!)
cat ~/.ssh/id_ed25519

# 查看服务器指纹记录
cat ~/.ssh/known_hosts
```

---

## 二、上传公钥到服务器

### 2.1 自动方式(推荐)

```bash
ssh-copy-id 用户名@服务器IP
```

**完整示例:**
```bash
ssh-copy-id root@150.158.53.137
```

执行后会提示输入一次密码:
```
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/Users/meow/.ssh/id_ed25519.pub"
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
root@150.158.53.137's password:   ← 输入密码后回车

Number of key(s) added: 1         ← 成功!
```

### 2.2 手动方式

如果 `ssh-copy-id` 不可用,手动操作:

**步骤 1: 复制公钥内容**
```bash
cat ~/.ssh/id_ed25519.pub
# 输出: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... 备注
```

**步骤 2: 登录服务器**
```bash
ssh root@150.158.53.137
```

**步骤 3: 在服务器上执行**
```bash
# 创建 .ssh 目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 添加公钥(粘贴第一步复制的内容)
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...你的公钥" >> ~/.ssh/authorized_keys

# 设置权限
chmod 600 ~/.ssh/authorized_keys

# 退出服务器
exit
```

### 2.3 验证免密码登录

```bash
ssh root@150.158.53.137
```

**成功**: 直接登录,看到服务器欢迎信息,无密码提示
**失败**: 仍提示输入密码,见常见问题章节

---

## 三、SSH 连接管理

### 3.1 连接到服务器

```bash
# 基础连接
ssh 用户名@服务器IP

# 示例
ssh root@150.158.53.137
```

### 3.2 断开连接

```bash
# 方法 1: 输入 exit
exit

# 方法 2: 按 Ctrl+D
```

### 3.3 首次连接的主机密钥确认

首次连接新服务器时:
```
The authenticity of host '150.158.53.137' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxx.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

输入 `yes` 确认,主机指纹保存到 `~/.ssh/known_hosts`。

### 3.4 一句话命令执行

不进入交互式终端,直接执行命令后退出:

```bash
# 示例: 查看服务器磁盘使用
ssh root@150.158.53.137 "df -h"

# 示例: 查看服务器运行时间
ssh root@150.158.53.137 "uptime"
```

---

## 四、常见问题与解决

### 4.1 免密码登录不生效

**检查清单:**

```bash
# 1. 检查本地私钥权限
ls -l ~/.ssh/id_ed25519
# 应该是: -rw------- (600)

# 2. 检查服务器授权文件权限(在服务器上执行)
ssh root@150.158.53.137 "ls -la ~/.ssh/"
# authorized_keys 应该是: -rw------- (600)
# .ssh 目录应该是: drwx------ (700)

# 3. 如果权限不对,在服务器上执行:
ssh root@150.158.53.137 "chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

### 4.2 仍然提示输入密码

可能原因:

| 原因 | 解决方法 |
|------|----------|
| 公钥没有添加到服务器 | 重新执行 `ssh-copy-id` |
| 服务器权限不对 | 在服务器执行 `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys` |
| 密钥文件路径不对 | 检查 `~/.ssh/` 下是否有 `id_ed25519` 和 `id_ed25519.pub` |
| SSH 配置禁止密钥登录 | 检查服务器 `/etc/ssh/sshd_config` 中 `PubkeyAuthentication yes` |

### 4.3 首次连接报 Host key verification failed

```bash
# 方案 1: 删除旧的主机记录
ssh-keygen -R 150.158.53.137

# 方案 2: 手动删除 known_hosts 中的一行
nano ~/.ssh/known_hosts
# 删除对应的行,保存

# 然后重新连接
ssh root@150.158.53.137
```

### 4.4 密钥文件保存到错误位置

如果像之前一样把密钥保存到了当前目录:

```bash
# 1. 删除错误文件
rm ~/Desktop/Project/smart-operation-platform/ssh-copy-id\ root@150.158.53.137
rm ~/Desktop/Project/smart-operation-platform/ssh-copy-id\ root@150.158.53.137.pub

# 2. 重新生成到正确位置
ssh-keygen -t ed25519 -C "备注"

# 3. 上传到服务器
ssh-copy-id root@150.158.53.137
```

---

## 五、高级配置

### 5.1 SSH 配置文件(简化登录命令)

编辑 `~/.ssh/config`:

```bash
nano ~/.ssh/config
```

添加配置:
```
Host my-server
    HostName 150.158.53.137
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host aliyun
    HostName 120.25.12.34
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
```

保存后简化登录:
```bash
ssh my-server    # 等于 ssh root@150.158.53.137
ssh aliyun       # 等于 ssh ubuntu@120.25.12.34
```

### 5.2 批量管理多台服务器

```bash
nano ~/.ssh/config
```

```
# 通用配置
Host *
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3

# 服务器1
Host server1
    HostName 192.168.1.100
    User root

# 服务器2
Host server2
    HostName 192.168.1.101
    User admin
```

### 5.3 SCP 文件传输

```bash
# 上传到服务器
scp 本地文件 用户名@服务器IP:目标路径
scp /tmp/test.txt root@150.158.53.137:/home/

# 从服务器下载
scp 用户名@服务器IP:文件路径 本地目录
scp root@150.158.53.137:/var/log/nginx.log /tmp/

# 传输目录
scp -r 本地目录 用户名@服务器IP:目标路径
```

### 5.4 脚本中测试 SSH 连接

```bash
# 测试连接(非交互模式)
ssh -o ConnectTimeout=10 -o BatchMode=yes 用户名@服务器IP "echo OK"

# 退出码 0 = 成功, 255 = 失败
```

---

## 六、安全建议

| 建议 | 说明 |
|------|------|
| 保护私钥 | 不要上传到 Git、分享给他人、存放在网盘 |
| 为私钥设置 passphrase | 额外保护,即使文件泄露也需要密码 |
| 不同用途用不同密钥 | 工作用一个密钥,个人项目用一个 |
| 定期更换密钥 | 建议每 1-2 年更换一次 |
| 不要复用密钥 | 多个服务器用同一密钥,一个泄露全部危险 |

---

## 七、本项目中的应用

### 部署脚本工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                   智能运营平台部署流程                       │
└─────────────────────────────────────────────────────────────┘

  本地 Mac
  ─────────

  ./build-local.sh      ← 本地编译前端
       ↓
       /tmp/smart-ops.tar.gz (176MB)
       ↓
  ./deploy-server.sh    ← 自动上传部署
       ↓
  ┌──────────────────────────────────────┐
  │  SSH 免密码连接到服务器               │
  │  自动清理旧容器                       │
  │  上传部署包                           │
  │  解压 + 启动容器                      │
  └──────────────────────────────────────┘
       ↓
  部署完成! https://meowquant.site
```

### 本项目 SSH 配置

```bash
Host 150.158.53.137
    HostName 150.158.53.137
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

---

## 八、命令速查表

| 命令 | 说明 |
|------|------|
| `ssh-keygen -t ed25519 -C "备注"` | 生成密钥对 |
| `ssh-copy-id 用户@服务器IP` | 上传公钥到服务器 |
| `ssh 用户@服务器IP` | 连接服务器 |
| `exit` 或 `Ctrl+D` | 断开连接 |
| `scp 文件 用户@服务器IP:路径` | 上传文件 |
| `scp 用户@服务器IP:文件 路径` | 下载文件 |
| `ssh 用户@服务器IP "命令"` | 执行远程命令 |
| `ls -la ~/.ssh/` | 查看本地 SSH 文件 |
| `cat ~/.ssh/id_ed25519.pub` | 查看公钥内容 |
| `ssh-keygen -R 服务器IP` | 删除服务器指纹 |
| `nano ~/.ssh/config` | 编辑 SSH 配置 |
