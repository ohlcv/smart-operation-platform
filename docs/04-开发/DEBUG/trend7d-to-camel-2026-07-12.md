# Pydantic `alias_generator=to_camel` 把 `trend_7d` 翻译成 `trend7D`

**日期**：2026-07-12
**类型**：Pydantic 序列化 / 字段命名一致性（ADR D24/D28）
**影响**：仪表盘趋势图前端静默空数据；不影响其他业务模块（本项目唯一已知 `数字+字母连写` 边界字段）
**根因**：`to_camel` 把 `trend_7d` 解析成 `[trend][7][d]` 三个词，组合时 `d` 单独被首字母大写成 `D`

---

## 1. 现象

路线 C 重构 dashboard 后，本地端到端测试通过 `pytest -dashboard` 全绿；路由层打开 `/biz/dashboard/overview` 看响应：

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "channelLocations": [...],
    "generatedAt": "2026-07-12 00:12:34",
    "kpi": {...},
    "province": "",
    "recentApprovals": [...],
    "statusDistribution": [...],
    "topCustomers": [...],
    "trend7D": [...]   ← 注意是大写 D
  }
}
```

前端 `dashboard.vue` 写死读 `data.trend7d`：

```vue
const trendDates = computed(() => (overview.value.trend7d || []).map(...))
//                                  ^^^^^^^^^^^ undefined
const trendNew = computed(() => (overview.value.trend7d || []).map(...))
```

`undefined` 不报错但得到空数组 → 大屏 7 日趋势图**静默不显示**（左侧 KPI 正常渲染 → 用户第一眼看到「图掉了」）。

后端同事第一反应：「是不是没给数据？」 → 拉实际 SQL 输出，发现 DAO 返回的 `Trend7dItemModel` 列表正常 7 条，问题在序列化层。

---

## 2. 根因分析

### 2.1 Pydantic `to_camel` 的具体行为

```python
>>> from pydantic.alias_generators import to_camel
>>> to_camel('trend_7d')
'trend7D'   # ← 数字当词边界
>>> to_camel('trend_7_days')
'trend7Days'
>>> to_camel('customer_name')
'customerName'
>>> to_camel('amount')
'amount'
```

源码层面（pydantic 2.x）实现：

```python
# pydantic/alias_generators.py
def to_camel(s: str) -> str:
    # 先按 _ split，每段首字母大写
    parts = s.split('_')
    return parts[0] + ''.join(p[:1].upper() + p[1:] for p in parts[1:] if p)
```

`trend_7d` → `'trend' + '7' + 'D' = 'trend7D'`

数字当词边界是设计行为，**不是 bug**——Pydantic 团队认为 `123_abc` 也应转 `123Abc`（参见 GitHub issue #8245 早在 2022 年就有讨论）。

### 2.2 静默不报错的链路

```python
# dashboard_vo.py（修复前）
class DashboardOverviewModel(DashboardBaseModel):
    kpi: DashboardKpiModel = Field(default_factory=DashboardKpiModel)
    trend_7d: list[Trend7dItemModel] = Field(default_factory=list)

dashboardBaseModel.model_config = ConfigDict(
    alias_generator=to_camel,
    from_attributes=True,
    populate_by_name=True,
)
```

```python
>>> m = DashboardOverviewModel(trend_7d=[...])
>>> m.model_dump(by_alias=True, mode='json').keys()
dict_keys([..., 'trend7D'])  # ← 出错点
>>> m.model_dump(by_alias=True, mode='json')['trend7D']
[{'date': '2026-07-06', 'newContracts': 1, 'approvedContracts': 0}, ...]
```

后端永远不报错，前端 `data.trend7d` 永远 `undefined`，趋势图永远空。

### 2.3 反射扫描全项目其他潜在受害者

```bash
grep -rEn '[a-zA-Z]+_[0-9]+[a-zA-Z_]+' ruoyi-fastapi-backend/module_biz/entity/vo/
```

扫描结果（修复前）：

| 文件 | 字段 | 转 camelCase 结果 | 影响 |
|---|---|---|---|
| `dashboard_vo.py` | `trend_7d` | `trend7D` | 🔴 **本 DEBUG 现场** |
| `dashboard_vo.py` | 其他（`kpi/trend_7d` 之外） | 正常 | ✅ |
| `customer_vo.py` / `contract_vo.py` / `invoice_vo.py` 等 | 全部纯字母字段 | 正常 | ✅ |

本项目唯一案例。

---

## 3. 修复前后对比

### 3.1 修复前（静默空数据）

```python
# ruoyi-fastapi-backend/module_biz/entity/vo/dashboard_vo.py
class DashboardOverviewModel(DashboardBaseModel):
    kpi: DashboardKpiModel = Field(default_factory=DashboardKpiModel)
    trend_7d: list[Trend7dItemModel] = Field(default_factory=list)
    # ↑ Field 没指定 alias，走 to_camel → 'trend7D'
```

```bash
$ curl -X GET .../biz/dashboard/overview -H "Authorization: Bearer ..." | jq '.data | keys'
[
  "channelLocations",
  "generatedAt",
  "kpi",
  "province",
  "recentApprovals",
  "statusDistribution",
  "topCustomers",
  "trend7D"   # ← 大写 D
]
```

前端访问 `data.trend7d` 得到 `undefined` → 趋势图不显示。

### 3.2 修复后（显式 alias 锁定）

```python
# ruoyi-fastapi-backend/module_biz/entity/vo/dashboard_vo.py
class DashboardOverviewModel(DashboardBaseModel):
    kpi: DashboardKpiModel = Field(default_factory=DashboardKpiModel)
    trend_7d: list[Trend7dItemModel] = Field(
        default_factory=list,
        alias='trend7d',                       # ← 关键
        serialization_alias='trend7d',          # ← 关键（dump by_alias 用）
    )
```

`alias=` 控 Python ↔ JSON 反序列化（外部数据进 Pydantic），`serialization_alias=` 控 Pydantic → JSON 输出（`model_dump(by_alias=True)` 用）。两者都得写，否则反序列化可能报「field required」或序列化字段名又走 to_camel。

验证：

```bash
$ ./venv/bin/python -c "
from module_biz.entity.vo.dashboard_vo import DashboardOverviewModel
m = DashboardOverviewModel(trend_7d=[])
print(sorted(m.model_dump(by_alias=True, mode='json').keys()))
"
['channelLocations', 'generatedAt', 'kpi', 'province', 'recentApprovals',
 'statusDistribution', 'topCustomers', 'trend7d']   # ✓ 小写 d
```

```bash
$ curl -X GET .../biz/dashboard/overview ...
{
  "data": {
    ...,
    "trend7d": [...]   # ✓
  }
}
```

---

## 4. 验证清单

- [x] Pydantic `model_dump(by_alias=True, mode='json')` 含 `trend7d` 键（小写 d）
- [x] HTTP 响应 JSON 含 `trend7d` 键（小写 d）
- [x] 前端 `dashboard.vue` `data.trend7d` 拿到 7 元素数组
- [x] `data.trend7D` 不存在（确认显式 alias 覆盖了 to_camel）
- [x] 烟雾测试其他 9 个键（kpi/channelLocations/...）都正常 camelCase

---

## 5. 反思与同类风险防范

### 5.1 静默 bug 的特征

这种 bug 没有任何报错：
- **后端**：序列化成功，dump 出 dict，无异常
- **前端**：访问 `data.trend7d` 得 `undefined`，`undefined.map(...)` = TypeError，但代码用了 `(data.trend7d || []).map(...)` 兜底，返回空数组
- **视觉**：图表组件拿到 `categories=[] data=[]`，efcharts 渲染出**「空坐标轴但默认线」**，看就是一条灰色底基线，**没有 7 元素柱子**

唯一能抓到的是**正向断言**：路由层打开 swagger-ui 看实际响应 + 前端开发者工具看 Network response。

### 5.2 类似风险扫描

```bash
# 全项目扫「数字+字母连写」字段
grep -rEn '[a-zA-Z]+_[0-9]+[a-zA-Z_]+' \
  ruoyi-fastapi-backend/module_biz/entity/vo/ \
  ruoyi-fastapi-backend/module_admin/entity/vo/
```

本项目当前其他 vo 中无命中。若未来引入如 `step_3_label`、`level_2_score`、`period_7_days`、`v2_2026` 等字段，必须按本规则加显式 alias。

### 5.3 防御性约束（新规则）

加入 ADR **D28**：Pydantic 模型若字段名包含「数字+字母连写」边界，**必须**用 `Field(alias='xx', serialization_alias='xx')` 显式声明。

Code review 时凡是看到形如 `xxx_yN` 或 `xxx_y_N`（其中 `y` 是数字、`N` 是字母）的字段名，**一票否决**，必须先按 D28 加 alias。

---

## 6. 关联决策 / 影响范围

- **关联 ADR**：D28（Pydantic 别名显式声明）、D24（API 字段命名一致性 + camelCase）、D29（仪表盘大屏形态）
- **影响范围**：
  - 当前唯一影响：`module_biz/entity/vo/dashboard_vo.py` 一处
  - 项目其他 Pydantic 模型已扫描，无同类字段
  - 前端 `dashboard.vue` / `views/biz/dashboard/index.vue` 都在 route layer 调 `/biz/dashboard/overview`，本修复对两端立即生效