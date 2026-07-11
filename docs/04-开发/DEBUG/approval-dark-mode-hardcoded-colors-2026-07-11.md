# 审批中心页（approval）暗色模式适配缺失：硬编码浅色在暗色背景下视觉突兀

**日期**：2026-07-11
**类型**：前端样式 ADR 违规（暗色主题适配）/ 业务页样式遗留
**影响**：用户在暗色模式下打开审批中心，顶部搜索区、操作摘要区、历史记录区、签名图等区块底色与全站暗色主题脱节，呈现「白色卡片漂浮在暗色页面」的视觉割裂
**根因**：业务页（`approval / contract / customer`）的 `<style scoped>` 里大量写死浅色硬编码（`#fafbfc / #f5f7fa / #909399 / #606266 / #e4e7ed / #ecf5ff / #409eff / #e6a23c / #a8abb2 / #c0c4cc`），未使用 Element Plus 的 CSS 变量，导致 `html.dark` 切换时不受影响

---

## 1. 现象

用户在「审批中心 → 待我审批」页切到暗色模式后：

| 区块 | 现象 | 根级 class |
|---|---|---|
| 顶部筛选区（合同编号 / 合同名称 / 关键字） | 容器底色 `#fafbfc`（浅灰白），明显比卡片底色亮一截；3 个 el-input 输入框 | `.search-form` |
| 操作摘要块（通过/驳回意见显示区） | 底色 `#f5f7fa`，文字用默认色，与暗色不协调 | `.action-summary` |
| 历史记录头部（审批流提示） | 同上，底色硬编码浅灰 | `.history-header` |
| 步骤标签（Step 1 / Step 2...） | `#ecf5ff` 浅蓝底 + `#409eff` 蓝字，暗色下浅蓝底突兀 | `.step-tag` |
| 次要文字（时间、角色名） | `#909399` / `#606266`，暗色下基本不可读 | `.time-text` / `.role` / `.history-item-comment` |
| 审批意见文字 | `#606266` 暗色下偏暗 | `.history-item-comment` |
| 签名图边框 + 底色 | `#e4e7ed` 边框 + `#fff` 底色 | `.sig-img` |

截图：用户反馈时附图（`assets/bdee226a-.../42a7fa32-...png`）可看到 3 个 el-input 输入框在暗色卡片背景上明显偏白。

---

## 2. 修复前后对比

### 2.1 approval/index.vue

| 位置 | 修复前 | 修复后 |
|---|---|---|
| `.search-form` background | `#fafbfc` | `var(--el-fill-color-blank)` + `1px solid var(--el-border-color-lighter)` |
| `.time-text` color | `#909399` | `var(--el-text-color-secondary)` |
| `.action-summary` background | `#f5f7fa` | `var(--el-fill-color-light)` + 文字 `var(--el-text-color-regular)` |
| `.history-header` background | `#f5f7fa` | `var(--el-fill-color-light)` + 文字 `var(--el-text-color-regular)` |
| `.step-tag` background / color | `#ecf5ff` / `#409eff` | `var(--el-color-primary-light-9)` / `var(--el-color-primary)` |
| `.approver` color | （无） | `var(--el-text-color-primary)` |
| `.role` color | `#909399` | `var(--el-text-color-secondary)` |
| `.history-item-comment` color | `#606266` | `var(--el-text-color-regular)` |
| `.sig-img` border / background | `#e4e7ed` / `#fff` | `var(--el-border-color)` / `var(--el-fill-color-blank)` |

### 2.2 contract/index.vue

| 位置 | 修复前 | 修复后 |
|---|---|---|
| `.cur-role` color | `#e6a23c` | `var(--el-color-warning)` |
| `.upload-tip` color | `#a8abb2` | `var(--el-text-color-placeholder)` |

### 2.3 customer/index.vue

| 位置 | 修复前 | 修复后 |
|---|---|---|
| `.muted` color | `#c0c4cc` | `var(--el-text-color-placeholder)` |

### 2.4 故意保留的硬编码

`approval/index.vue` 中 `#f56c6c` 出现在 `.tab-badge`（小红点）/ `.amount-text`（金额高亮）/ `.history-item-reject`（驳回原因）三处 —— **业务语义色（警告/金额/驳回）**，浅色与暗色模式下均保持红色对用户识别有利，不跟随主题切换。

---

## 3. 根因分析

### 3.1 暗色主题机制（已存在，运作正常）

```js
// src/store/modules/settings.js:5-6
const isDark = useDark()  // @vueuse/core 自动给 html 加 class="dark"
const toggleDark = useToggle(isDark)

// src/main.js:7
import 'element-plus/theme-chalk/dark/css-vars.css'
// EP 监听 html.dark → 自动切换所有 --el-bg-color / --el-text-color-* / --el-border-color-* 等变量
```

整个项目的暗色机制是**健全的**：`useDark()` 加 class，EP 的 `dark/css-vars.css` 切换变量。

### 3.2 业务页违反机制

业务页（approval / contract / customer）开发时**直接写死了 Element Plus 旧版浅色调色板色值**，没有用 `var(--el-*)` 形式引用 CSS 变量。结果：

- 浅色模式下视觉无异常（硬编码值恰是浅色）
- 暗色模式下 EP 切了变量但本页用的是硬编码 → 视觉割裂

> 这与 `role-sort-conflict-2026-07-11.md` 的根因同源：**RuoYi 原生默认值与本项目语义冲突，但脚本作者没改默认**。本次是 EP 原生浅色调色板与本项目暗色主题冲突，业务页作者没换变量。

### 3.3 为什么早没暴露

- `dashboard` 等参考页（src/views/dashboard/index.vue）严格使用 `var(--el-*)`，暗色适配正常
- `approval / contract / customer` 是新开发的业务页（台账 §三编号 2.1 / 2.2 / 2.4），台账里**没有「暗色适配验收」这条验收项**
- 台账 §四验收标准中关于「样式」只要求"按钮/字段对齐、参考 dashboard 视觉"，没有具体覆盖暗色

---

## 4. 修复执行

```bash
# 全部 3 个文件，11 处替换，详情见 §2 表格
# 实际改动（approval = 9 处, contract = 2 处, customer = 1 处 + 后续扫描发现 6 个占位页共 12 处未修）
```

修复完成后，3 个 active 业务页在 `var(--el-*)` 形式下，`html.dark` 切换时全部跟随：

```css
/* 浅色模式（html 无 .dark）：
   --el-fill-color-blank     = #ffffff
   --el-fill-color-light     = #f5f7fa
   --el-text-color-secondary = #909399
   --el-color-warning        = #e6a23c
   --el-text-color-placeholder = #a8abb2
   → 视觉与原硬编码值一致，无回归 */

/* 暗色模式（html.dark）：
   --el-fill-color-blank     = #1d1e1f   （EP 自动切）
   --el-fill-color-light     = #262727
   --el-text-color-secondary = #a3a6ad
   --el-color-warning        = #cf9236
   --el-text-color-placeholder = #8d9095
   → 所有区块跟随主题切换，无白色漂浮 */
```

---

## 5. 验收

### 5.1 视觉验收（人工）

```bash
# 在 ruoyi-fastapi-frontend 启动 dev server
cd ruoyi-fastapi-frontend && npm run dev

# 浏览器访问 /biz/approval
# 1. 浅色模式下：搜索区/操作摘要/历史区视觉与修复前一致（颜色微调不影响布局）
# 2. 点击右上角「月亮」图标切换暗色
# 3. 验证：
#    - .search-form 容器底色变为深色，3 个输入框不再悬浮
#    - .step-tag 跟随主色（如你配的紫色），背景变深
#    - .time-text / .role / .history-item-comment 文字清晰可读
#    - .sig-img 边框为深色，不与背景融为一体
```

### 5.2 残留扫描

```bash
# 扫描 active 业务页是否还有写死浅色硬编码
rg -n '#[0-9a-fA-F]{3,6}' ruoyi-fastapi-frontend/src/views/biz/approval/index.vue \
  ruoyi-fastapi-frontend/src/views/biz/contract/index.vue \
  ruoyi-fastapi-frontend/src/views/biz/customer/index.vue | grep -vE 'f56c6c|303133'

# 期望输出：0 行（f56c6c 是警告色保留，303133 不在这 3 个文件里）
```

### 5.3 已知未修（占位页）

扫描发现 6 个占位页（`cockpit / ota / operation / finance / invoice / channel`）各有两处硬编码 `#909399` + `#303133`，但这些页面**只有 `<div class="biz-placeholder">TODO</div>`**，尚未实现业务，等待 Phase 4 真实开发时再清理：

```bash
rg -n '#909399|#303133' ruoyi-fastapi-frontend/src/views/biz/{cockpit,ota,operation,finance,invoice,channel}/index.vue
# 当前：12 行命中（6 页 × 2 处）
```

---

## 6. 后续启示

- **业务页样式必须用 `var(--el-*)` 变量，禁止写死 EP 调色板色值**：在 §四验收标准「样式」项追加一条 ——「所有色值（背景/文字/边框）必须通过 EP CSS 变量引用，禁止硬编码 `#xxxxxx`（业务语义色除外，注：哪些算语义色需要定义）」。
- **暗色适配作为业务页「完成」的前置验收项**：当前台账验收维度是「按钮 / 字段对齐 / 视觉 / 接口契约」4 维，建议增加第 5 维「主题适配」：「切到暗色模式，所有色值跟随主题变化，无白色/浅色块漂浮」。
- **为业务语义色建立显式清单**：本次只识别了 `#f56c6c`（警告/驳回/金额）保留，其他全换变量。下次有类似需求时应该把这清单写到 ADR 里（例如 D25：业务页主题色使用规范）。
- **修一个页时顺手扫同类页**：本次扫描发现 6 个占位页同款硬编码，但因为它们只是 TODO 占位没修。这种"等真开发时再修"是有道理的（避免现在改完未来还得二次调整），但台账里要能查到「已知 TODO：6 个占位页样式合规性待 Phase 4 业务开发时一并处理」。

---

## 关联文件

- `ruoyi-fastapi-frontend/src/views/biz/approval/index.vue` — 9 处替换
- `ruoyi-fastapi-frontend/src/views/biz/contract/index.vue` — 2 处替换
- `ruoyi-fastapi-frontend/src/views/biz/customer/index.vue` — 1 处替换
- `ruoyi-fastapi-frontend/src/store/modules/settings.js:5-6` — 暗色主题机制
- `ruoyi-fastapi-frontend/src/main.js:7` — `element-plus/theme-chalk/dark/css-vars.css` 入口
- `ruoyi-fastapi-frontend/src/views/dashboard/index.vue` — 参考实现（已合规）
- `docs/04-开发/开发进度台账.md` — 待追加「主题适配」验收维度
- `docs/04-开发/ARD/ADR-架构决策记录.md` — 待追加 D25 业务页主题色规范

## 关联已有 DEBUG

- `role-sort-conflict-2026-07-11.md` — 同一类问题（RuoYi 默认值与本项目语义冲突但没改），可参考其"修复执行 + 同步 SQL 脚本 + 同步 ADR 约束"流程