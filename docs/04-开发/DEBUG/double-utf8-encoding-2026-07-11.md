# DEBUG-20260711-01 双重 UTF-8 编码（Double UTF-8 Encoding）

| 项目     | 内容                                                          |
| -------- | ------------------------------------------------------------- |
| 文档编号 | DEBUG-20260711-01                                             |
| 类别     | 数据库 / 字符集 / 数据修复                                    |
| 严重度   | 🔴 P0（菜单、部门、字典全部中文都显示乱码，前台不可用）      |
| 状态     | ✅ 已修复（永久方案已落地）                                |
| 涉及版本 | smart-operation-platform @ 2026-07-11                         |
| 发现人   | 开发自检（前端菜单点击空菜单、无显示时发现）                  |
| 修复人   | 开发自检                                                       |
| 关联脚本 | [`scripts/fix_double_utf8.py`](../../../scripts/fix_double_utf8.py) |
| 复现验证 | 2026-07-11 17:00 — `docker rm ruoyi-mysql` 后字符集再次回归，**已确认通过 mysql-conf 卷挂载修复** |

---

## 1. 现象（Symptoms）

启动开发环境后访问前端：

- **菜单管理** 列表中 `menu_name` 列大量显示为乱码，类似：
  `ç³»ç»Ÿç®¡ç†`、`è‹¥ä¾å®˜ç½‘`、`ç”¨æˆ·ç®¡ç†`
- **部门管理** 显示 `é›†å›¢æ€»å…¬å¸`、`éƒ¨é—¨ç®¡ç†`
- **角色管理** 显示 `è¶…çº§ç®¡ç†å‘˜`
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

### 3.1 已采取的永久性修复

#### 3.1.1 数据库 server 字符集（已永久写入）

`/etc/mysql/conf.d/charset.cnf`（容器内挂载，已存在）：

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

重启后验证：

```sql
SHOW VARIABLES WHERE Variable_name LIKE 'character_set%' OR Variable_name LIKE 'collation%';
```

所有变量应当全部为 `utf8mb4` / `utf8mb4_0900_ai_ci`。

#### 3.1.2 应用代码

`ruoyi-fastapi-backend/.env.dev` 中数据库连接已正确使用 `charset=utf8mb4`，**应用代码无需修改**。

但建议在 `start-dev.sh` 中加上字符集自检（见 §5 后续改进）。

#### 3.1.3 数据修复（一次性）

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

1. **确认 server 字符集已为 utf8mb4**

   ```bash
   docker exec ruoyi-mysql mysql -uroot -proot \
       -e "SHOW VARIABLES LIKE 'character_set%';"
   ```

2. **先 dry-run 预览**

   ```bash
   cd /Users/meow/Desktop/Project/smart-operation-platform
   python3 scripts/fix_double_utf8.py --dry-run
   ```

3. **确认 dry-run 输出合理后，正式修复**

   ```bash
   python3 scripts/fix_double_utf8.py
   ```

4. **抽样验证**

   ```bash
   docker exec ruoyi-mysql mysql -uroot -proot --default-character-set=utf8mb4 \
       ruoyi-fastapi -e "
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
- **容器重建**：⚠️ 如果 `docker rm ruoyi-mysql` 重建容器，3.1.1 的 cnf 文件随容器丢失，需重新挂载或加 volumes（见 §5 改进 1）

---

## 5. 后续改进（Follow-ups）

### 改进 1：`mysql-conf` 永久卷挂载（防容器重建丢配置）— ✅ **已落地 (2026-07-11 17:00)**

**复现现象**：2026-07-11 删除并重建 `ruoyi-mysql` 容器后，菜单/部门再次出现双重编码。

**根因**：之前 `/etc/mysql/conf.d/charset.cnf` 是在**容器内手动写入**的，`docker rm` 后丢失，新容器以默认 `latin1` 启动，旧字符集配置不再生效。

**修复**：在项目根目录建立 `mysql-conf/charset.cnf` 文件（已提交）：

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

`start-dev.sh` 在 `docker run ruoyi-mysql` 时挂载该文件：

```bash
docker run -d \
  --name ruoyi-mysql \
  ...
  -v $PROJECT_ROOT/mysql-conf/charset.cnf:/etc/mysql/conf.d/charset.cnf:ro \
  mysql:8.0
```

**重要发现**：`ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql` 这个 init SQL 文件本身就是**正确 utf8mb4 编码**的，容器首次启动会执行它自动建表+灌数据。所以：

- ✅ 字符集挂载正确 → 应用发 utf8 字节、server 不再误按 latin1 解读
- ✅ init SQL 本身合法 → 灌入数据不再被双重编码
- ✅ **重建 ruoyi-mysql 后，再无双重编码问题**
- ✅ **新建表、新写入数据全部正常**

**已不再需要每次重建后跑数据修复脚本**——`fix_double_utf8.py` 仅作为应急保留。

### 改进 2：`start-dev.sh` 增加启动后字符集自检 — ✅ **已落地**

在 MySQL 启动就绪后插入：

```bash
local charset
charset=$(docker exec ruoyi-mysql mysql -uroot -proot -N -B \
  -e "SHOW VARIABLES WHERE Variable_name='character_set_client'" 2>/dev/null | awk '{print $2}')
if [ "$charset" != "utf8mb4" ]; then
  log_error "MySQL character_set_client=$charset（期望 utf8mb4）"
  log_error "可能原因：mysql-conf/charset.cnf 未挂载或被忽略"
  exit 1
fi
log_info "  MySQL 字符集自检: character_set_client=utf8mb4 ✓"
```

启动若看到此自检行通过，说明 cnf 挂载生效；若缺失则会立即 fail-fast。

### 改进 3：CI 增加批量数据健康巡检（防止未来再发生）— 🔲 **TODO**

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
| 0x91   | U+2018  | ‘      | 左单引号 |
| 0x92   | U+2019  | ’      | 右单引号 |
| 0x93   | U+201C  | “      | 左双引号 |
| 0x94   | U+201D  | ”      | 右双引号 |
| 0x97   | U+2014  | —      | 破折号   |
| 0x99   | U+2122  | ™      | 商标符号 |
| 0x9C   | U+0153  | œ      | oe 连字  |
| 0x9F   | U+0178  | Ÿ      | Y 变音符 |

---

## 8. 勘误（2026-07-11 17:13）

### 8.1 关于"Docker 模式天然免疫"的错误说明

**之前错误表述**：以为"应用跑在容器里"是字符集正常的关键。

**实际真相**：
- 两种模式（`./start-dev.sh` 和 `./start-dev.sh --docker`）**共用同一个 ruoyi-mysql 容器**，
  不存在"应用在容器里所以正常"这回事。
- 真正差异在 `docker run` 命令：

  | 模式 | 启动方式 | 字符集配置 |
  |---|---|---|
  | `./start-dev.sh`（local） | `start-dev.sh` 第 169 行 `docker run mysql:8.0` | **无参数**，默认 latin1 → 乱码 |
  | `./start-dev.sh --docker` | `docker-compose.my.yml` 第 46 行 `command:` 行 | 显式声明 utf8mb4 → 正常 |

### 8.2 最终方案选择（B 为主，A 备用）

**主方案（B）**：直接在 `docker run` 末尾追加 `--character-set-server` 等参数，
等价格式复制 `docker-compose.my.yml` 第 46 行 `command:` 的内容：

```bash
docker run mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_general_ci \
  --skip-character-set-client-handshake=1
```

**备用方案（A）**：保留 `mysql-conf/charset.cnf` + 卷挂载不变。
当需要以下能力时切回 A：
- 设置 `[client]` / `[mysql]` CLI 专用区块
- 使用 `init-connect = "SET NAMES utf8mb4"` 捕获普通用户连接的字符集问题

cnf 方案优于命令行参数的原因：
- 支持 `[client]` / `[mysql]` / `[mysqld]` 分组，命令行参数只能影响 server
- 支持 `init-connect = "SET NAMES utf8mb4"` 这样的会话级指令
- 配置内容可版本控制且独立于容器/启动命令

---

**最后更新**：2026-07-11 17:21（B 方案上线，A 方案降级为备用，脚本 + 文档同步更新）
