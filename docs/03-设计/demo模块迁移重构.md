# 7级审批流 & 科技感UI · 重构可行性深度分析

> 文档版本：v1.0  
> 分析日期：2026-07-09  
> 分析目的：逐文件分析两个核心功能的具体实现，证明可完整重构

---

## 一、核心结论

```
┌─────────────────────────────────────────────────────────────┐
│                    ✅ 重构完全可行                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  7级审批流：                                               │
│  ├── 后端：约 200 行 Python 代码（明确清晰）               │
│  ├── 前端：约 600 行 Vue 代码（合同页+审批页+详情抽屉）   │
│  └── 可完整移植到 RuoYi 框架                              │
│                                                             │
│  科技感UI（含数据大屏）：                                  │
│  ├── 登录页：约 170 行（CSS 玻璃拟态+动态背景）           │
│  ├── 数据大屏：约 330 行（布局+动画+ECharts配置）         │
│  ├── 飞线地图：约 125 行（ECharts geo 地图+飞线）        │
│  └── 可完整移植到 RuoYi 前端框架                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、7级审批流：逐文件实现分析

### 2.1 后端实现（4个文件）

#### 文件1：`backend/app/core/enums.py` — 审批链定义

```python
# 当前实现：28行，定义审批链
class Role(str, Enum):
    BUSINESS_HANDLER = "business_handler"      # 业务经办
    BUSINESS_REVIEWER = "business_reviewer"    # 业务复核
    RISK_AUDITOR = "risk_auditor"              # 风控审核
    FINANCE_HANDLER = "finance_handler"        # 财务经办
    FINANCE_REVIEWER = "finance_reviewer"      # 财务复核
    SCM_DIRECTOR = "scm_director"              # 供管公司负责人
    INVEST_DIRECTOR = "invest_director"        # 投资公司负责人

# 7级审批链
APPROVAL_CHAIN = [
    Role.BUSINESS_HANDLER,     # Step 0
    Role.BUSINESS_REVIEWER,    # Step 1
    Role.RISK_AUDITOR,         # Step 2
    Role.FINANCE_HANDLER,      # Step 3
    Role.FINANCE_REVIEWER,     # Step 4
    Role.SCM_DIRECTOR,         # Step 5
    Role.INVEST_DIRECTOR,      # Step 6 (最后一关)
]

def role_at_step(step): return APPROVAL_CHAIN[step]
def is_final_step(step): return step == len(APPROVAL_CHAIN) - 1
```

**重构方案：**
```
→ 迁移到 RuoYi：创建新枚举文件 custom_enums.py
→ RuoYi 本身有 Role 模型，改用枚举更符合当前业务
→ 或者：扩展 RuoYi 的 sys_menu 表，添加审批链配置表
```

#### 文件2：`backend/app/models/contract.py` — 合同模型

```python
# 当前实现：58行，核心字段
class Contract(Base):
    __tablename__ = "biz_contract"

    # 基础字段
    contract_no: Mapped[str]   # 合同编号（唯一）
    title: Mapped[str]        # 合同名称
    party_a/party_b: Mapped[str]  # 甲乙方
    amount: Mapped[Decimal]    # 金额
    sign_date: Mapped[date]   # 签订日期
    department/customer_name/business_type: Mapped[str]  # 业务字段

    # 审批流状态
    status: Mapped[ContractStatus]   # draft/pending/approved/rejected
    current_step: Mapped[int]        # 当前步序（0-6）
    created_by: Mapped[int]          # 创建人FK

    # 关系
    approvals: Mapped[list["Approval"]]  # 一对多审批记录
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 保留 biz_contract 表（数据迁移）
  2. 扩展 RuoYi 的 workflow 模块（如果用 RuoYi 的流程引擎）
  3. 或者：作为独立模块，不依赖 RuoYi 的权限体系
```

#### 文件3：`backend/app/models/approval.py` — 审批记录模型

```python
# 当前实现：41行，审计日志+签章快照
class Approval(Base):
    __tablename__ = "biz_approval"

    contract_id: Mapped[int]   # FK 合同
    approver_id: Mapped[int]  # FK 审批人
    step: Mapped[int]         # 审批步序（0-6）
    approver_role: Mapped[str] # 审批时角色
    action: Mapped[ApprovalAction]  # approve/reject
    comment: Mapped[str]       # 意见/驳回原因
    signature_snapshot: Mapped[str]  # 电子签名快照（关键！）
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 保留 biz_approval 表（数据迁移）
  2. 添加 approval_time 字段记录审批时间
  3. 添加 approval_ip 字段记录审批IP（可选）
```

#### 文件4：`backend/app/api/v1/endpoints/contract.py` — 审批逻辑（核心）

```python
# 当前实现：323行，完整的审批流逻辑

# 辅助函数
def _ensure_current_approver(contract, user) -> Role:
    """校验用户是否有权审批当前合同"""
    if contract.status != ContractStatus.PENDING:
        raise HTTPException("不处于审批中")
    expected = role_at_step(contract.current_step)
    if user.role != expected and not user.is_superuser:
        raise HTTPException("无权审批")

# 核心接口
@router.post("/{contract_id}/submit")    # 业务经办提交 → Step 0
@router.post("/{contract_id}/approve")    # 审批通过 → current_step+1 或 approved
@router.post("/{contract_id}/reject")    # 驳回 → rejected
```

**关键逻辑（提交审批）：**
```python
# Step 0：业务经办提交时自动完成，并附加电子签名
db.add(Approval(
    contract_id=contract.id,
    approver_id=current_user.id,
    step=0,
    approver_role=Role.BUSINESS_HANDLER,
    action=ApprovalAction.APPROVE,
    signature_snapshot=current_user.signature,  # 电子签章！
))
contract.status = ContractStatus.PENDING
contract.current_step = 1  # 流转到业务复核
```

**关键逻辑（逐级审批通过）：**
```python
# 每一级：附加审批人的电子签名
db.add(Approval(
    ...
    signature_snapshot=current_user.signature,  # 电子签章！
))
if is_final_step(step):
    contract.status = ContractStatus.APPROVED  # 最后一关通过
else:
    contract.current_step = step + 1  # 流转到下一关
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 在 RuoYi 的 system/ 或 workflow/ 模块中新建 contract.py
  2. 直接复用当前 323 行代码，仅需调整：
     - import 路径（RuoYi 的 deps.py、models.py 路径不同）
     - Response 包装格式（RuoYi 用自己的响应格式）
  3. 审批链角色可扩展到 RuoYi 的 sys_role 表
```

---

### 2.2 前端实现（3个文件）

#### 文件5：`frontend/src/views/contract/index.vue` — 合同管理页

```vue
<!-- 当前实现：276行 -->

<!-- 核心功能： -->
1. 合同列表（业务经办仅看自己，审批人看全部）
2. 新建/编辑合同（el-dialog 表单）
3. 提交审批按钮（仅业务经办可见）
4. 删除按钮（仅草稿/驳回态可见）
5. 详情抽屉（打开 ContractDetailDrawer）
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 在 RuoYi 前端的 src/views/ 模块下新建 contract/ 目录
  2. 复制 contract/index.vue
  3. 调整 API 路径（from '@/api/contract' 改为 RuoYi 的 API 模式）
  4. 复用 el-table、el-dialog、el-form 等 Element Plus 组件
```

#### 文件6：`frontend/src/views/approval/index.vue` — 审批中心

```vue
<!-- 当前实现：163行 -->

<!-- 核心功能： -->
1. 待我审批列表（过滤：current_step = 我的角色）
2. 通过按钮 → 弹窗填写意见 → 调用 approve 接口
3. 驳回按钮 → 弹窗填写原因（必填）→ 调用 reject 接口
4. 查看详情 → 打开 ContractDetailDrawer
```

**审批通过弹窗：**
```vue
<el-alert type="success" title="通过后将自动附加您的电子签名" />
<el-input v-model="fm.comment" placeholder="审批意见（可选）" />
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 新建 approval/index.vue
  2. 复用当前逻辑，仅调整 API 调用方式
  3. RuoYi 有现成的 el-table 和弹窗组件，可直接用
```

#### 文件7：`frontend/src/components/ContractDetailDrawer.vue` — 合同详情抽屉 ⭐ 核心亮点

```vue
<!-- 当前实现：277行，最复杂的组件 -->

<!-- 核心功能： -->
1. 合同基本信息（el-descriptions）
2. 7级审批进度条（el-steps）
3. 审批时间轴（el-timeline）← 审计日志
4. 电子签名展示 ← 签章快照
5. 打印审批单 ← 关键功能！
```

**7级审批进度条：**
```vue
<el-steps :active="stepsActive" align-center finish-status="success">
  <el-step v-for="(r, i) in APPROVAL_CHAIN" :key="r" :title="roleLabel(r)" />
</el-steps>

<!-- stepsActive 计算： -->
if (status === 'approved') return 7  // 全部完成
if (status === 'draft') return 0    // 未开始
return current_step                   // pending/rejected 停在当前
```

**审批时间轴（带签章）：**
```vue
<el-timeline>
  <el-timeline-item v-for="a in approvals">
    <span class="flow-role">{{ a.role_label }}</span>
    <el-tag>{{ a.action === 'reject' ? '驳回' : '通过' }}</el-tag>
    <span class="flow-approver">{{ a.approver_name }}</span>
    <div class="flow-comment" v-if="a.comment">{{ a.comment }}</div>
    <img v-if="a.signature_snapshot" :src="a.signature_snapshot" class="flow-sig" />  ← 签章！
  </el-timeline-item>
</el-timeline>
```

**打印审批单（teleport + @media print）：**
```vue
<!-- 使用 teleport 渲染到 body，然后用 CSS 控制打印 -->
<div class="approval-print-root">
  <div class="print-sheet">
    <div class="print-title">山东出版供应链管理有限公司</div>
    <table class="print-table">
      <!-- 合同信息 -->
      <tr><th>申请部门</th><td>{{ department }}</td>...</tr>
    </table>
    <table class="print-sign-table">
      <!-- 签章表 -->
      <tr v-for="a in approvals">
        <td>{{ a.role_label }}</td>
        <td>{{ a.approver_name }}</td>
        <td>{{ a.comment }}</td>
        <td><img :src="a.signature_snapshot" class="print-sig" /></td>  ← 打印签章
      </tr>
    </table>
  </div>
</div>

<style>
@media print {
  body * { visibility: hidden !important; }
  .approval-print-root { display: block !important; }
}
</style>
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 新建 components/ContractDetailDrawer.vue
  2. 复用全部当前代码（约 277 行）
  3. 调整：
     - APPROVAL_CHAIN 数据来源（可从后端接口获取）
     - 打印样式（保持 A4 格式即可）
  4. RuoYi 的布局系统兼容此组件
```

---

### 2.3 审批流代码行数统计

| 文件 | 路径 | 行数 | 迁移难度 |
|------|------|------|---------|
| `enums.py` | 后端 | 28 | ⭐ 简单 |
| `contract.py` (model) | 后端 | 58 | ⭐ 简单 |
| `approval.py` (model) | 后端 | 41 | ⭐ 简单 |
| `contract.py` (endpoint) | 后端 | 323 | ⭐⭐ 中等 |
| `contract/index.vue` | 前端 | 276 | ⭐⭐ 中等 |
| `approval/index.vue` | 前端 | 163 | ⭐⭐ 中等 |
| `ContractDetailDrawer.vue` | 前端 | 277 | ⭐⭐ 中等 |
| **合计** | 7个文件 | **1166行** | **可完整移植** |

---

## 三、科技感UI：逐文件实现分析

### 3.1 登录页（`frontend/src/views/login/index.vue`）

```vue
<!-- 当前实现：170行 -->

<!-- 视觉效果： -->
1. 科技动态背景网格（perspective rotateX + animation）
2. 玻璃拟态卡片（backdrop-filter blur + 边框光晕）
3. 光晕动画（两个圆球 float 动画）
4. 渐变文字标题（background-clip text）
```

**核心 CSS 特效：**

```scss
/* 动态网格背景 */
.bg-grid {
  background-image:
    linear-gradient(rgba(34,211,238,0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34,211,238,0.08) 1px, transparent 1px);
  background-size: 44px 44px;
  transform: perspective(400px) rotateX(60deg);
  animation: gridmove 18s linear infinite;
}
@keyframes gridmove { from { background-position: 0 0; } to { background-position: 0 440px; } }

/* 玻璃拟态卡片 */
.login-card {
  background: rgba(10, 28, 60, 0.55) !important;
  backdrop-filter: blur(14px);
  border: 1px solid rgba(34, 211, 238, 0.35) !important;
  box-shadow: 0 0 40px rgba(28, 155, 230, 0.3);
}

/* 渐变文字 */
.title {
  background: linear-gradient(90deg, #eafcff, #7fd8ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 删除 RuoYi 单文件 `src/views/login.vue`
  2. 新建目录 `src/views/login/`，将 v1 代码移入 `index.vue`（方案 A，见 ADR D23）
  3. 更新 `src/router/index.js` 中的路由引用为 `import('@/views/login/index.vue')`
  4. 保留当前 170 行代码，仅调整 API 调用方式（RuoYi 用自己的 auth API）和路由跳转
  5. CSS 特效完全复用；图片资源迁移到 `src/assets/`
```

### 3.2 数据大屏主组件（`frontend/src/components/screen/DataScreen.vue`）

```vue
<!-- 当前实现：327行 -->

<!-- 页面结构： -->
<template>
  <div class="ds">
    <!-- 顶部标题栏 -->
    <header class="screen-head">
      <span class="title-cn">山东出版供应链管理</span>
      <span class="title-en">SD PUBLISHING SUPPLY-CHAIN DATA CENTER</span>
      <span class="clock">{{ clock }}</span>  <!-- 实时时钟 -->
    </header>

    <!-- 三栏布局 -->
    <div class="screen-body">
      <!-- 左栏：核心指标 + 月度趋势图 -->
      <section class="col-left">
        <div class="metrics">
          <div class="metric" v-for="m in metricCards">
            <CountTo :value="m.value" :prefix="m.prefix" />
          </div>
        </div>
        <BaseChart :option="areaOption" />  <!-- ECharts 面积图 -->
      </section>

      <!-- 中栏：天眼地图（核心亮点） -->
      <section class="col-center">
        <ScreenMap :data="provinceData" hub="山东省" />
      </section>

      <!-- 右栏：审批跑马灯 + AI雷达 -->
      <section class="col-right">
        <div class="marquee">  <!-- 滚动字幕 -->
          <div class="mq-item" v-for="it in marqueeLoop">
            {{ it.no }} - {{ it.title }} - {{ it.role }}
          </div>
        </div>
        <BaseChart :option="radarOption" />  <!-- ECharts 雷达图 -->
        <AiTyper :messages="aiMessages" />  <!-- AI打字机 -->
      </section>
    </div>
  </div>
</template>
```

**核心交互：**
1. 时钟每秒更新（`setInterval`）
2. 省份点击联动（`onProvince` → 更新 `region` → 刷新指标卡）
3. 审批跑马灯（CSS `scrollUp` 动画，鼠标悬停暂停）
4. AI 打字机（`setTimeout` 逐字显示）

**ECharts 配置示例（月度趋势面积图）：**
```javascript
areaOption = {
  backgroundColor: 'transparent',
  grid: { left: 46, right: 16, top: 16, bottom: 24 },
  xAxis: { type: 'category', data: months, ... },
  yAxis: { type: 'value', formatter: (v) => v / 10000 + '万', ... },
  series: [{
    type: 'line', smooth: true, symbol: 'none',
    lineStyle: { color: '#2de1c2', width: 2 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(45,225,194,0.5)' },
          { offset: 1, color: 'rgba(45,225,194,0.02)' }
        ]
      }
    }
  }]
}
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 在 RuoYi 前端新建 views/screen/index.vue
  2. 复制当前 327 行代码
  3. 调整 API 调用（RuoYi 用自己的 API 模式）
  4. 布局可保持三栏或改为 RuoYi 的 Dashboard 布局
  5. ECharts 配置完全复用
```

### 3.3 飞线地图组件（`frontend/src/components/screen/ScreenMap.vue`）

```vue
<!-- 当前实现：125行 -->

<!-- 核心功能： -->
1. 中国地图底图（从 geo.datav.aliyun.com 加载）
2. 省份气泡（effectScatter，大小与业务额成正比）
3. 飞线动画（lines + effect + arrow）
4. 点击省份事件（emit 给父组件）
```

**ECharts geo 地图配置：**
```javascript
async function ensureMap() {
  // 从阿里云数据可视化平台加载地图 JSON
  const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
  echarts.registerMap('china', await resp.json())
}

buildOption() {
  return {
    geo: {
      map: 'china', roam: true, zoom: 1.15,
      itemStyle: {
        areaColor: 'rgba(9,34,74,0.75)',
        borderColor: 'rgba(44,225,192,0.35)'
      },
      emphasis: {
        itemStyle: { areaColor: 'rgba(28,155,230,0.45)' }
      }
    },
    series: [
      { type: 'map', map: 'china' },  // 地图底色
      {
        name: '物流飞线', type: 'lines',
        effect: { show: true, period: 5, trailLength: 0.55, symbol: 'arrow' },
        lineStyle: { color: '#39c5ff', curveness: 0.25 },
        data: lines  // [[hub, province1], [hub, province2], ...]
      },
      {
        name: '业务节点', type: 'effectScatter',
        rippleEffect: { brushType: 'stroke', scale: 4 },
        symbolSize: (val) => 6 + (val[2] / max) * 18,
        data: scatter
      },
      {
        name: '中枢', type: 'effectScatter',
        symbolSize: 16,
        itemStyle: { color: '#ffd34e' },
        data: [{ name: '山东省', value: [...hubCoord, max] }]
      }
    ]
  }
}
```

**省份经纬度映射：**
```javascript
const GEO = {
  山东省: [117.0, 36.65], 广东省: [113.28, 23.13],
  江苏省: [118.78, 32.04], 浙江省: [120.15, 30.28],
  // ...
}
```

**重构方案：**
```
→ 迁移到 RuoYi：
  1. 复制 ScreenMap.vue 到 RuoYi 前端
  2. 完全复用 125 行代码
  3. 仅需确保 ECharts 已安装（RuoYi 默认有 ECharts）
  4. 地图数据源可保持阿里云或改为本地静态文件
```

### 3.4 辅助组件

#### `CountTo.vue` — 数字滚动动画
```vue
<!-- 当前实现：约 50 行 -->
<!-- 功能：数字从 0 滚动到目标值，支持前缀/后缀 -->
```

#### `BaseChart.vue` — ECharts 封装
```vue
<!-- 当前实现：约 30 行 -->
<!-- 功能：封装 echarts.init + resize + setOption -->
```

### 3.5 UI代码行数统计

| 文件 | 行数 | 迁移难度 |
|------|------|---------|
| `login/index.vue` (登录页) | 170 | ⭐ 简单 |
| `screen/DataScreen.vue` (大屏) | 327 | ⭐⭐ 中等 |
| `screen/ScreenMap.vue` (地图) | 125 | ⭐ 简单 |
| `screen/CountTo.vue` (数字动画) | 50 | ⭐ 简单 |
| `BaseChart.vue` (ECharts封装) | 30 | ⭐ 简单 |
| **合计** | **702行** | **可完整移植** |

---

## 四、完整重构方案

### 4.1 项目结构映射

```
当前项目                           RuoYi-Vue3-FastAPI
─────────────────────────────────────────────────────────────────────

后端 backend/app/
  ├── core/enums.py         →  custom_enums.py 或扩展 sys_role 表
  ├── models/contract.py    →  新建 app/models/biz_contract.py
  ├── models/approval.py    →  新建 app/models/biz_approval.py
  └── api/contract.py       →  新建 app/api/v1/endpoints/biz_contract.py

前端 frontend/src/
  ├── views/login/         →  删除 RuoYi 的 views/login.vue，新建 views/login/index.vue（ADR D23）
  ├── views/contract/       →  新建 views/biz/contract/
  ├── views/approval/       →  新建 views/biz/approval/
  ├── views/screen/         →  新建 views/screen/
  ├── components/screen/     →  复制 components/screen/*
  └── constants/business.js  →  custom_constants.js
```

### 4.2 分步骤重构计划

```
┌─────────────────────────────────────────────────────────────┐
│                    重构步骤（预计 2 周）                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  第1步：数据库设计（半天）                                  │
│  ├── 复用当前 7 张表（sys_user, biz_contract 等）         │
│  └── 新增审批链配置表（可选，支持动态配置）                │
│                                                             │
│  第2步：后端审批流（1天）                                  │
│  ├── 迁移 enums.py（28行）                                │
│  ├── 迁移 contract.py model（58行）                       │
│  ├── 迁移 approval.py model（41行）                        │
│  └── 迁移 contract.py endpoint（323行）                   │
│  → 合计约 450 行 Python 代码                               │
│                                                             │
│  第3步：前端审批流（2天）                                  │
│  ├── 迁移 contract/index.vue（276行）                      │
│  ├── 迁移 approval/index.vue（163行）                      │
│  └── 迁移 ContractDetailDrawer.vue（277行）               │
│  → 合计约 716 行 Vue 代码                                  │
│                                                             │
│  第4步：登录页迁移（半天）                                 │
│  ├── 删除 RuoYi 的 src/views/login.vue                  │
│  ├── 新建 src/views/login/ 目录，放入 index.vue         │
│  ├── 更新 router/index.js 中的 import 路径               │
│  └── 复用 CSS 特效（170行）                             │
│                                                             │
│  第5步：数据大屏迁移（2天）                                │
│  ├── 新建 views/screen/index.vue（327行）                  │
│  ├── 迁移 ScreenMap.vue（125行）                          │
│  ├── 迁移 CountTo.vue（50行）                             │
│  └── 迁移 BaseChart.vue（30行）                           │
│                                                             │
│  第6步：集成调试（1天）                                    │
│  ├── 调整 API 路径                                         │
│  ├── 调整 路由守卫                                         │
│  └── 测试完整审批流程                                       │
│                                                             │
│  第7步：数据迁移（半天）                                    │
│  ├── 导出当前数据                                          │
│  └── 导入到新系统                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 关键技术点

#### 审批流核心算法

```python
# 提交审批：Step 0 自动完成
def submit(contract, user):
    # 1. 创建 Step 0 审批记录（业务经办提交）
    approval = Approval(
        step=0,
        approver_role=Role.BUSINESS_HANDLER,
        signature_snapshot=user.signature  # 电子签章
    )
    # 2. 合同进入审批流
    contract.status = PENDING
    contract.current_step = 1

# 审批通过
def approve(contract, user):
    # 1. 创建审批记录
    approval = Approval(
        step=contract.current_step,
        signature_snapshot=user.signature  # 电子签章
    )
    # 2. 判断是否最后一关
    if contract.current_step == 6:  # INVEST_DIRECTOR
        contract.status = APPROVED
    else:
        contract.current_step += 1  # 流转到下一关
```

#### 签章快照存储

```python
# 审批时保存签名图片的 data-URI 或 URL
signature_snapshot = current_user.signature  # 从 User.signature 字段读取
# 存储在 biz_approval 表的 signature_snapshot 字段
# 打印时从该字段读取并渲染
```

#### 飞线地图数据流

```javascript
// 1. 定义省份经纬度
const GEO = { 山东省: [117.0, 36.65], ... }

// 2. 加载地图 JSON
await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
echarts.registerMap('china', json)

// 3. 生成飞线数据
const hubCoord = GEO['山东省']
const lines = provinces.map(p => ({
  coords: [hubCoord, GEO[p.name]]  // 从山东到各省
}))

// 4. 渲染飞线 + 气泡
series: [
  { type: 'lines', effect: { symbol: 'arrow' }, data: lines },
  { type: 'effectScatter', data: provinces }
]
```

---

## 五、重构可行性总结

### 5.1 代码量评估

| 模块 | 当前行数 | 迁移难度 | 备注 |
|------|---------|---------|------|
| 7级审批流后端 | ~450行 | ⭐⭐ 中等 | 逻辑清晰，无框架依赖 |
| 7级审批流前端 | ~716行 | ⭐⭐ 中等 | 复用 Element Plus 组件 |
| 登录页UI | ~170行 | ⭐ 简单 | 纯 CSS 特效 |
| 数据大屏 | ~532行 | ⭐⭐ 中等 | ECharts 配置复杂 |
| **总计** | **~1868行** | **可完成** | |

### 5.2 迁移风险评估

| 风险点 | 概率 | 影响 | 应对 |
|--------|------|------|------|
| 审批流逻辑不兼容 RuoYi | 低 | 高 | 可作为独立模块，不依赖 RuoYi 权限 |
| ECharts 地图加载失败 | 中 | 低 | 降级为省份列表展示 |
| 打印样式不兼容 | 低 | 低 | CSS @media print 兼容性很好 |
| 数据迁移丢失 | 低 | 高 | 先备份，执行完整数据导出导入 |

### 5.3 最终结论

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ✅ 重构完全可行                                           │
│                                                             │
│  理由：                                                    │
│  1. 审批流代码逻辑清晰，无复杂框架依赖                      │
│  2. UI 代码全为标准 Vue + CSS + ECharts                    │
│  3. 核心差异化（审批流+签章+大屏）可完整移植               │
│  4. 预计 2 周可完成重构                                    │
│                                                             │
│  建议方案：                                                │
│  方案A：完整重构（推荐）                                    │
│  → 基于 RuoYi 框架，从头搭建                               │
│  → 迁移审批流+大屏代码                                      │
│  → 补齐 RuoYi 缺失的系统功能                               │
│                                                             │
│  方案B：渐进增强                                            │
│  → 保留当前项目，逐步补充缺失功能                           │
│  → RuoYi 作为参考而非替代                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*文档结束*
