# DEBUG-20260712-01 孤儿 ruoyi-network 导致 docker compose up 失败 + 误触发自动 build

| 项目     | 内容                                                          |
| -------- | ------------------------------------------------------------- |
| 文档编号 | DEBUG-20260712-01                                             |
| 类别     | Docker / 启动脚本 / 资源归属 / DEBUG（**修复未完结**）        |
| 严重度   | 🟠 P1（本地 docker 模式首次启动失败；老环境清理后能跑但有副作用） |
| 状态     | ⚠️ **部分修复**（cleanup 工具已就绪 + 脚本职责已划清；start-dev.sh 的 `ensure_clean` 待补） |
| 涉及版本 | smart-operation-platform @ 2026-07-12                         |
| 发现人   | 开发自检 (`./start-dev.sh --docker` 跑出 28.1s 自动构建，疑似浪费) |
| 修复人   | 开发自检                                                       |
| 关联脚本 | [`start-dev.sh`](../../../start-dev.sh)、[`stop-dev.sh`](../../../stop-dev.sh)、[`docker-compose.my.yml`](../../../docker-compose.my.yml)、[`docker-compose.pg.yml`](../../../docker-compose.pg.yml)、[`scripts/cleanup-orphan-network.sh`](../../../scripts/cleanup-orphan-network.sh) |
| 前置 commit | `3d30967 chore(network): ruoyi-network 改 external...`（**部分正确**） |

---

## 目录（Table of Contents）

1. [现象（Symptoms）](#1-现象symptoms)
2. [排查过程（Investigation）](#2-排查过程investigation)
3. [修复（Fix）](#3-修复fix)
4. [当前代码现状（As-Is）](#4-当前代码现状as-is)
5. [影响面（Impact）](#5-影响面impact)
6. [待补改进（Follow-ups）](#6-待补改进follow-ups)
7. [经验教训（Lessons Learned）](#7-经验教训lessons-learned)
8. [附录（Appendix）](#8-附录appendix)

---

## 1. 现象（Symptoms）

执行 `./start-dev.sh --docker`，出现下述输出（关键信息已加粗）：

```
========================================
  Docker 容器模式
========================================

[STEP]  互斥检查：停止所有本地进程...
  ✓ 无冲突
[STEP]  清理旧容器并启动（不重建镜像）...
[INFO]    启动容器（复用本地镜像）...
WARN[0000] a network with name ruoyi-network exists but was not created by compose.
Set `external: true` to use an existing network
network ruoyi-network was found but has incorrect label com.docker.compose.network set to "" (expected: "ruoyi-network")
exit status 1                                       ← compose 拒绝
[WARN]   启动失败（很可能是镜像不存在），尝试自动构建一次...    ← start-dev.sh 的 fallback
[+] Building 28.1s (7/8)                            ← 用户看到的"白构建"
```

观察到的真正问题：

- **`docker compose up` 完全没成功起容器**，但 `start-dev.sh` 把失败归因为"镜像不存在"并自动触发 `docker compose up -d --build`，白白跑了一次 28s 的 `pip install`
- 服务器 `docker images` 显示 `ruoyi-backend-my:latest` 和 `ruoyi-frontend:latest` **都已存在**
- 同样的失败复现 100%（每次 `start-dev.sh --docker` 都重新构建）

---

## 2. 排查过程（Investigation）

### 2.1 现场取证

服务器上看到的网络：

```bash
$ docker network ls --format '{{.Name}} {{.Labels "com.docker.compose.network"}}' \
  | grep '^ruoyi-network'
ruoyi-network                  ← 值为空，说明无标签
```

复现成功。说明：**网络是"无 compose 标签的孤儿网络"**——存在，但不被 compose 视为己有。

### 2.2 根因（Root Cause）

`start-dev.sh`（历史版本）在 `docker compose up` 之前有这段：

```bash
# ---- 创建 Docker 网络（不存在则创建） ----
if ! docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx "ruoyi-network"; then
  log_info "  创建 ruoyi-network..."
  docker network create ruoyi-network > /dev/null 2>&1   # ← 罪魁
fi
```

`docker network create ruoyi-network` 创建出来的网络**不带任何标签**——尤其是缺 `com.docker.compose.network` 这个关键标签。

紧接着 `docker compose -f docker-compose.my.yml up -d` 跑起来，compose 看到：

1. 网络 `ruoyi-network` 已经存在
2. 但没有 `com.docker.compose.network=ruoyi-network` 标签
3. compose 配置文件里 `external: true`（commit 3 的当前状态）
4. 判定："网络存在但不是我创建的，不予接管" → 拒绝 → exit 1

### 2.3 commit 3 的"修复"为什么只对了一半

第一轮响应（commit `3d30967`）我把 `docker-compose.my.yml` 和 `docker-compose.pg.yml` 的网络段改成 `external: true` —— 这个改动本身是**对的方向**（生产环境与本地解耦、本地网络由运维/脚本负责），但**没解决真正问题**：

- ✅ 配置文件层面：声明 `external: true` 让 compose 不再尝试创建网络
- ❌ 启动流程层面：`start-dev.sh` 仍然在 compose up 前**裸 `docker network create`**，仍会留下无标签网络
- ❌ 失败诊断层面：`start-dev.sh` 的 fallback 把所有 `up` 失败都归因为"镜像不存在"，触发 28s 白构建

也就是说，commit 3 之后，**首次在干净服务器上跑**仍会失败——只是失败后不再误导成"镜像不存在"，而是**干脆失败**（因为 `external: true` 让 compose 完全忽略网络段）。

### 2.4 为什么 fallback 触发了自动 build（历史行为）

`start-dev.sh` 第 388-390 行（**注：commit 3 之前的旧版本**）：

```bash
if ! docker compose -f "$DOCKER_COMPOSE_FILE" up -d; then
  log_warn "  启动失败（很可能是镜像不存在），尝试自动构建一次..."
  docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build
fi
```

逻辑假定 `up` 失败的最大概率是"镜像不存在"。网络冲突、配置错误这类原因**也被无差别归入这个分支**，导致每次网络问题都白构建一次（28s+）。

> 当前 `start-dev.sh` 的实际行为：commit 3 之后，**`external: true` + 启动脚本仍裸 `docker network create` 的组合**让 compose up 直接 exit 1，且**因为没有合适的 fallback**，错误信息可能更隐晦。

### 2.5 链路总图

```
start-dev.sh --docker
    │
    ├─ 检查 ruoyi-network
    │   不存在 ↓
    │   docker network create ruoyi-network   ← ✗ 无 compose 标签
    │
    ├─ docker compose -f docker-compose.my.yml up -d
    │   └─ external: true + 网络存在但无标签
    │       compose 报 "incorrect label"，exit 1
    │
    └─ fallback: docker compose ... up -d --build   ← ✗ 白构建 28s+
       （commit 3 后行为可能略有不同，但本质上仍不正确）
```

---

## 3. 修复（Fix）

### 3.1 修复策略（双管齐下 + 防御层）

| 维度 | 措施 | 落地状态 |
|------|------|---------|
| 运维工具 | 新增 `scripts/cleanup-orphan-network.sh`：手动清理"无标签孤儿网络"，**生产标签网络被自动放过** | ✅ 已落地（commit 3） |
| 启动脚本 fallback | `start-dev.sh` 应区分"缺镜像失败" vs "其他失败"，不再无差别 `--build` | 🔲 TODO（待补） |
| 启动前自检 | `start-dev.sh` 新增 `ensure_clean_ruoyi_network` 函数：检测到无标签孤儿网络自动清理 | 🔲 TODO（待补） |
| local mode 网络创建 | 脚本创建网络时**带 compose 标签**（`--label com.docker.compose.network=...`），与 compose 兼容 | 🔲 TODO（待补） |
| docker mode 网络创建 | **完全让 compose 接管**，脚本不预创建网络（依赖 `external: false`） | ⚠️ 半完成：现在 `external: true`，由脚本或运维预创建 |

### 3.2 已落地的改动

#### 3.2.1 ✅ `scripts/cleanup-orphan-network.sh`（运维工具）

```bash
NET_NAME="ruoyi-network"

if ! docker network ls --format '{{.Name}}' | grep -qx "$NET_NAME"; then
  echo "[OK] $NET_NAME 不存在，无需清理"
  exit 0
fi

# 检查是否有容器还在用（生产容器不能误删）
USING=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$NET_NAME" 2>/dev/null | xargs)
if [ -n "$USING" ]; then
  echo "[ERROR] $NET_NAME 仍被容器占用: $USING"
  echo "        请先停掉这些容器再重试"
  exit 1
fi

# 检查是否是 compose 创建的（带标签 = 生产）
LABEL=$(docker network inspect -f '{{index .Labels "com.docker.compose.network"}}' "$NET_NAME" 2>/dev/null || echo "")
if [ -n "$LABEL" ]; then
  echo "[OK] $NET_NAME 是生产 compose 网络，跳过清理"
  exit 0
fi

# 真正的孤儿：删
echo "[WARN] $NET_NAME 是无标签孤儿网络，清理中..."
docker network rm "$NET_NAME"
echo "[OK] $NET_NAME 已清理"
```

**使用**：在服务器上手动跑一次：

```bash
sudo bash scripts/cleanup-orphan-network.sh
# 输出：[WARN] ruoyi-network 是无标签孤儿网络，清理中...
#       [OK]   ruoyi-network 已清理
```

#### 3.2.2 ✅ `docker-compose.{my,pg}.yml` 网络段：`external: true`

```yaml
networks:
  ruoyi-network:
    name: ruoyi-network
    external: true
```

- 表达"网络由外部管理（运维 / 启动脚本）"
- compose up 不再尝试创建 / 删除网络
- 生产 compose (`docker-compose.server.yml`) 与本地 compose 共用网络名时不冲突

#### 3.2.3 ✅ `stop-dev.sh` 不再删除网络

```bash
# 删本地项目专属网络（不影响其他项目同名网络）
# 已删除整段（原代码行：docker network rm ruoyi-network）
# 网络 ruoyi-network 不再在此处删除（external: true，可能生产在用）
```

### 3.3 待补的改动（**当前未落地**，属 §6 TODO）

#### 3.3.1 🔲 `start-dev.sh` 增加 `ensure_clean_ruoyi_network`

```bash
ensure_clean_ruoyi_network() {
  local net_name="ruoyi-network"
  if ! docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx "$net_name"; then
    return 0   # 不存在 → 让 compose / 后续脚本自己建
  fi

  local using
  using=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$net_name" 2>/dev/null | xargs)
  if [ -n "$using" ]; then
    log_warn "  $net_name 仍被容器占用: $using"
    log_warn "    请先停掉这些容器（生产容器不要用本脚本停），再重试"
    return 1
  fi

  local label
  label=$(docker network inspect -f '{{index .Labels "com.docker.compose.network"}}' "$net_name" 2>/dev/null || echo "")
  if [ -n "$label" ]; then
    return 0   # 带 compose 标签 → 合法保留
  fi

  log_warn "  发现孤儿网络 $net_name（无 compose 标签），自动删除..."
  docker network rm "$net_name" > /dev/null 2>&1 || return 1
  return 0
}
```

#### 3.3.2 🔲 local mode 网络创建时带标签

```bash
ensure_clean_ruoyi_network
if ! docker network ls --format '{{.Name}}' 2>/dev/null | grep -qx "ruoyi-network"; then
  log_info "  创建 ruoyi-network（带 compose 标签）..."
  docker network create \
    --label com.docker.compose.project=ruoyi \
    --label com.docker.compose.network=ruoyi-network \
    ruoyi-network > /dev/null 2>&1
fi
```

#### 3.3.3 🔲 docker mode fallback 区分"缺镜像" vs "其他错误"

```bash
# 旧逻辑（无差别 fallback）：
if ! docker compose -f "$DOCKER_COMPOSE_FILE" up -d; then
  log_warn "  启动失败（很可能是镜像不存在），尝试自动构建一次..."
  docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build
fi

# 新逻辑（按错误类型 fallback）：
if ! docker compose -f "$DOCKER_COMPOSE_FILE" up -d 2> /tmp/up_err.log; then
  if grep -q "No such image" /tmp/up_err.log; then
    log_warn "  镜像不存在，自动构建一次..."
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d --build
  else
    log_error "  启动失败，且非镜像缺失问题："
    cat /tmp/up_err.log | sed 's/^/    /'
    log_error "  常见原因：网络 ruoyi-network 状态异常、端口冲突、配置错误"
    log_error "  排查建议：bash scripts/cleanup-orphan-network.sh 后重试"
    exit 1
  fi
fi
```

### 3.4 临时绕过方法（**在 §3.3 落地前**）

```bash
# 1. 手工清理孤儿网络
sudo bash scripts/cleanup-orphan-network.sh

# 2. 手工创建带标签的网络
sudo docker network create \
  --label com.docker.compose.project=ruoyi \
  --label com.docker.compose.network=ruoyi-network \
  ruoyi-network

# 3. 重跑
./start-dev.sh --docker
```

---

## 4. 当前代码现状（As-Is）

> 此节为"自检快照"，确保文档与现实一致（2026-07-12 20:33 自检）

| 维度 | 当前代码 | 与本文档 §3.2 一致？ |
|------|----------|----------------------|
| `docker-compose.my.yml` 网络段 | `external: true` | ✅ |
| `docker-compose.pg.yml` 网络段 | `external: true` | ✅ |
| `stop-dev.sh` 删网络段 | 已删除 | ✅ |
| `scripts/cleanup-orphan-network.sh` | 存在、可执行 | ✅ |
| `start-dev.sh` `ensure_clean_ruoyi_network` | **未实现** | ❌（§3.3.1 TODO） |
| `start-dev.sh` local mode 创建网络时带标签 | **未实现** | ❌（§3.3.2 TODO） |
| `start-dev.sh` docker mode fallback 区分错误类型 | **未实现** | ❌（§3.3.3 TODO） |

---

## 5. 影响面（Impact）

### 5.1 正面影响（已落地部分）

- ✅ **`stop-dev.sh` 不再误删生产网络**：之前会强制 `docker network rm ruoyi-network`，**生产 compose 网络会被误删**——commit 3 已修
- ✅ **`docker-compose.*.yml` 与生产解耦**：本地 compose 不再尝试创建/删除网络
- ✅ **运维工具已就位**：`cleanup-orphan-network.sh` 可在服务器手动清理孤儿网络

### 5.2 潜在影响（未落地部分）

- 🟠 **首次在干净服务器上跑 `./start-dev.sh --docker` 仍会失败**：因为脚本会先裸 `docker network create` 留个无标签网络，然后 compose up 报 "incorrect label"
  - **临时绕过**：§3.4 三步
  - **最终解决**：§6 改进 1（`ensure_clean`）+ 改进 2（带标签创建）

- 🟡 **`docker compose up --build` fallback 仍会触发**：错误诊断能力差，仍可能浪费 28s 构建
  - **最终解决**：§6 改进 3（按错误类型 fallback）

### 5.3 回归风险

| 场景 | 风险等级 | 备注 |
|---|---|---|
| 已正确部署过环境（生产 compose 网络在用） | 🟢 仍正常 | `external: true` 让本地不碰网络 |
| 全新环境首次跑 | 🟠 失败 | 需先 §3.4 临时绕过，或 §6 改进 1-2 落地 |
| 历史孤儿网络在 | 🟡 fallback 仍误触发 | 需先 §6 改进 3 |

---

## 6. 待补改进（Follow-ups）

### 改进 1：`start-dev.sh` 新增 `ensure_clean_ruoyi_network` — 🔲 **TODO**

代码见 §3.3.1。在 `start-dev.sh` 的 docker mode / local mode 入口都调用一次。

### 改进 2：local mode 创建网络时带 compose 标签 — 🔲 **TODO**

代码见 §3.3.2。**这是 docker mode fallback 不再被网络问题触发的前提**。

### 改进 3：fallback 按错误类型区分 — 🔲 **TODO**

代码见 §3.3.3。把"网络冲突" / "端口冲突" / "配置错误"从自动 build 路径里分离出来，让用户看到**真正的错误信息**。

### 改进 4：考虑 `external: false` 撤回到 `driver: bridge` — 🤔 **决策待定**

| 选项 | 优点 | 缺点 |
|---|---|---|
| 保留 `external: true`（当前） | 与生产解耦，脚本/运维可控 | 启动脚本必须配合创建网络 |
| 改回 `driver: bridge` | compose 自己创建，标签正确 | **生产 compose 仍可能与本地抢网络**——这正是 commit 3 想规避的 |

**结论**：保留 `external: true`，但配合改进 1-2 让脚本侧能正确处理创建流程。

### 改进 5：CI / pre-commit 检查 — 🔲 **TODO**

在 CI 中跑：

```bash
bash scripts/cleanup-orphan-network.sh
# 期望输出 [OK]，否则 PR 不能合并
```

---

## 7. 经验教训（Lessons Learned）

### 7.1 `docker network create` 不带标签 → 必为孤儿

`com.docker.compose.network=<name>` 是 compose 识别"我创建的"的**唯一标准**。裸 `docker network create <name>` 永远不会被任何 compose 文件接管。

**教训**：所有"被 compose 使用"的网络**必须由 compose 创建**——要么 compose 配置文件里 `driver: bridge` 让它自动建，要么手动创建时**带 `--label`**。

### 7.2 "网络冲突"的根因常常是脚本本身

排查"网络冲突"时，先看**你的启动脚本**——是不是它在 docker compose 跑前**偷偷建了网络**。95% 的"网络冲突"其实都是脚本自建的孤儿网络在背锅。

### 7.3 fallback 设计原则：宁可"硬失败 + 给诊断"，不要"宽容失败 + 自动 build"

`start-dev.sh` 的 fallback 把所有失败归为"镜像不存在"自动 build，是个**反模式**：

- 网络 / 端口 / 配置错误**都被掩盖**
- 用户**看不到真正的错误信息**
- 浪费时间（28s+ 白构建）

**原则**：fallback 应是**"上次成功的状态可恢复"**（如镜像 cache 丢失），不是"什么错都兜底"。

### 7.4 配置变更的"半正确"比"错误"更危险

commit 3 的 `external: true` 是**对的方向但只对了一半**——它解决了"生产网络被本地误删"，但**没解决"启动失败"**。这种"看起来工作但首次部署必失败"的配置，比明摆着错误的配置**更难发现**。

**教训**：涉及"启动链路"的改动，要做"干净环境首次部署"的端到端验证——不是只在本机跑通就算完。

### 7.5 "外部资源" vs "内部资源"的语义

`external: true` 表达的是"资源由**外部**管理"——谁负责？**没说**。当前设计是"由运维/脚本负责"，但**脚本本身没做好接管**，于是语义正确、实现残缺。

**教训**：声明"外部管理"时，必须**配套提供"外部管理者"实现**——否则就是甩锅。

---

## 8. 附录（Appendix）

### 8.1 复用脚本清单

```bash
# 1. 清理孤儿网络
bash scripts/cleanup-orphan-network.sh

# 2. 手工建网络（带标签）
docker network create \
  --label com.docker.compose.project=ruoyi \
  --label com.docker.compose.network=ruoyi-network \
  ruoyi-network

# 3. 验证网络状态
docker network inspect ruoyi-network --format '{{.Labels}}'
# 期望：map[com.docker.compose.network:ruoyi-network com.docker.compose.project:ruoyi]
```

### 8.2 历史 commit 与本次关联

| Commit | 改动 | 与本文关系 |
|--------|------|------------|
| `3d30967 chore(network): ruoyi-network 改 external...` | compose 网络段 `external: true` + stop-dev.sh 不删网络 + cleanup 脚本新增 | ✅ 已落地部分 |
| 🔲 TODO | `start-dev.sh` ensure_clean + local mode 带标签创建 + fallback 区分错误 | 📋 §6 改进 1-3 |

### 8.3 此次改动涉及的 `git diff` 概要

| 文件 | 改动类型 | 状态 |
|------|----------|------|
| `docker-compose.my.yml` | 网络段 `external: true` | ✅ commit 3 |
| `docker-compose.pg.yml` | 同上 | ✅ commit 3 |
| `start-dev.sh` | 待补 `ensure_clean_ruoyi_network` 等 | 🔲 TODO |
| `stop-dev.sh` | 不再尝试删除 `ruoyi-network` | ✅ commit 3 |
| `scripts/cleanup-orphan-network.sh` | 新增（手动诊断工具） | ✅ commit 3 |
| `docs/04-开发/DEBUG/orphan-ruoyi-network-2026-07-12.md` | 本文档 | ✅ 本 commit |

---

**最后更新**：2026-07-12 20:33（**部分修复**——`external: true` + cleanup 工具 + stop-dev.sh 不删网络已落地；`start-dev.sh` 的 ensure_clean / 带标签创建 / fallback 错误区分**仍 TODO**；文档已与代码现状对齐）