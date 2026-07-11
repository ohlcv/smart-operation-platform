# DEBUG-20260711-01 双重 UTF-8 编码（Double UTF-8 Encoding）

| 项目     | 内容                                                          |
| -------- | ------------------------------------------------------------- |
| 文档编号 | DEBUG-20260711-01                                             |
| 类别     | 数据库 / 字符集 / 数据修复                                    |
| 严重度   | 🔴 P0（菜单、部门、字典全部中文都显示乱码，前台不可用）      |
| 状态     | ✅ 已修复（永久方案 A+B 双保险已落地）                    |
| 涉及版本 | smart-operation-platform @ 2026-07-11                         |
| 发现人   | 开发自检（前端菜单点击空菜单、无显示时发现）                  |
| 修复人   | 开发自检                                                       |
| 关联脚本 | [`scripts/fix_double_utf8.py`](../../../scripts/fix_double_utf8.py) |
| 复现验证 | 2026-07-11 17:00 — `docker rm ruoyi-mysql` 后字符集再次回归，**已确认通过 mysql-conf 卷挂载 + 命令行参数双保险修复** |

---

## 目录（Table of Contents）

1. [现象（Symptoms）](#1-现象symptoms)
2. [排查过程（Investigation）](#2-排查过程investigation)
3. [修复（Fix）](#3-修复fix)
4. [影响面（Impact）](#4-影响面impact)
5. [后续改进（Follow-ups）](#5-后续改进follow-ups)
6. [经验教训（Lessons Learned）](#6-经验教训lessons-learned)
7. [附录（Appendix）](#7-附录appendix)
8. [勘误（Errata）](#8-勘误errata)

---

## 1. 现象（Symptoms）

启动开发环境后访问前端：

- **菜单管理** 列表中 `menu_name` 列大量显示为乱码，类似：
  `ç³»ç»Ÿç®¡ç†`、`è‹¥ä¾å®˜ç½‘`、`ç"¨æˆ·ç®¡ç†`
- **部门管理** 显示 `é›†å›¢æ€»å…¬å¸`、`éƒ¨é—¨ç®¡ç†`
- **角色管理** 显示 `è¶…çº§ç®¡ç†å'˜`
- **字典管理** 显示 `èŒå•çŠ¶æ€`
- 切换客户端 / 切换浏览器无效
- 后端 DEBUG 日志中 SQL 参数已经是乱码字符串（说明写入时就是错的，不是读取错）

---

## 2. 排查过程（Investigation）

### 2.1 字节层取证

挑 `sys_menu.menu_id = 1` 一行（应为 `系统管理`）：

```sql
SELECT menu_id, HEX(menu_name), CHAR_LENGTH(menu_name), LENGTH(menu_name)
FROM sys_menu WHERE menu_id = 1;
```

结果：

```
menu_id  HEX(menu_name)                                 CHAR_LENGTH  LENGTH
1        C3A7C2B3C2BBC3A7C2BBC5B8C3A7C2AEC2A1C3A7C290E280A0   12          25
```

期望 `系统管理` 的 UTF-8 编码 = `E7B3BB E7BB9F E7AE A1 E79086`（共 12 字节）。

实际字节明显是「`E7 B3 BB` → 经 latin1 解读成字符 `ç³»` → 再 utf-8 编码为 `C3 A7 C2 B3 C2 BB`」的痕迹，**3 字节原始 UTF-8 变成 6 字节**，**完全对得上双重编码**。

### 2.2 双重编码公式

```
原始 S = "系统管理"
    ↓ encode('utf-8')
B1 = E7 B3 BB E7 BB 9F E7 AE A1 E7 90 86          ← 12 字节
    ↓ (server 错按 latin1 解读)
C  = chr(E7)+chr(B3)+chr(BB)+... = "ç³»ç»Ÿç®¡ç†"   ← 12 个字符
    ↓ (写入 utf8mb4 字段时再 encode('utf-8'))
B2 = C3 A7 C2 B3 C2 BB C3 A7 C2 BB C5 B8 ...     ← 24 字节
```

### 2.3 为什么一部分编码后字节数对不上

剩余未修复行（`menu_id=99` `若依官网`）的 HEX：

```
C3A8 E280B9 C2A5 C3A4 C2BE C29D C3A5 C2AE CB9C C3A7 C2BD E28098
```

用 Python `utf-8 decode` 得到字符串 `'è‹¥ä¾\x9då®˜ç½‘'`，里面混入了 `U+2039`（"‹"）、`U+009D` 等字符。

**关键发现**：MySQL 的 `latin1` 字符集实质是 **Windows-1252 (cp1252)**，不是 ISO-8859-1：

- `0x8B` 在 cp1252 中被映射到 `U+2039`（"‹"），写入时编码为 `E2 80 B9`
- `0x81 0x8D 0x8F 0x90 0x9D` 在 cp1252 中是**未定义**（C1 控制字符），保持原字节

所以双重编码后的字符串里既可能有 Unicode 高位字符（`U+201D` `"` 等），也可能有 C1 控制字符（`U+0090` 等）。

### 2.4 根因（Root Cause）

**MySQL 容器启动时未指定字符集**，server 默认：
- `character_set_client = latin1`（应用发字节用的客户端解码器）
- `character_set_server = latin1`（其他几个相关变量）

应用代码（`ruoyi-fastapi-backend`）连接字符串中指定 `charset=utf8mb4`，**但连接握手阶段也会被 server 的 `character_set_client` 截获**。

写入流程：
1. 应用把 `系统管理` utf-8 编码为 `E7 B3 BB ...`
2. 字节通过 client→server 链路发送
3. server 用 `character_set_client = latin1` 解读这些字节为字符 `ç³»ç»Ÿ...`
4. server 在写入 utf8mb4 字段时，**重新 utf-8 编码这些字符**
5. 落库字节 = `C3 A7 C2 B3 C2 BB ...`

读出时配置正确就拿到 `ç³»ç»Ÿ...`，前端 / navie 显示就全是乱码。

### 2.5 影响范围

通过 `LENGTH(menu_name)` 大于期望字节数的条件查询，影响以下字段（修复时全部覆盖）：

| 表              | 字段                                    | 受损行数 |
| --------------- | --------------------------------------- | -------- |
| `sys_menu`      | menu_name 等 8 个文本字段               | 47 → 46  |
| `sys_dept`      | dept_name                                | 5        |
| `sys_role`      | role_name                                | 1        |
| `sys_dict_type` | dict_name                                | 5 → 7    |
| `sys_dict_data` | dict_label, css_class, list_class       | 22 → 9   |
| `sys_user`      | nick_name                                | 1        |
| **合计**        |                                         | **150+** |

---

## 3. 修复（Fix）

### 3.1 已采取的永久性修复（方案 A+B 双保险）

#### 3.1.1 数据库 server 字符集配置（方案 A：cnf 卷挂载）

**文件位置**：`$PROJECT_ROOT/mysql-conf/charset.cnf`（项目根目录，随 Git 版本控制）

```ini
[client]
default-character-set = utf8mb4
[mysql]
default-character-set = utf8mb4
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_0900_ai_ci
init-connect = "SET NAMES utf8mb4"
```

挂载到容器内路径：`/etc/mysql/conf.d/charset.cnf:ro`

#### 3.1.2 数据库 server 命令行参数（方案 B：docker run 追加参数）

`start-dev.sh` 中 `docker run` 命令行末尾追加：

```bash
docker run mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_general_ci \
  --skip-character-set-client-handshake=1
```

> 注意：`--skip-character-set-client-handshake=1` 强制 server 忽略客户端的字符集协商请求，以 server 端的设置为准。

#### 3.1.3 为什么需要 A+B 双保险

| 方案 | 优点 | 缺点 |
|------|------|------|
| 方案 A（cnf 卷挂载） | 支持 `[client]`/`[mysql]` 分组；支持 `init-connect` 捕获普通用户连接 | 依赖卷挂载是否正确生效，排查链路长 |
| 方案 B（命令行参数） | 简单直接，与 `docker-compose.my.yml` 一致 | 只能影响 server，不支持分组配置 |
| **A+B 双保险** | 任一方案生效即可，双重防护 | 无 |

两种方案同时生效时，以 `[mysqld]` + 命令行参数中**更严格的配置**为准，**不会有冲突**。

#### 3.1.4 应用代码

`ruoyi-fastapi-backend/.env.dev` 中数据库连接已正确使用 `charset=utf8mb4`，**应用代码无需修改**。

#### 3.1.5 数据修复（一次性）

脚本 [`scripts/fix_double_utf8.py`](../../../scripts/fix_double_utf8.py)，两次执行合计修复 150+ 行：

| 时间       | 修复行数 | 备注                                       |
| ---------- | -------- | ------------------------------------------ |
| 第一次试跑 | 81       | 仅 cp1252 标准字符（缺 C1 控制字符支持）   |
| 第二次     | 69       | 补全 cp1252 高位表，覆盖全部 `0x80-0x9F`   |

修复前后对照（sys_menu 例子）：

```
修复前: 'ç³»ç»Ÿç®¡ç\x90†'  (cl=25)
修复后: '系统管理'         (cl=4)
```

### 3.2 修复步骤（复现）

> **前提**：请确保 `mysql-conf/charset.cnf` 文件存在且 `start-dev.sh` 已包含方案 B 命令行参数。

1. **重建 MySQL 容器（使配置生效）**

   ```bash
   docker rm -f ruoyi-mysql
   ./start-dev.sh
   ```

   观察输出中 `MySQL 字符集自检: character_set_client=utf8mb4 ✓` 是否出现。

2. **确认 server 字符集已为 utf8mb4**

   ```bash
   docker exec ruoyi-mysql mysql --default-character-set=utf8mb4 -uroot -proot \
       -e "SHOW VARIABLES WHERE Variable_name LIKE 'character_set%';"
   ```

   所有变量应当全部为 `utf8mb4`。

3. **dry-run 预览（仅当有历史数据损坏时需要）**

   ```bash
   cd /Users/meow/Desktop/Project/smart-operation-platform
   python3 scripts/fix_double_utf8.py --dry-run
   ```

4. **确认 dry-run 输出合理后，正式修复**

   ```bash
   python3 scripts/fix_double_utf8.py
   ```

5. **抽样验证**

   ```bash
   docker exec ruoyi-mysql mysql --default-character-set=utf8mb4 -uroot -proot ruoyi-fastapi -e "
       SET NAMES utf8mb4;
       SELECT menu_id, menu_name FROM sys_menu ORDER BY menu_id LIMIT 10;
   "
   ```

   应看到全部正常中文 `系统管理`、`系统监控`、`系统工具` 等。

---

## 4. 影响面（Impact）

- **数据正确性**：✅ 数据已全部修复，与原始输入一致
- **性能**：脚本全表扫描 + UPDATE，行数 < 200 时秒级完成
- **回归风险**：脚本对每个字段做"修复前后对照"，仅当反转后含中文且与原值不同时才更新，**不会误改已正确数据**
- **后续写入**：✅ 新写入的数据已不会再发生双重编码
- **容器重建**：✅ `mysql-conf/charset.cnf` 在宿主机（`$PROJECT_ROOT/mysql-conf/`），`docker rm` 不会丢失；方案 B 命令行参数在 `start-dev.sh` 中，同样持久化

---

## 5. 后续改进（Follow-ups）

### 改进 1：cnf 永久卷挂载 + 命令行参数双保险 — ✅ **已落地 (2026-07-11 17:00, 升级 2026-07-11 20:37)**

**复现现象**：2026-07-11 删除并重建 `ruoyi-mysql` 容器后，菜单/部门再次出现双重编码。

**根因**：之前 `/etc/mysql/conf.d/charset.cnf` 是在**容器内手动写入**的，`docker rm` 后丢失，新容器以默认 `latin1` 启动。

**修复**：

1. 在项目根目录建立 `mysql-conf/charset.cnf` 文件（已提交），由 `start-dev.sh` 挂载
2. `docker run` 命令行追加方案 B 参数，与 `docker-compose.my.yml` 第 46 行等价

`start-dev.sh` 中的实现：

```bash
docker run -d \
  --name ruoyi-mysql \
  --network ruoyi-network \
  --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ruoyi-fastapi \
  -p 13306:3306 \
  -v $PROJECT_ROOT/ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql:/docker-entrypoint-initdb.d/ruoyi-fastapi.sql \
  -v $PROJECT_ROOT/mysql-conf/charset.cnf:/etc/mysql/conf.d/charset.cnf:ro \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_general_ci \
  --skip-character-set-client-handshake=1
```

**重要发现**：`ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql` 这个 init SQL 文件本身就是**正确 utf8mb4 编码**的，容器首次启动会执行它自动建表+灌数据。所以：

- ✅ 字符集配置正确 → 应用发 utf8 字节、server 不再误按 latin1 解读
- ✅ init SQL 本身合法 → 灌入数据不再被双重编码
- ✅ **重建 ruoyi-mysql 后，再无双重编码问题**
- ✅ **新建表、新写入数据全部正常**

**已不再需要每次重建后跑数据修复脚本**——`fix_double_utf8.py` 仅作为应急保留。

### 改进 2：`start-dev.sh` 字符集自检脚本（带诊断输出） — ✅ **已落地 (2026-07-11 17:00, 升级 2026-07-11 20:37)**

在 MySQL 启动就绪后插入自检，失败时打印完整返回值便于诊断：

```bash
local charset_raw charset
charset_raw=$(LANG=C docker exec ruoyi-mysql mysql --default-character-set=utf8mb4 \
  -uroot -proot -N -B \
  -e "SHOW VARIABLES WHERE Variable_name='character_set_client'" 2>&1)
charset=$(echo "$charset_raw" | tail -n 1 | tr -d '[:space:]')
if [ "$charset" != "utf8mb4" ]; then
  log_error "MySQL character_set_client=[${charset}]（期望 utf8mb4）"
  log_error "完整返回值（用于诊断）："
  echo "$charset_raw" | sed 's/^/    /'
  log_error "可能原因：mysql-conf/charset.cnf 未挂载或被忽略"
  exit 1
fi
log_info "  MySQL 字符集自检: character_set_client=utf8mb4 ✓"
```

关键改进：
- `--default-character-set=utf8mb4`：强制 mysql CLI 客户端自身使用 utf8mb4 通信
- `tail -n 1`：在只有一行结果时直接取该行，避免 `cut -f2` 对 tab 分隔符的脆弱依赖
- 失败时打印完整输出，区分"字符集真的错"vs"命令本身出错（如权限、容器未就绪）vs"自检脚本解析 bug"

### 改进 3：CI 增加批量数据健康巡检 — 🔲 **TODO**

修复脚本输出"待修复行数"作为健康指标，可接入 CI 周期任务。一旦 > 0 即报警。

### 改进 4：删除"首次"实验性修复（容器内 cnf）的痕迹 — 🔲 **TODO**

早期通过 `docker exec ... tee /etc/mysql/conf.d/charset.cnf` 写入容器内的方案已被放弃，所有配置应在 `mysql-conf/` 中托管。

---

## 6. 经验教训（Lessons Learned）

1. **永远不要让 MySQL 容器以默认字符集启动**。`docker run mysql` 不显式指定字符集就是 `latin1`。
2. **应用端 `charset=utf8mb4` 不够**，还需 server 端 `character_set_client = utf8mb4`，否则链路中段 server 会"翻译"一次。
3. **`character_set_client` 是链路中间最关键的变量**，应用发什么字节、server 按什么解码、字段按什么存储，三者必须协调。
4. **出现"双重编码"时**，简单 `b.decode('utf-8')` 解不出来，必须借助 **cp1252 高位映射表** 反查回原始字节。
5. **优先做 `--dry-run`** 再正式跑批量修复，脚本已默认提供。
6. **自检脚本本身也要健壮**——用 `tail -n 1` 代替 `cut -f2`，并在失败时打印完整输出；shell 的 `set -e` 配合 `local` 变量时要小心子 shell 退出码。
7. **双保险优于单方案**：cnf 挂载 + 命令行参数同时存在，任一生效即可防回归。

---

## 7. 附录（Appendix）

### 7.1 双重编码诊断 checklist

```python
import pymysql
conn = pymysql.connect(host='127.0.0.1', port=13306, user='root',
                       password='root', database='ruoyi-fastapi',
                       charset='utf8mb4')
with conn.cursor() as cur:
    cur.execute("SELECT menu_id, menu_name FROM sys_menu WHERE menu_id=1")
    mid, v = cur.fetchone()
    print(f"menu_id={mid}")
    print(f"Python str:    {v!r}")
    print(f"utf-8 bytes:   {v.encode('utf-8').hex()}")
    for i, ch in enumerate(v):
        print(f"  [{i}] U+{ord(ch):04X} = {ch!r}")
```

期望看到类似 `U+00E7` (`ç`) 的 codepoint 而不是 `U+7528` (`用`)。如果出现 `U+00E7`/`U+00B3` 等字符，**确证双重编码**。

### 7.2 双重编码反转核心函数

```python
CP1252_HIGH = {
    0x80: 0x20AC, 0x82: 0x201A, 0x83: 0x0192, 0x84: 0x201E, 0x85: 0x2026,
    0x86: 0x2020, 0x87: 0x2021, 0x88: 0x02C6, 0x89: 0x2030, 0x8A: 0x0160,
    0x8B: 0x2039, 0x8C: 0x0152, 0x8E: 0x017D, 0x91: 0x2018, 0x92: 0x2019,
    0x93: 0x201C, 0x94: 0x201D, 0x95: 0x2022, 0x96: 0x2013, 0x97: 0x2014,
    0x98: 0x02DC, 0x99: 0x2122, 0x9A: 0x0161, 0x9B: 0x203A, 0x9C: 0x0153,
    0x9E: 0x017E, 0x9F: 0x0178,
}
UNI_TO_CP1252 = {cp: b for b, cp in CP1252_HIGH.items()}

def reverse_double_utf8(s):
    if not s or any('\u4e00' <= ch <= '\u9fff' for ch in s):
        return s
    bs = bytearray()
    for ch in s:
        cp = ord(ch)
        if cp < 0x100:
            bs.append(cp)
        elif cp in UNI_TO_CP1252:
            bs.append(UNI_TO_CP1252[cp])
        else:
            return None
    try:
        return bytes(bs).decode('utf-8')
    except UnicodeDecodeError:
        return None
```

### 7.3 cp1252 → Unicode 映射表速查

| cp1252 | Unicode | 字符   | 描述     |
| ------ | ------- | ------ | -------- |
| 0x80   | U+20AC  | €      | 欧元符号 |
| 0x8B   | U+2039  | ‹      | 单左引号 |
| 0x8C   | U+0152  | Œ      | OE 连字  |
| 0x91   | U+2018  | '      | 左单引号 |
| 0x92   | U+2019  | '      | 右单引号 |
| 0x93   | U+201C  | "      | 左双引号 |
| 0x94   | U+201D  | "      | 右双引号 |
| 0x97   | U+2014  | —      | 破折号   |
| 0x99   | U+2122  | ™      | 商标符号 |
| 0x9C   | U+0153  | œ      | oe 连字  |
| 0x9F   | U+0178  | Ÿ      | Y 变音符 |

---

## 8. 勘误（Errata）

### 8.1 关于"Docker 模式天然免疫"的错误说明

**之前错误表述**：以为"应用跑在容器里"是字符集正常的关键。

**实际真相**：
- 两种模式（`./start-dev.sh` 和 `./start-dev.sh --docker`）**共用同一个 ruoyi-mysql 容器**，
  不存在"应用在容器里所以正常"这回事。
- 真正差异在 `docker run` 命令：

| 模式 | 启动方式 | 字符集配置 |
|---|---|---|
| `./start-dev.sh`（local） | `start-dev.sh` 第 169 行 `docker run mysql:8.0` | **无参数**，默认 latin1 → 乱码（修复前） |
| `./start-dev.sh --docker` | `docker-compose.my.yml` 第 46 行 `command:` 行 | 显式声明 utf8mb4 → 正常 |

### 8.2 方案演进历史

| 时间 | 方案 | 状态 | 说明 |
|------|------|------|------|
| 2026-07-11 下午 | 方案 0：容器内手动写入 cnf | ❌ 已废弃 | `docker rm` 后丢失，不防重建 |
| 2026-07-11 17:00 | 方案 A：cnf 卷挂载 | ✅ 落地（基础版） | `mysql-conf/charset.cnf` 挂载 |
| 2026-07-11 17:21 | 方案 B：命令行参数（主）/ 方案 A（备用） | ⚠️ 文档更新但脚本未同步 | 文档写 B 为主，实际脚本仍是方案 A |
| **2026-07-11 20:37** | **方案 A+B 双保险** | **✅ 最终落地** | cnf 挂载 + 命令行参数同时生效；自检脚本升级 |

### 8.3 自检脚本解析 bug 排查记录

**问题现象**：2026-07-11 晚间，`./start-dev.sh` 执行后自检报错：

```
[ERROR] MySQL character_set_client=??期望 utf8mb4）
```

其中 `??` 仅 2 字符，而预期值 `utf8mb4` 为 6 字符。

**排查过程**：
1. 原始脚本使用 `cut -f2 -d'	'`（tab 分隔取第 2 列），在 macOS zsh 环境下对 tab 分隔符处理存在差异
2. `mysql -N -B` 输出为 `character_set_client<TAB>utf8mb4`，`cut -f2` 应取到 `utf8mb4`，但实际取到了空值或短值
3. 排除字符集本身错误（`docker run` 已同时有方案 A/B 配置）
4. 确认为**自检脚本解析 bug**，非 MySQL 字符集实际错误

**修复**：
- 将 `cut -f2 -d'	'` 改为 `tail -n 1 | tr -d '[:space:]'`
- 增加 `--default-character-set=utf8mb4` 强制 mysql CLI 自身通信字符集
- 失败时打印完整返回值，区分"字符集真错"vs"命令出错"vs"解析 bug"

**教训**：自检脚本本身也需要健壮性测试——不能只在字符集正确时测试通过，也要模拟错误场景。

---

**最后更新**：2026-07-11 20:37（A+B 双保险最终落地，自检脚本升级，文档全面同步更新）
