# UI 视觉还原规格书

> 文档版本：v1.0  
> 创建日期：2026-07-10  
> 文档目的：在 RuoYi-Vue3-FastAPI 框架基础上，**视觉风格还原** v1 demo 的科技风深色主题  
> 适用人员：前端开发、UI 设计、验收测试

---

## 一、问题与决策

### 1.1 现状差异

| 维度 | RuoYi 默认 | v1 demo | 用户期望 |
|------|-----------|---------|----------|
| **基础框架** | Vue 3 + Element Plus + Ant Design Vue（混合） | Vue 3 + Element Plus + ECharts | **RuoYi 框架，复用其权限/路由/状态管理** |
| **整体风格** | 浅色商务风 | **全站科技风深色主题** | **复刻 v1 demo 的科技风视觉** |
| **主色调** | 浅蓝 `#409EFF` | **科技蓝 `#1c9be6` + 青色 `#22d3ee`** | **复刻 v1 demo 科技蓝** |
| **背景** | 浅灰 `#f0f2f5` | **径向渐变深蓝 `#071228 → #0a1a35` + 双光晕** | **复刻 v1 demo 渐变背景** |
| **卡片质感** | 普通白底圆角 | **玻璃霓虹（rgba + backdrop-blur + 顶部蓝青渐变线）** | **复刻 v1 demo 玻璃质感** |
| **侧边栏** | `#304156` 深灰 | **180° 深蓝渐变 + 渐变文字 logo** | **复刻 v1 demo 渐变侧栏** |
| **按钮** | Element Plus 默认 | **主按钮 135° 蓝青渐变 + 发光阴影** | **复刻 v1 demo 渐变按钮** |
| **表格表头** | 浅灰 `#f8f8f9` | **深蓝渐变 + 浅蓝文字 + 蓝色 hover** | **复刻 v1 demo 暗色表格** |
| **业务页面** | 通用 admin 风 | **业务特色（审批流跑马灯、数据大屏、AI 智能大脑）** | **页面布局沿用 v1 demo** |

### 1.2 核心决策

**决策 1：以 RuoYi 框架为底座，覆写 SCSS 主题变量实现科技风还原。**

- 不引入额外 UI 框架，继续使用 Element Plus
- 在 RuoYi 的 `variables.module.scss` 上**覆写主色、背景、卡片、按钮**等关键变量
- 新增 `src/assets/styles/theme/` 目录存放 v1 demo 风格的样式覆盖
- 业务页面（合同、审批、客户、渠道、发票、经营数据）**布局沿用 v1 demo**

**决策 2：v1 demo 的页面布局可直接复用，但需要迁移到 RuoYi 框架。**

- v1 demo 的 9 个业务页面（合同列表、详情抽屉、审批中心、客户、渠道、发票、经营数据、数据大屏、首页）的**布局结构、组件组合方式、字段位置**可直接参考
- 但 v1 demo 的代码耦合在 `1/frontend/`，需要重新组织到 RuoYi 框架下
- 数据大屏（`/dashboard`）保留 v1 demo 的三栏指挥中心风格

**决策 3：v1 demo 中 demo 专用的演示元素需要替换或去除。**

- 演示用固定账号密码、emoji logo、示例 CSV 数据等需要替换为真实数据
- "演示区域，不会真实上传"等提示语需删除
- 打印审批单（A4）功能保留（业务实用）

---

## 二、整体视觉规范

### 2.1 颜色系统

**主色板（覆写 RuoYi Element Plus 变量）：**

| 用途 | 变量名 | 色值 | 说明 |
|------|--------|------|------|
| 主色（Primary） | `--el-color-primary` | `#1c9be6` | 科技蓝 |
| 浅主色（Light） | `--el-color-primary-light-3` | `#5cb8eb` | hover/禁用 |
| 暗主色（Dark） | `--el-color-primary-dark-2` | `#1684c5` | 按下态 |
| 辅色（Accent） | `--tech-cyan` | `#22d3ee` | 青色高亮 |
| 成功 | `--el-color-success` | `#67C23A` | 沿用 Element Plus |
| 警告 | `--el-color-warning` | `#E6A23C` | 沿用 Element Plus |
| 危险 | `--el-color-danger` | `#F56C6C` | 沿用 Element Plus |
| 信息 | `--el-color-info` | `#909399` | 沿用 Element Plus |

**背景色板：**

| 用途 | 色值 | 用途场景 |
|------|------|----------|
| 全局背景 | `radial-gradient(ellipse at bottom left, #0a1a35 0%, #071228 50%)` | 主内容区 |
| 全局背景（右上光晕） | `radial-gradient(circle at 90% 10%, rgba(28,155,230,0.18) 0%, transparent 45%)` | 叠加层 |
| 全局背景（左下光晕） | `radial-gradient(circle at 10% 90%, rgba(34,211,238,0.12) 0%, transparent 40%)` | 叠加层 |
| 卡片背景 | `rgba(14, 34, 68, 0.72)` | el-card 容器 |
| 卡片悬停背景 | `rgba(14, 34, 68, 0.85)` | 鼠标悬停 |
| 表格行背景（奇数） | `rgba(10, 28, 60, 0.45)` | el-table 隔行 |
| 表格行背景（偶数） | `rgba(14, 34, 68, 0.55)` | el-table 隔行 |
| 表格行悬停 | `rgba(28, 155, 230, 0.12)` | hover |
| 输入框背景 | `rgba(10, 28, 60, 0.45)` | el-input |
| 下拉框/弹窗背景 | `rgba(14, 34, 68, 0.95)` + `backdrop-filter: blur(12px)` | el-dialog / el-select dropdown |

**文字色板：**

| 用途 | 色值 | 适用场景 |
|------|------|----------|
| 主文字 | `#dcecff` | 标题、关键信息 |
| 常规文字 | `#a9c2e0` | 表格内容、描述 |
| 次要文字 | `#7f9ec6` | 提示、辅助 |
| 占位文字 | `#5b7aa6` | 输入框 placeholder |
| 链接文字 | `#5cb8eb` | 可点击链接 |
| 反白文字 | `#071228` | 浅色按钮上的文字 |

**边框色板：**

| 用途 | 色值 |
|------|------|
| 卡片边框 | `rgba(96, 150, 210, 0.2)` |
| 卡片顶部装饰线 | `linear-gradient(90deg, #1c9be6, #22d3ee)`（2px） |
| 输入框边框 | `rgba(96, 150, 210, 0.3)` |
| 表格边框 | `rgba(96, 150, 210, 0.16)` |
| 按钮主色 hover 时增强 | `rgba(28, 155, 230, 0.5)` |

### 2.2 字体规范

| 层级 | 字体 | 字号 | 字重 | 颜色 |
|------|------|------|------|------|
| 全局字体 | `'Segoe UI', 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif` | 14px | 400 | `#a9c2e0` |
| 大标题（如页面 H1） | 同上 | 22px | 600 | `#dcecff` |
| 卡片标题 | 同上 | 16px | 600 | `#dcecff` |
| 表格表头 | 同上 | 13px | 600 | `#cfe6ff` |
| 表格内容 | 同上 | 13px | 400 | `#a9c2e0` |
| 提示文字 | 同上 | 12px | 400 | `#7f9ec6` |
| 大数字（KPI） | `'Avenir', 'Helvetica Neue', sans-serif` | 28px | 700 | `#dcecff` |
| 中文大写（金额） | 同上 | 14px | 500 | `#22d3ee` |

### 2.3 间距规范

| 用途 | 尺寸 |
|------|------|
| 页面内边距 | `16px` |
| 卡片间距 | `16px` |
| 表单项间距 | `18px` |
| 表格行高 | `44px`（v1 demo 紧凑风格） |
| 弹窗内边距 | `20px` |
| 抽屉内边距 | `20px` |

### 2.4 圆角与阴影

| 元素 | 圆角 | 阴影 |
|------|------|------|
| 主按钮 | `4px` | `0 4px 12px rgba(28,155,230,0.3)` |
| 主按钮 hover | `4px` | `0 6px 18px rgba(28,155,230,0.5)` |
| 普通按钮 | `4px` | 无 |
| 卡片 | `10px` | `0 4px 18px rgba(2, 10, 28, 0.5)` |
| 卡片 hover | `10px` | `0 8px 24px rgba(28,155,230,0.2)` + `translateY(-2px)` |
| 输入框 | `4px` | 无 |
| 弹窗 | `12px` | `0 16px 48px rgba(0,0,0,0.4)` |
| 抽屉 | `0`（左侧） | `-2px 0 12px rgba(0,0,0,0.3)` |

---

## 三、布局结构

### 3.1 整体布局

```
┌──────────────────────────────────────────────────────────────────┐
│  侧边栏 (220px)  │   顶栏 (60px)                                │
│  深蓝渐变        ├──────────────────────────────────────────────┤
│                  │                                              │
│  Logo            │  标签栏 (34px) — RuoYi 特性保留               │
│  菜单            ├──────────────────────────────────────────────┤
│                  │                                              │
│                  │  主内容区                                     │
│                  │  径向渐变背景 + 双光晕                         │
│                  │                                              │
│                  │  ┌────────┐ ┌────────┐ ┌────────┐            │
│                  │  │ 卡片1  │ │ 卡片2  │ │ 卡片3  │            │
│                  │  └────────┘ └────────┘ └────────┘            │
│                  │                                              │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 侧边栏规范

**宽度与高度：**

| 属性 | 值 |
|------|---|
| 宽度（展开） | `220px` |
| 宽度（折叠） | `64px` |
| 高度 | `100vh` |
| 位置 | `fixed` 左 |

**样式：**

```css
background: linear-gradient(180deg, #0a1a35 0%, #050f1f 100%);
box-shadow: 2px 0 12px rgba(0, 0, 0, 0.3);
```

**Logo 区：**

- 高度 `60px`
- 居中显示应用 Logo + 名称
- 名称使用渐变文字 `linear-gradient(90deg, #39c5ff, #22d3ee)`
- 字体 `Avenir, Helvetica Neue, Arial`，字号 16px，字重 600

**菜单项：**

| 状态 | 样式 |
|------|------|
| 默认 | 文字 `#a9c2e0`，背景透明 |
| hover | 背景 `rgba(28, 155, 230, 0.08)`，文字 `#dcecff` |
| 选中 | 文字 `#ffffff`，背景 `linear-gradient(90deg, rgba(28,155,230,0.25) 0%, rgba(28,155,230,0.05) 100%)`，左侧 3px `#22d3ee` 实线 |
| 图标 | 18px，继承文字颜色 |

### 3.3 顶栏规范

**样式：**

| 属性 | 值 |
|------|---|
| 高度 | `60px` |
| 背景 | `linear-gradient(90deg, #1c9be6 0%, #1684c5 100%)` |
| 阴影 | `0 2px 8px rgba(0,0,0,0.15)` |
| 位置 | `fixed`，右侧距侧栏 `220px`，顶部 `0` |

**元素：**

- 左侧：折叠按钮、面包屑
- 中部：页面标题（渐变文字 `linear-gradient(90deg, #eafcff, #7fd8ff)`）
- 右侧：搜索、消息、全屏、用户头像下拉

### 3.4 标签栏（保留 RuoYi 特性）

| 属性 | 值 |
|------|---|
| 高度 | `34px` |
| 背景 | `rgba(10, 28, 60, 0.55)` |
| 标签默认 | 背景 `rgba(14, 34, 68, 0.6)`，文字 `#a9c2e0` |
| 标签 active | 背景 `linear-gradient(180deg, #1c9be6, #1684c5)`，文字 `#ffffff` |

### 3.5 主内容区

**背景：**

```css
background: 
  radial-gradient(circle at 90% 10%, rgba(28,155,230,0.18) 0%, transparent 45%),
  radial-gradient(circle at 10% 90%, rgba(34,211,238,0.12) 0%, transparent 40%),
  #071228;
min-height: calc(100vh - 94px);
padding: 16px;
```

---

## 四、核心组件样式

### 4.1 按钮（el-button）

**主按钮（primary）：**

```css
background: linear-gradient(135deg, #1c9be6 0%, #22d3ee 100%);
border: none;
color: #ffffff;
box-shadow: 0 4px 12px rgba(28,155,230,0.3);
transition: all 0.3s;

&:hover {
  background: linear-gradient(135deg, #22d3ee 0%, #1c9be6 100%);
  box-shadow: 0 6px 18px rgba(28,155,230,0.5);
  transform: translateY(-1px);
}

&:active {
  transform: translateY(0);
}
```

**成功按钮（success）：** 通过审批等场景

```css
background: linear-gradient(135deg, #67C23A 0%, #5daf34 100%);
border: none;
color: #ffffff;
box-shadow: 0 4px 12px rgba(103,194,58,0.3);
```

**危险按钮（danger）：** 驳回、删除等场景

```css
background: linear-gradient(135deg, #F56C6C 0%, #dd6161 100%);
border: none;
color: #ffffff;
box-shadow: 0 4px 12px rgba(245,108,108,0.3);
```

**次按钮（默认）：**

```css
background: rgba(14, 34, 68, 0.6);
border: 1px solid rgba(96, 150, 210, 0.3);
color: #dcecff;

&:hover {
  background: rgba(14, 34, 68, 0.8);
  border-color: rgba(96, 150, 210, 0.5);
  color: #ffffff;
}
```

### 4.2 卡片（el-card）

```css
background: rgba(14, 34, 68, 0.72);
backdrop-filter: blur(6px);
-webkit-backdrop-filter: blur(6px);
border: 1px solid rgba(96, 150, 210, 0.2);
border-radius: 10px;
box-shadow: 0 4px 18px rgba(2, 10, 28, 0.5);
position: relative;
overflow: hidden;
transition: all 0.3s;

/* 顶部装饰线 */
&::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, #1c9be6, #22d3ee);
}

.el-card__header {
  padding: 14px 20px;
  border-bottom: 1px solid rgba(96, 150, 210, 0.2);
  color: #dcecff;
  font-size: 16px;
  font-weight: 600;
}

.el-card__body {
  padding: 20px;
}
```

### 4.3 表格（el-table）

```css
background: transparent;
color: #a9c2e0;

.el-table__header-wrapper th {
  background: linear-gradient(180deg, #123057 0%, #0e2244 100%);
  color: #cfe6ff;
  font-weight: 600;
  border-bottom: 1px solid rgba(96, 150, 210, 0.3);
}

.el-table__row {
  background: rgba(10, 28, 60, 0.45);
  
  &.el-table__row--striped {
    background: rgba(14, 34, 68, 0.55);
  }
  
  &.hover-row, &:hover {
    background: rgba(28, 155, 230, 0.12) !important;
  }
}

.el-table__cell {
  border-bottom: 1px solid rgba(96, 150, 210, 0.16);
}

.el-table__empty-block {
  background: transparent;
}

.el-table__empty-text {
  color: #7f9ec6;
}
```

### 4.4 输入框（el-input / el-textarea / el-select）

```css
.el-input__wrapper, .el-textarea__inner {
  background: rgba(10, 28, 60, 0.45);
  box-shadow: 0 0 0 1px rgba(96, 150, 210, 0.3) inset;
  border-radius: 4px;
  
  &:hover {
    box-shadow: 0 0 0 1px rgba(96, 150, 210, 0.5) inset;
  }
  
  &.is-focus {
    box-shadow: 0 0 0 1px #1c9be6 inset, 0 0 0 2px rgba(28,155,230,0.2);
  }
}

.el-input__inner, .el-textarea__inner {
  color: #dcecff;
  
  &::placeholder {
    color: #5b7aa6;
  }
}
```

### 4.5 弹窗（el-dialog）

```css
background: rgba(14, 34, 68, 0.95);
backdrop-filter: blur(12px);
border: 1px solid rgba(96, 150, 210, 0.3);
border-radius: 12px;
box-shadow: 0 16px 48px rgba(0,0,0,0.4);

.el-dialog__title {
  color: #dcecff;
  font-weight: 600;
}

.el-dialog__headerbtn .el-dialog__close {
  color: #a9c2e0;
}
```

### 4.6 抽屉（el-drawer）

```css
background: rgba(14, 34, 68, 0.95);
backdrop-filter: blur(12px);

.el-drawer__header {
  margin-bottom: 16px;
  padding: 16px 20px 0;
  color: #dcecff;
}
```

### 4.7 Tag（el-tag）

| 类型 | 样式 |
|------|------|
| `primary` | 背景 `rgba(28,155,230,0.18)`，文字 `#5cb8eb`，边框 `rgba(28,155,230,0.3)` |
| `success` | 背景 `rgba(103,194,58,0.18)`，文字 `#85ce61`，边框 `rgba(103,194,58,0.3)` |
| `warning` | 背景 `rgba(230,162,60,0.18)`，文字 `#eebe77`，边框 `rgba(230,162,60,0.3)` |
| `danger` | 背景 `rgba(245,108,108,0.18)`，文字 `#f89898`，边框 `rgba(245,108,108,0.3)` |
| `info` | 背景 `rgba(144,147,153,0.18)`，文字 `#a6a9ad`，边框 `rgba(144,147,153,0.3)` |

### 4.8 滚动条

```css
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(10, 28, 60, 0.3);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #1c9be6, #22d3ee);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #22d3ee, #1c9be6);
}
```

---

## 五、业务页面布局规格

### 5.1 合同管理 `/contract`

**布局结构：**

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─ 工具栏 ────────────────────────────────────────────┐   │
│  │ [搜索框: 合同编号/名称]    [+ 新建合同]  [刷新]    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ 合同列表表格 ──────────────────────────────────────┐   │
│  │ 合同编号 │ 合同名称 │ 类型 │ 客户 │ 金额 │ 状态 │ 操作│   │
│  │ HT-001   │ 景区...  │ tag  │ xx   │ 50万 │ tag  │ ...  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ 分页 ──────────────────────────────────────────────┐    │
│  │ 共 50 条  [<] 1 2 3 4 5 [>]  [10条/页]              │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**表格列规范：**

| 列名 | 宽度 | 对齐 | 渲染 |
|------|------|------|------|
| 合同编号 | 150 | 左 | 文本 |
| 合同名称 | min-180 | 左 | show-overflow-tooltip |
| 类型 | 130 | 居中 | `el-tag effect="plain"` 业务付款/业务审批 |
| 客户 | min-130 | 左 | 文本 |
| 金额（元） | 130 | 右 | 千分位 + `¥` 前缀 |
| 状态 | 160 | 居中 | tag（draft/pending/approved/rejected） + 下方小字 `当前：xxx` |
| 操作 | 280 | 居中 | 详情 / 编辑 / 提交 / 删除 link 按钮 |

**新建/编辑弹窗（el-dialog）：**

```
宽度: 600px
标题: 新建合同 / 编辑合同 / 详情查看

表单字段:
- 单据类型 [el-radio-group 业务付款审批单 / 业务审批单]
- 合同编号 [el-input]
- 合同名称 [el-input]
- 申请部门 / 业务类型 [el-row 2 列]
- 客户名称 [el-select + biz/customer/list]
- 乙方 [el-input, 默认 "山东出版供应链管理公司"]
- 金额 [el-input-number, step=10000]
- 签订日期 [el-date-picker]
- 备注 [el-textarea]
- 合同附件 [el-upload drag, 演示用 auto-upload=false]
```

### 5.2 合同详情（右侧抽屉）

**抽屉规格：** size="820px"，direction="rtl"

**抽屉内部布局（自上而下）：**

```
┌─ 抽屉工具栏 ──────────────────────────────────────┐
│ [状态tag] [类型tag]   [生成并打印审批单按钮]    │
├─ 基础字段（el-descriptions :column="2" border）──┤
│ 合同编号 │ 单据类型                              │
│ 合同名称（span=2）                               │
│ 申请部门 │ 业务类型                              │
│ 客户名称 │ 乙方                                  │
│ 金额（含中文大写 digitToRMB）│ 签订日期        │
│ 创建人 │ 当前环节                                │
│ 备注（span=2）                                   │
├─ 7 级审批流转进度 ────────────────────────────────┤
│ [el-steps :active="currentStep" align-center]    │
│ 业务经办 → 业务复核 → 风控审核 → 财务经办 → ... │
├─ 合规审计日志（el-timeline）────────────────────┤
│ [审批记录 timeline item]                          │
│  - role + tag（通过/驳回）                        │
│  - 审批人 + 时间 + 意见                            │
│  - 电子签名快照 <img 44px>                        │
├─ 打印区域（@media print 时显示）─────────────────┤
│ A4 审批单样式 + 5 列签章表                       │
└────────────────────────────────────────────────────┘
```

### 5.3 审批中心 `/approval`

**布局结构：**

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─ 头部 ────────────────────────────────────────────────┐   │
│  │ 审批中心                [当前身份：业务复核 tag]       │   │
│  │                          仅显示流转到「我」的合同    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ 待审批表格 ──────────────────────────────────────────┐   │
│  │ 合同编号 │ 合同名称 │ 类型 │ 客户 │ 金额 │ 当前环节 │ 操作│
│  │ HT-001   │ ...      │ tag  │ xx   │ 50万 │ 风控审核 │ ... │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**通过/驳回弹窗：**

- 宽度：480px
- 通过时：顶部 `el-alert type="success"` 提示「通过后将自动附加您的电子签名，并流转至下一审批环节」
- 驳回时：顶部 `el-alert type="error"` 提示「驳回后合同将变为「已驳回待修改」状态，业务经办可修改后重新提交」
- 表单：`el-form-item` 包裹 `el-input type="textarea" :rows="4"`
- 驳回时 comment 必填，动态 rules
- footer 按钮颜色：成功绿渐变 / 危险红渐变

### 5.4 客户管理 `/customer`

**布局：单卡片 + 工具栏 + 表格 + dialog/drawer**

```
┌─ 工具栏 ─────────────────────────────┐
│ [搜索框: 客户名称/ID/联系人] [+新建] [刷新]
├─ 表格 ───────────────────────────────┤
│ 客户ID │ 客户名称 │ 联系人 │ 电话 │ 地址 │ 准入资料 │ 操作
│ 1      │ xxx      │ 张三  │ ...  │ ...  │ [3 个附件 tag] │ ...
└──────────────────────────────────────┘
```

**新建/编辑 dialog（560px）：**

- 客户名称（必填）
- 客户类型（select: scenic/hotel/agency/publish）
- 联系人 / 联系电话（行内 2 列）
- 地址（textarea）
- 准入资料（tag 列表 + 上传按钮，演示用）
- 备注

**查看 drawer（520px）：** el-descriptions 1 列 border

### 5.5 渠道管理 `/channel`

**布局独特：CSS Grid 卡片网格**

```
┌─ 顶部 ─────────────────────────┐
│ 多渠道数据集成            [刷新]
├─ 卡片网格（grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))）──┤
│ ┌─ 渠道卡 1 ─┐  ┌─ 渠道卡 2 ─┐  ┌─ 渠道卡 3 ─┐
│ │[logo] 名称 │  │[logo] 名称 │  │[logo] 名称 │
│ │ 描述...    │  │ 描述...    │  │ 描述...    │
│ │ 凭据区     │  │ 凭据区     │  │ 凭据区     │
│ │ [打开][回传]│  │ [打开][回传]│  │ [打开][回传]│
│ └────────────┘  └────────────┘  └────────────┘
└────────────────────────────────────┘
```

**单张渠道卡样式：**

- 顶部：logo + 名称 + 分类 tag
- 描述：灰色 13px
- 凭据区：半透明青蓝填充 `rgba(28,155,230,0.08)` + 边框 `rgba(96,150,210,0.16)`
- 底部操作按钮：打开平台（primary）/ 回传平台数据（success）

**回传数据 drawer（900px）：**

- 工具栏：导入 CSV + 填充示例数据 + 当前模式 tag + 保存
- el-alert 说明
- 可编辑表格：每列是动态生成的（CSV 列名/示例列名）
- "新增一行"按钮

### 5.6 发票管理 `/invoice`

**布局：顶部 4 个 KPI 卡 + 主表格**

```
┌─ 4 个 KPI 卡（24栅格 × 4，每 col span=6）──────────────┐
│ [发票总数 50]  [待开票 15]  [已开票 30]  [已开票金额 ¥150万]
├─ 发票列表 ──────────────────────────────────────────────┤
│ 发票抬头 │ 税号 │ 类型 │ 金额 │ 关联合同 │ 状态 │ 操作
└──────────────────────────────────────────────────────────┘
```

**KPI 卡样式：**

- 数值颜色按状态着色：白色 / 橙色 / 绿色 / 蓝色
- 仅「已开票金额」卡显示金额数字（其他显示数字）
- 卡片采用通用卡片样式

**新建/编辑 dialog（560px）：** 字段如发票抬头、税号、类型、金额、客户、关联合同、状态、日期、备注

### 5.7 经营数据 `/operation`

**布局：filter-bar + 4 KPI + 2 图表 + AI 智能大脑面板**

```
┌─ 筛选卡 ──────────────────────────────────────────┐
│ [统计周期: 本月/本季度/本年] [月份选择器] [当前：tag]
├─ 4 个 KPI 卡（24栅格 × 4，可点击跳转）────────────┤
│ [总营收]  [总成本]  [总利润]  [订单总数]   ← 顶部 3px 蓝边 + hover 上浮
├─ 2 列图表（14:10）──────────────────────────────┤
│ 左: 营收/利润趋势 (bar+line) │ 右: 业务条线营收占比 (pie)
├─ AI 智能大脑分析卡 ──────────────────────────────┤
│ [🧠 AI 智能大脑分析]              [一键诊断]
│ 总览摘要 / 4 个指标 box / 业务风险预警 / 闲置资金建议
└──────────────────────────────────────────────────┘
```

**KPI 卡特殊样式（可点击）：**

```css
cursor: pointer;
border-top: 3px solid #1c9be6;
transition: all 0.3s;

&:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(28,155,230,0.3);
  
  .stat-arrow {
    transform: translateX(3px);
  }
}
```

**AI 智能大脑卡片：** 详见 v1 demo `AiBrainPanel.vue`，业务保留

### 5.8 数据大屏 `/dashboard`

**保留 v1 demo 三栏指挥中心风格（最强烈科技风）**

```
┌─ 顶部 screen-head ────────────────────────────────────┐
│ [在线状态点 + 身份]   [CN 标题 + EN]   [时钟 + 日期 + 全屏]
├─ 左列 26% ─── 中列 flex ─── 右列 26% ──────────────────┤
│ 核心经营指标    天眼地图       7级审批跑马灯
│ 月度趋势图     物流飞线      AI雷达
│                                打字机文本
└────────────────────────────────────────────────────────┘
```

**特色：**

- 双层发光阴影（内外）
- 3D 翻入动画
- 省份点击联动
- 跑马灯滚动

---

## 六、文件组织与改造

### 6.1 新增样式文件

```
ruoyi-fastapi-frontend/src/assets/styles/
├── theme/                          # 新增：v1 demo 风格覆写
│   ├── theme-variables.scss        # CSS 变量覆写（主色、背景、文字）
│   ├── element-overrides.scss      # Element Plus 组件覆写
│   ├── layout-overrides.scss       # 侧边栏、顶栏、标签栏覆写
│   ├── components-v1.scss          # 通用组件样式（按钮、卡片、表格）
│   └── tech-blueprint.scss         # 数据大屏专用样式
└── ...
```

### 6.2 复用 v1 demo 业务页面

| 页面 | 来源（v1 demo） | 目标位置 |
|------|----------------|----------|
| 合同列表 | `1/frontend/src/views/contract/index.vue` | `ruoyi-fastapi-frontend/src/views/biz/contract/index.vue` |
| 合同详情抽屉 | `1/frontend/src/components/ContractDetailDrawer.vue` | `ruoyi-fastapi-frontend/src/views/biz/contract/components/ContractDetailDrawer.vue` |
| 审批中心 | `1/frontend/src/views/approval/index.vue` | `ruoyi-fastapi-frontend/src/views/biz/approval/index.vue` |
| 客户管理 | `1/frontend/src/views/customer/index.vue` | `ruoyi-fastapi-frontend/src/views/biz/customer/index.vue` |
| 渠道管理 | `1/frontend/src/views/channel/index.vue` | `ruoyi-fastapi-frontend/src/views/biz/channel/index.vue` |
| 发票管理 | `1/frontend/src/views/invoice/index.vue` | `ruoyi-fastapi-frontend/src/views/biz/invoice/index.vue` |
| 经营数据 | `1/frontend/src/views/operation/index.vue` | `ruoyi-fastapi-frontend/src/views/biz/operation/index.vue` |
| 数据大屏 | `1/frontend/src/views/dashboard/index.vue` | `ruoyi-fastapi-frontend/src/views/dashboard/index.vue` |
| 首页（看板） | `1/frontend/src/views/dashboard/index.vue`（非 screen 部分） | `ruoyi-fastapi-frontend/src/views/index.vue` |
| AI 智能大脑 | `1/frontend/src/components/AiBrainPanel.vue` | `ruoyi-fastapi-frontend/src/components/AiBrainPanel.vue` |
| BaseChart | `1/frontend/src/components/BaseChart.vue` | `ruoyi-fastapi-frontend/src/components/BaseChart.vue` |

### 6.3 改造要点

**从 v1 demo 迁移到 RuoYi 框架时的改动：**

1. **替换数据源**：v1 demo 是本地 mock 数据，RuoYi 中替换为真实 API 调用（详见 API 设计文档）
2. **集成 RuoYi 权限**：使用 RuoYi 的 `useUserStore` 和 `usePermission` 替换 v1 demo 简单的角色判断
3. **路由配置**：在 RuoYi 的路由文件中注册业务路由
4. **登录集成**：使用 RuoYi 的 `/login` API 和 token 管理
5. **替换演示元素**：
   - 演示用固定账号密码 → 真实登录
   - emoji logo → 真实 Logo 图片
   - "演示区域，不会真实上传" → 真实上传
   - 示例 CSV 数据 → 真实业务数据

---

## 七、验收清单

### 7.1 全局视觉

- [ ] 主色 `#1c9be6` + 青色 `#22d3ee` 正确应用
- [ ] 主背景径向渐变 + 双光晕正确渲染
- [ ] 侧边栏 220px 深蓝渐变正常
- [ ] 顶栏 60px 蓝渐变正常
- [ ] 滚动条样式为渐变蓝青色
- [ ] 字体颜色层级清晰

### 7.2 组件样式

- [ ] 主按钮蓝青渐变 + 发光阴影
- [ ] 卡片玻璃霓虹质感 + 顶部装饰线
- [ ] 表格表头渐变深蓝 + 蓝色 hover
- [ ] 输入框深色背景 + 蓝色聚焦
- [ ] 弹窗/抽屉深色毛玻璃背景

### 7.3 业务页面

- [ ] 合同管理：列表 + 新建/编辑弹窗
- [ ] 合同详情：右侧抽屉 + 7-step 进度 + 时间轴 + 打印审批单
- [ ] 审批中心：待审批列表 + 通过/驳回弹窗
- [ ] 客户管理：列表 + 新建/编辑/查看
- [ ] 渠道管理：CSS Grid 卡片网格 + 回传数据抽屉
- [ ] 发票管理：4 KPI 卡 + 列表
- [ ] 经营数据：4 KPI 卡 + 2 图表 + AI 智能大脑
- [ ] 数据大屏：三栏指挥中心风

### 7.4 交互细节

- [ ] 卡片 hover 上浮 + 增强阴影
- [ ] KPI 卡 hover 上浮 + 箭头移动
- [ ] 表格行 hover 蓝色高亮
- [ ] 按钮 hover 渐变方向反转
- [ ] 弹窗/抽屉 backdrop-filter 毛玻璃

---

## 八、参考文档

| 文档 | 关联内容 |
|------|----------|
| `API设计文档.md` | 业务页面数据来源 |
| `权限模型设计.md` | 角色/按钮权限 |
| `RuoYi重构方案.md` | 前端技术选型 |
| `v1现状盘点.md` | v1 demo 视觉参考（本文档主要依据） |

---

*文档结束*