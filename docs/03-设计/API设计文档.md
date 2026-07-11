# API 设计文档

> 文档版本：v1.1  
> 创建日期：2026-07-10  
> 文档目的：定义系统前后端 API 接口规范，作为前后端联调和对齐的依据  
> 设计原则：沿用 RuoYi-FastAPI 原生 API 规范，业务模块采用相同风格

---

## 一、API 设计规范

### 1.1 技术规范

| 维度 | 规范 | 说明 |
|------|------|------|
| **基础协议** | HTTPS | 全站强制 HTTPS |
| **接口前缀** | `/prod-api` 或 `/dev-api` | 按环境区分，Nginx 统一出口 |
| **版本控制** | URL 路径版本 | 如 `/prod-api/v1/...`，v1 期暂不加版本号 |
| **字符编码** | UTF-8 | 所有请求和响应 |
| **内容类型** | `application/json` | 请求和响应均为 JSON |

### 1.2 响应格式

RuoYi 统一响应包装，格式如下：

**成功响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": { ... },
  "success": true,
  "time": "2026-07-10 21:44:00"
}
```

**分页响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "rows": [ ... ],
  "pageNum": 1,
  "pageSize": 10,
  "total": 100,
  "hasNext": true,
  "success": true,
  "time": "2026-07-10 21:44:00"
}
```

**异常响应：**

```json
{
  "code": 401,
  "msg": "登录已过期，请重新登录",
  "data": null,
  "success": false,
  "time": "2026-07-10 21:44:00"
}
```

### 1.3 响应状态码

| 状态码 | 含义 | 典型场景 |
|--------|------|----------|
| `200` | 成功 | 正常业务处理 |
| `201` | 已创建 | POST 创建成功 |
| `204` | 无内容 | DELETE 成功（Body 为空） |
| `400` | 请求参数错误 | 参数校验失败、缺少必填字段 |
| `401` | 未认证 | Token 过期、无效、未登录 |
| `403` | 无权限 | 按钮级权限校验失败 |
| `404` | 资源不存在 | 查询 ID 不存在 |
| `409` | 业务冲突 | 合同编号重复、状态不允许操作 |
| `500` | 服务器错误 | 未捕获的异常 |

### 1.4 字段命名

| 层级 | 命名规范 | 示例 |
|------|----------|------|
| URL 路径 | kebab-case | `/system-user`, `/biz-contract` |
| JSON 请求/响应 | **camelCase** | `contractNo`, `currentStep`, `partyA` |
| 数据库字段 | snake_case | `contract_no`, `current_step`, `party_a` |

> **驼峰化**：后端统一使用 Pydantic `alias_generator=to_camel`，Python 用蛇形命名，JSON 用驼峰命名。
> 保留 `populate_by_name=True`，可同时接受 snake_case 输入（兼容老客户端）。

> **强约束（ADR D24）**：全站 `module_admin` 与 `module_biz` 必须一致使用 camelCase，禁止混用 snake_case。
> 任何新模块必须继承统一基类或显式配置 `alias_generator=to_camel`。

### 1.5 HTTP 方法使用规范

| 方法 | 用途 | 幂等性 |
|------|------|--------|
| `GET` | 查询资源（无副作用） | ✅ 幂等 |
| `POST` | 创建资源 | ❌ 非幂等 |
| `PUT` | 更新完整资源 | ✅ 幂等 |
| `DELETE` | 删除资源 | ✅ 幂等 |

### 1.6 路径变量与查询参数

| 场景 | 使用方式 | 示例 |
|------|----------|------|
| 单个资源 ID | 路径变量 `{id}` | `GET /biz/contract/123` |
| 批量删除 | 路径变量，逗号分隔 `{ids}` | `DELETE /biz/contract/1,2,3` |
| 分页查询 | Query 参数 | `GET /biz/contract/list?pageNum=1&pageSize=10` |
| 条件过滤 | Query 参数 | `GET /biz/contract/list?status=pending&currentStep=3` |
| 时间范围 | Query 参数 | `GET /biz/contract/list?beginTime=2026-01-01&endTime=2026-12-31` |

---

## 二、接口分组

系统 API 按模块分组，与 RuoYi 保持一致：

| 模块前缀 | 模块名称 | 说明 |
|----------|----------|------|
| `/login` | 登录认证 | 登录、登出、验证码 |
| `/user` | 用户相关 | 获取当前用户信息 |
| `/system` | 系统管理 | 用户、角色、菜单、部门、字典、参数、公告 |
| `/biz` | 核心业务 | 合同、审批、客户、渠道、发票、财务、经营数据 |
| `/monitor` | 系统监控 | 日志、操作记录（沿用 RuoYi） |
| `/common` | 通用功能 | 文件上传、下载 |

---

## 三、登录认证模块

### 3.1 登录

```
POST /login
```

**请求体：**

```json
{
  "username": "admin",
  "password": "123456",
  "code": "1234",
  "uuid": "xxx-xxx-xxx"
}
```

**成功响应：**

```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userInfo": {
      "userId": 1,
      "userName": "admin",
      "nickName": "系统管理员",
      "avatar": "",
      "deptId": 100,
      "deptName": "信息中心",
      "signature": "data:image/svg+xml;base64,..."
    },
    "roles": ["admin"],
    "permissions": ["*:*:*"]
  },
  "success": true,
  "time": "2026-07-10 21:44:00"
}
```

> **说明**：`permissions` 数组中包含用户拥有的所有 `perms` 权限字符串，`*:*:*` 表示超管。前端路由守卫基于此数组做按钮级权限控制。

### 3.2 获取当前用户信息

```
GET /getInfo
```

**请求头：**

```
Authorization: Bearer {token}
```

**成功响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "user": {
      "userId": 1,
      "userName": "admin",
      "nickName": "系统管理员",
      "deptId": 100,
      "deptName": "信息中心",
      "signature": "data:image/svg+xml;base64,..."
    },
    "roles": ["admin"],
    "permissions": ["*:*:*"]
  },
  "success": true
}
```

### 3.3 登出

```
POST /logout
```

**成功响应：**

```json
{
  "code": 200,
  "msg": "退出成功",
  "success": true
}
```

---

## 四、系统管理模块

> 沿用 RuoYi 原生接口，本文档不重复定义。核心接口清单：

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 用户分页列表 | GET | `/system/user/list` | 分页、条件过滤 |
| 用户详情 | GET | `/system/user/{userId}` | 获取单个用户 |
| 新增用户 | POST | `/system/user` | 创建用户 |
| 编辑用户 | PUT | `/system/user` | 更新用户 |
| 删除用户 | DELETE | `/system/user/{userIds}` | 批量删除 |
| 重置密码 | PUT | `/system/user/resetPwd` | 超管重置 |
| 角色分页列表 | GET | `/system/role/list` | |
| 新增角色 | POST | `/system/role` | |
| 编辑角色 | PUT | `/system/role` | |
| 删除角色 | DELETE | `/system/role/{roleIds}` | |
| 菜单列表 | GET | `/system/menu/list` | |
| 角色菜单授权 | GET | `/system/menu/roleMenuTreeselect/{roleId}` | 获取角色已有菜单树 |
| 提交菜单授权 | PUT | `/system/menu` | 更新角色菜单 |
| 部门树 | GET | `/system/dept/treeselect` | 树形结构 |
| 字典类型列表 | GET | `/system/dict/type/list` | |
| 字典数据列表 | GET | `/system/dict/data/list` | |
| 通知公告列表 | GET | `/system/notice/list` | |
| 登录日志列表 | GET | `/monitor/logininfor/list` | |
| 操作日志列表 | GET | `/monitor/operlog/list` | |

---

## 五、合同管理模块

### 5.1 合同列表

```
GET /biz/contract/list
```

**权限标识：** `contract:list`（业务经办只查本人，审批角色可查全部，超管可查全部）

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pageNum` | int | 否，默认 1 | 页码 |
| `pageSize` | int | 否，默认 10 | 每页条数 |
| `contractNo` | string | 否 | 合同编号（模糊搜索） |
| `title` | string | 否 | 合同名称（模糊搜索） |
| `contractType` | string | 否 | 合同类型：`payment` / `business` |
| `status` | string | 否 | 状态：`draft` / `pending` / `approved` / `rejected` |
| `currentStep` | int | 否 | 当前审批步骤（0-6） |
| `beginTime` | string | 否 | 创建开始时间（格式：`YYYY-MM-DD`） |
| `endTime` | string | 否 | 创建结束时间 |

**成功响应（分页）：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "rows": [
    {
      "id": 1,
      "contractNo": "HT-2026-001",
      "title": "景区门票采购合同",
      "contractType": "payment",
      "contractTypeLabel": "业务付款审批单",
      "partyA": "济南新华书店",
      "partyB": "山东出版供应链管理公司",
      "amount": 500000.00,
      "status": "pending",
      "statusLabel": "审批中",
      "currentStep": 2,
      "currentStepLabel": "风控审核",
      "rejectCount": 0,
      "createdBy": 2,
      "createdByName": "张经办",
      "createTime": "2026-07-01 10:00:00"
    }
  ],
  "pageNum": 1,
  "pageSize": 10,
  "total": 50,
  "hasNext": true,
  "success": true
}
```

### 5.2 我的合同（业务经办视角）

```
GET /biz/contract/my-list
```

**权限标识：** `contract:list`

**说明**：返回当前用户创建的合同列表（`createdBy = 当前用户`），不受数据范围限制筛选。

**Query 参数：** 同 5.1 合同列表

### 5.3 合同详情

```
GET /biz/contract/{id}
```

**权限标识：** `contract:list`

**成功响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 1,
    "contractNo": "HT-2026-001",
    "title": "景区门票采购合同",
    "contractType": "payment",
    "contractTypeLabel": "业务付款审批单",
    "partyA": "济南新华书店",
    "partyB": "山东出版供应链管理公司",
    "amount": 500000.00,
    "amountInWords": "伍拾万元整",
    "signDate": "2026-06-28",
    "department": "业务部",
    "businessType": "景区门票",
    "customerId": 1,
    "customerName": "济南新华书店",
    "remark": "备注信息",
    "attachments": [
      {"name": "合同附件.pdf", "url": "/uploads/xxx.pdf"}
    ],
    "status": "pending",
    "statusLabel": "审批中",
    "currentStep": 2,
    "currentStepLabel": "风控审核",
    "rejectCount": 1,
    "createdBy": 2,
    "createdByName": "张经办",
    "createTime": "2026-07-01 10:00:00",
    "updateTime": "2026-07-02 14:30:00"
  },
  "success": true
}
```

### 5.4 新建合同

```
POST /biz/contract
```

**权限标识：** `contract:add`

**请求体：**

```json
{
  "contractNo": "HT-2026-002",
  "title": "数字出版合作协议",
  "contractType": "business",
  "partyA": "青岛出版发行集团",
  "partyB": "山东出版供应链管理公司",
  "amount": 300000.00,
  "signDate": "2026-07-15",
  "department": "数字业务部",
  "businessType": "数字出版",
  "customerId": 2,
  "remark": "合作期限两年",
  "attachments": [
    {"name": "合作协议.pdf", "url": "/uploads/yyy.pdf"}
  ]
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `contractNo` | string | ✅ | 合同编号（手动输入，当前阶段不自动生成） |
| `title` | string | ✅ | 合同名称，最大 200 字 |
| `contractType` | string | ✅ | `payment`=业务付款审批单 / `business`=业务审批单 |
| `partyA` | string | ✅ | 甲方（客户）名称 |
| `partyB` | string | ✅ | 乙方（本司）名称 |
| `amount` | decimal | ✅ | 合同金额，最小 0 |
| `signDate` | date | 否 | 签订日期 |
| `department` | string | 否 | 申请部门 |
| `businessType` | string | 否 | 业务类型 |
| `customerId` | int | 否 | 关联客户 ID |
| `remark` | string | 否 | 备注 |
| `attachments` | array | 否 | 附件列表 |

**成功响应：**

```json
{
  "code": 200,
  "msg": "新增成功",
  "data": { "id": 2 },
  "success": true
}
```

### 5.5 编辑合同

```
PUT /biz/contract
```

**权限标识：** `contract:edit`

**前置条件：**

- `status` 必须为 `draft`（草稿）或 `rejected`（已驳回待修改）
- `createdBy` 必须为当前用户
- 审批中（`pending`）和已通过（`approved`）不可编辑

**请求体：** 同 5.4 新建合同，可只传需要修改的字段

**成功响应：**

```json
{
  "code": 200,
  "msg": "修改成功",
  "success": true
}
```

### 5.6 删除合同

```
DELETE /biz/contract/{ids}
```

**权限标识：** `contract:delete`

**前置条件：**

- `status` 必须为 `draft`（草稿）或 `rejected`（已驳回待修改）
- `createdBy` 必须为当前用户

**路径参数：**

| 参数 | 说明 |
|------|------|
| `ids` | 合同 ID，多个用逗号分隔，如 `1,2,3` |

**成功响应：**

```json
{
  "code": 200,
  "msg": "删除成功",
  "success": true
}
```

### 5.7 提交审批

```
POST /biz/contract/submit/{id}
```

**权限标识：** `contract:submit`

**前置条件：**

- `status` 必须为 `draft`（草稿）或 `rejected`（已驳回待修改）
- `createdBy` 必须为当前用户

**业务逻辑：**

1. 校验合同信息完整性（必填字段不能为空）
2. 将 `status` 变为 `pending`
3. 将 `current_step` 置为 0（Step 0 自动完成）
4. 创建 `biz_approval` 记录（Step 0 自动审批，含电子签名快照）

**成功响应：**

```json
{
  "code": 200,
  "msg": "提交审批成功",
  "data": {
    "status": "pending",
    "currentStep": 0
  },
  "success": true
}
```

### 5.8 合同编号唯一性校验

```
GET /biz/contract/check-no
```

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `contractNo` | string | ✅ | 待校验的合同编号 |

**成功响应（编号不存在时）：**

```json
{
  "code": 200,
  "msg": "编号可用",
  "data": true,
  "success": true
}
```

**编号已存在时：**

```json
{
  "code": 200,
  "msg": "编号已存在",
  "data": false,
  "success": true
}
```

---

## 六、审批中心模块

### 6.1 待我审批列表

```
GET /biz/approval/pending-list
```

**权限标识：** `approval:list`

**说明**：返回当前用户待审批的合同列表。

- **超管（`admin`）**：返回全部 `status=pending` 的合同
- **普通审批角色**：返回 `current_step + 1 = 用户.role.role_sort` 且 `status=pending` 的合同

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pageNum` | int | 否 | 页码 |
| `pageSize` | int | 否 | 每页条数 |
| `contractNo` | string | 否 | 合同编号（模糊） |
| `title` | string | 否 | 合同名称（模糊） |
| `beginTime` | string | 否 | 创建开始时间 |
| `endTime` | string | 否 | 创建结束时间 |

**成功响应（分页）：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "rows": [
    {
      "id": 3,
      "contractNo": "HT-2026-001",
      "title": "景区门票采购合同",
      "contractType": "payment",
      "amount": 500000.00,
      "currentStep": 2,
      "currentStepLabel": "风控审核",
      "rejectCount": 0,
      "createdByName": "张经办",
      "createTime": "2026-07-01 10:00:00"
    }
  ],
  "pageNum": 1,
  "pageSize": 10,
  "total": 5,
  "hasNext": false,
  "success": true
}
```

### 6.2 审批通过

```
POST /biz/approval/approve/{contractId}
```

**权限标识：** `approval:approve`

**后端双重校验：**

1. 接口级：`UserInterfaceAuthDependency('approval:approve')` 校验按钮权限
2. 业务级：`ApprovalService.can_approve_contract()` 校验 `current_step + 1 == 用户.role.role_sort`（超管跳过）

**前置条件：**

- 合同 `status` 必须为 `pending`
- 当前用户必须是对应 step 的审批人（或超管）

**请求体：**

```json
{
  "comment": "审核通过，同意执行"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `comment` | string | 否 | 审批意见（通过时可选） |

**业务逻辑：**

1. 权限校验（`can_approve_contract`）
2. 判断是否为最后一步（`current_step == 6`）
   - 是：合同状态变为 `approved`，流程结束
   - 否：`current_step += 1`，继续流转
3. 创建 `biz_approval` 记录（`action=approve`，含电子签名快照）

**成功响应：**

```json
{
  "code": 200,
  "msg": "审批通过",
  "data": {
    "status": "pending",
    "currentStep": 3,
    "currentStepLabel": "财务经办"
  },
  "success": true
}
```

**最后一步通过时：**

```json
{
  "code": 200,
  "msg": "审批通过，流程结束",
  "data": {
    "status": "approved",
    "currentStep": 6,
    "currentStepLabel": "已通过"
  },
  "success": true
}
```

### 6.3 审批驳回

```
POST /biz/approval/reject/{contractId}
```

**权限标识：** `approval:reject`

**前置条件：** 同 6.2 审批通过

**请求体：**

```json
{
  "comment": "风控评估未完成，请补充风险控制方案"
}
```

> **驳回时 `comment` 为必填**，不传或空字符串返回 400 错误。

**业务逻辑：**

1. 校验 `comment` 非空
2. 权限校验
3. 合同 `status` 变为 `rejected`（**不是终止态，可重新提交**）
4. `current_step` 保持不变
5. `reject_count += 1`
6. 创建 `biz_approval` 记录（`action=reject`，含电子签名快照）

**成功响应：**

```json
{
  "code": 200,
  "msg": "驳回成功",
  "data": {
    "status": "rejected",
    "rejectCount": 1
  },
  "success": true
}
```

### 6.4 审批历史（时间轴）

```
GET /biz/approval/history/{contractId}
```

**权限标识：** `approval:list`

**说明**：返回合同的全量审批历史记录，按时间倒序（最新的在前）。

**成功响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": [
    {
      "id": 5,
      "step": 2,
      "stepLabel": "风控审核",
      "approverId": 4,
      "approverName": "王风控",
      "approverRole": "risk_auditor",
      "action": "approve",
      "actionLabel": "通过",
      "comment": "审核通过，同意执行",
      "signatureSnapshot": "data:image/svg+xml;base64,...",
      "approvalTime": "2026-07-03 15:30:00"
    },
    {
      "id": 4,
      "step": 1,
      "stepLabel": "业务复核",
      "approverId": 3,
      "approverName": "李复核",
      "approverRole": "business_reviewer",
      "action": "approve",
      "actionLabel": "通过",
      "comment": "复核无误",
      "signatureSnapshot": "data:image/svg+xml;base64,...",
      "approvalTime": "2026-07-02 11:00:00"
    },
    {
      "id": 3,
      "step": 0,
      "stepLabel": "业务经办（提交）",
      "approverId": 2,
      "approverName": "张经办",
      "approverRole": "business_handler",
      "action": "approve",
      "actionLabel": "通过",
      "comment": null,
      "signatureSnapshot": "data:image/svg+xml;base64,...",
      "approvalTime": "2026-07-01 10:05:00"
    }
  ],
  "success": true
}
```

---

## 七、客户管理模块

### 7.1 客户列表

```
GET /biz/customer/list
```

**权限标识：** `customer:list`

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pageNum` | int | 否 | 页码 |
| `pageSize` | int | 否 | 每页条数 |
| `customerName` | string | 否 | 客户名称（模糊） |
| `customerType` | string | 否 | 客户类型：`scenic` / `hotel` / `agency` / `publish` |
| `level` | string | 否 | 客户等级：`A` / `B` / `C` |

### 7.2 客户详情

```
GET /biz/customer/{id}
```

**权限标识：** `customer:list`

### 7.3 新建客户

```
POST /biz/customer
```

**权限标识：** `customer:add`

**请求体：**

```json
{
  "customerName": "齐鲁印刷厂",
  "customerType": "publish",
  "contactName": "张经理",
  "contactPhone": "0531-88888888",
  "contactEmail": "zzz@qilu.com",
  "address": "济南市历下区文化东路",
  "businessLicense": "91370100MA3xxxxxx",
  "taxNo": "91370100MA3xxxxxx",
  "level": "A",
  "tags": ["出版社", "长期合作"],
  "remark": "优质客户"
}
```

### 7.4 编辑客户

```
PUT /biz/customer
```

**权限标识：** `customer:edit`

### 7.5 删除客户

```
DELETE /biz/customer/{ids}
```

**权限标识：** `customer:delete`

---

## 八、渠道管理模块

### 8.1 渠道列表

```
GET /biz/channel/list
```

**权限标识：** `channel:list`

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pageNum` | int | 否 | 页码 |
| `pageSize` | int | 否 | 每页条数 |
| `channelName` | string | 否 | 渠道名称（模糊） |
| `channelType` | string | 否 | 渠道类型：`meituan` / `douyin` / `ctrip` / `tongcheng` |
| `status` | string | 否 | 状态：`active` / `inactive` / `suspended` |

### 8.2 新建渠道

```
POST /biz/channel
```

**权限标识：** `channel:add`

**请求体：**

```json
{
  "channelName": "美团到综济南站",
  "channelType": "meituan",
  "account": "meituan_jinan",
  "password": "******",
  "apiKey": "******",
  "apiSecret": "******",
  "remark": "2026年新签约渠道"
}
```

> 密钥字段后端加密存储，前端显示 `******`。

### 8.3 编辑渠道

```
PUT /biz/channel
```

**权限标识：** `channel:edit`

### 8.4 删除渠道

```
DELETE /biz/channel/{ids}
```

**权限标识：** `channel:delete`

### 8.5 导入回传数据

```
POST /biz/channel/import
```

**权限标识：** `channel:import`

**Content-Type：** `multipart/form-data`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `channelId` | int | ✅ | 渠道 ID |
| `file` | file | ✅ | CSV 文件 |

**成功响应：**

```json
{
  "code": 200,
  "msg": "导入成功，共导入 120 条记录",
  "data": {
    "total": 120,
    "success": 118,
    "failed": 2
  },
  "success": true
}
```

---

## 九、发票管理模块

### 9.1 发票列表

```
GET /biz/invoice/list
```

**权限标识：** `invoice:list`

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pageNum` | int | 否 | 页码 |
| `pageSize` | int | 否 | 每页条数 |
| `invoiceNo` | string | 否 | 发票号（精确） |
| `invoiceType` | string | 否 | 发票类型：`special` / `normal` |
| `status` | string | 否 | 状态：`pending` / `issued` / `void` |
| `beginTime` | string | 否 | 创建开始时间 |
| `endTime` | string | 否 | 创建结束时间 |

### 9.2 新建发票

```
POST /biz/invoice
```

**权限标识：** `invoice:add`

**请求体：**

```json
{
  "invoiceNo": "FP20260710001",
  "invoiceType": "normal",
  "title": "山东出版供应链管理公司",
  "taxNo": "91370100MA3xxxxxx",
  "amount": 50000.00,
  "taxAmount": 4500.00,
  "taxRate": 9,
  "contractId": 1,
  "customerName": "济南新华书店",
  "remark": "景区门票第一批开票"
}
```

### 9.3 编辑发票

```
PUT /biz/invoice
```

**权限标识：** `invoice:edit`

### 9.4 确认开票

```
PUT /biz/invoice/issue/{id}
```

**权限标识：** `invoice:confirm`

**业务逻辑：** 将 `status` 变为 `issued`，自动填入 `issued_date` 为当天日期。

**成功响应：**

```json
{
  "code": 200,
  "msg": "开票成功",
  "data": {
    "status": "issued",
    "issuedDate": "2026-07-10"
  },
  "success": true
}
```

### 9.5 作废发票

```
PUT /biz/invoice/void/{id}
```

**权限标识：** `invoice:void`

**请求体：**

```json
{
  "voidReason": "发票开具错误，需要重新开具"
}
```

### 9.6 发票统计

```
GET /biz/invoice/stats
```

**权限标识：** `invoice:list`

**成功响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "total": 50,
    "pending": 15,
    "issued": 30,
    "void": 5,
    "issuedAmount": 1500000.00,
    "pendingAmount": 500000.00
  },
  "success": true
}
```

---

## 十、经营数据模块

### 10.1 经营数据列表

```
GET /biz/operation/list
```

**权限标识：** `operation:list`

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pageNum` | int | 否 | 页码 |
| `pageSize` | int | 否 | 每页条数 |
| `year` | int | 否 | 年份 |
| `month` | int | 否 | 月份（1-12） |
| `businessLine` | string | 否 | 业务线：`scenic` / `digital` / `logistics` |

### 10.2 录入经营数据

```
POST /biz/operation
```

**权限标识：** `operation:add`

**请求体：**

```json
{
  "year": 2026,
  "month": 7,
  "businessLine": "scenic",
  "revenue": 120.50,
  "cost": 80.20,
  "profit": 40.30,
  "orderCount": 350,
  "customerCount": 15,
  "remark": "7月暑期旺季"
}
```

### 10.3 编辑经营数据

```
PUT /biz/operation
```

**权限标识：** `operation:edit`

### 10.4 删除经营数据

```
DELETE /biz/operation/{ids}
```

**权限标识：** `operation:delete`

### 10.5 经营看板聚合

```
GET /biz/operation/kpi
```

**权限标识：** `operation:list`

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `year` | int | 否 | 年份，默认当前年 |
| `month` | int | 否 | 月份，默认当前月 |
| `period` | string | 否 | 周期：`month` / `quarter` / `year`，与 year/month 联动 |

**成功响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "currentPeriod": {
      "revenue": 350.50,
      "revenueGrowth": 12.5,
      "cost": 220.30,
      "costGrowth": 8.2,
      "profit": 130.20,
      "profitGrowth": 18.3,
      "orderCount": 980,
      "orderGrowth": 15.0,
      "customerCount": 42
    },
    "byBusinessLine": [
      {"businessLine": "scenic", "businessLineLabel": "景区发行", "revenue": 180.50, "profit": 75.20},
      {"businessLine": "digital", "businessLineLabel": "数字出版", "revenue": 120.00, "profit": 45.00},
      {"businessLine": "logistics", "businessLineLabel": "物流仓储", "revenue": 50.00, "profit": 10.00}
    ],
    "trendData": [
      {"month": "2026-01", "revenue": 280.00, "profit": 95.00},
      {"month": "2026-02", "revenue": 310.00, "profit": 110.00},
      ...
    ]
  },
  "success": true
}
```

---

## 十一、财务记录模块

> ADR D10：银行对账采用 CSV 导入，不做直连银行 API。
> 财务记录关联合同（可选）和渠道（OTA 销售场景）。

### 11.1 财务记录列表

```
GET /biz/finance/list
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，默认 10 |
| contractId | long | 否 | 关联合同 ID |
| channelId | long | 否 | 关联渠道 ID |
| financeType | string | 否 | 财务类型：`income`=收入 / `expense`=支出 |
| bizDate | string | 否 | 业务日期（yyyy-MM-dd） |
| beginTime | string | 否 | 开始日期（yyyy-MM-dd） |
| endTime | string | 否 | 结束日期（yyyy-MM-dd） |

**响应示例：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "rows": [
    {
      "financeId": 1,
      "contractId": 10,
      "contractNo": "HT-2026-001",
      "channelId": 3,
      "channelName": "美团到综",
      "invoiceId": 5,
      "financeType": "income",
      "financeTypeLabel": "收入",
      "amount": 50000.00,
      "bizDate": "2026-06-15",
      "remark": "6月结算款",
      "createTime": "2026-06-20 10:00:00"
    }
  ],
  "total": 120,
  "pageNum": 1,
  "pageSize": 10,
  "success": true
}
```

### 11.2 新增财务记录

```
POST /biz/finance
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contractId | long | 否 | 关联合同 ID |
| channelId | long | 否 | 关联渠道 ID |
| invoiceId | long | 否 | 关联发票 ID |
| financeType | string | ✅ | `income` / `expense` |
| amount | decimal | ✅ | 金额 |
| bizDate | string | ✅ | 业务日期（yyyy-MM-dd） |
| remark | string | 否 | 备注 |

### 11.3 编辑财务记录

```
PUT /biz/finance
```

请求体同 11.2，增加 `financeId` 字段。

### 11.4 删除财务记录

```
DELETE /biz/finance/{ids}
```

**参数：** `ids` — 主键 ID，多个用逗号分隔。

### 11.5 银行对账 CSV 导入

```
POST /biz/finance/import
```

**Content-Type：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | ✅ | 银行 CSV 文件（GBK 编码） |
| channelId | long | 否 | 渠道 ID（自动关联渠道） |

**CSV 格式：**

```csv
交易日期,凭证号,对方账户,金额,摘要
2026-06-15,TXN001,美团结算户,50000.00,6月销售结算
2026-06-15,TXN002,抖音结算户,32000.00,6月销售结算
```

**响应：**

```json
{
  "code": 200,
  "msg": "导入成功，共处理 25 条记录",
  "data": {
    "total": 25,
    "success": 24,
    "failed": 1,
    "errors": [
      {"row": 5, "reason": "金额格式错误"}
    ]
  }
}
```

### 11.6 财务统计

```
GET /biz/finance/stats
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| beginTime | string | ✅ | 开始日期 |
| endTime | string | ✅ | 结束日期 |
| channelId | long | 否 | 渠道筛选 |

**响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "totalIncome": 1250000.00,
    "totalExpense": 680000.00,
    "netProfit": 570000.00,
    "incomeCount": 45,
    "expenseCount": 32
  },
  "success": true
}
```

---

## 十二、OTA 数据导入模块

> ADR D09：先做 CSV 导入兜底，API 对接作为第二阶段。
> 本模块为第一阶段实现。

### 12.1 渠道订单 CSV 导入

```
POST /biz/ota/import
```

**Content-Type：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | ✅ | 渠道订单 CSV |
| channelId | long | ✅ | 渠道 ID（`biz_channel.id`） |
| importMode | string | 否 | `merge`=合并更新 / `replace`=覆盖（默认 merge） |

**CSV 格式（美团示例）：**

```csv
订单号,票种名称,客户名称,数量,单价,金额,下单时间,核销时间,状态
ORD20260615001,景区门票-成人票,张三,2,100.00,200.00,2026-06-15 10:30:00,2026-06-15 14:00:00,已核销
```

**CSV 格式（抖音示例）：**

```csv
订单ID,商品名称,买家昵称,数量,单价,实付金额,下单时间,核销时间,状态
DY20260615001,酒店住宿-标准间,李四,1,380.00,350.00,2026-06-15 09:00:00,2026-06-15 15:00:00,已核销
```

> 不同渠道 CSV 格式不同，后端根据 `channelId` 匹配对应解析器。
> 解析器可通过 `biz_channel.channel_config`（JSON）配置字段映射。

**响应：**

```json
{
  "code": 200,
  "msg": "导入成功",
  "data": {
    "total": 100,
    "success": 98,
    "failed": 2,
    "errors": [
      {"row": 3, "orderNo": "ORD20260615003", "reason": "票种[无效票种]在系统中不存在"},
      {"row": 7, "orderNo": "ORD20260615007", "reason": "金额校验不通过：csv=150.00,系统=145.00"}
    ]
  }
}
```

### 12.2 导入记录查询

```
GET /biz/ota/import-log/list
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| channelId | long | 否 | 渠道 ID |
| beginTime | string | 否 | 开始时间 |
| endTime | string | 否 | 结束时间 |

**响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "rows": [
    {
      "logId": 1,
      "channelId": 1,
      "channelName": "美团到综",
      "fileName": "meituan_20260615.csv",
      "total": 100,
      "success": 98,
      "failed": 2,
      "operator": "admin",
      "createTime": "2026-06-15 16:00:00"
    }
  ],
  "total": 5,
  "success": true
}
```

### 12.3 渠道订单查询

```
GET /biz/ota/order/list
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| channelId | long | 否 | 渠道 ID |
| ticketId | long | 否 | 票种 ID |
| orderStatus | string | 否 | 订单状态：`paid`=已支付 / `used`=已核销 / `refunded`=已退款 |
| beginTime | string | 否 | 下单开始时间 |
| endTime | string | 否 | 下单结束时间 |

**响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "rows": [
    {
      "orderId": 1,
      "channelId": 1,
      "channelName": "美团到综",
      "orderNo": "ORD20260615001",
      "ticketId": 5,
      "ticketName": "景区门票-成人票",
      "customerName": "张三",
      "quantity": 2,
      "unitPrice": 100.00,
      "totalAmount": 200.00,
      "orderStatus": "used",
      "orderStatusLabel": "已核销",
      "orderTime": "2026-06-15 10:30:00",
      "useTime": "2026-06-15 14:00:00"
    }
  ],
  "total": 980,
  "success": true
}
```

---

## 十三、战略驾驶舱模块

> 经营总览：合同统计、渠道收入、经营数据趋势。
> 数据来源于 `biz_contract`、`biz_channel`、`biz_finance`、`biz_operation_data` 的聚合查询。

### 13.1 合同统计概览

```
GET /biz/cockpit/contract/stats
```

**响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "totalContracts": 156,
    "pendingContracts": 12,
    "approvedContracts": 138,
    "rejectedContracts": 6,
    "totalAmount": 5800000.00,
    "approvedAmount": 5200000.00,
    "byContractType": {
      "payment": {"count": 45, "amount": 3200000.00},
      "business": {"count": 111, "amount": 2600000.00}
    }
  },
  "success": true
}
```

### 13.2 渠道收入排行

```
GET /biz/cockpit/channel/revenue
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| beginTime | string | 否 | 开始月份（yyyy-MM） |
| endTime | string | 否 | 结束月份（yyyy-MM） |
| topN | int | 否 | 返回前 N 名，默认 10 |

**响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": [
    {"rank": 1, "channelId": 1, "channelName": "美团到综", "totalAmount": 1800000.00, "orderCount": 3200},
    {"rank": 2, "channelId": 2, "channelName": "抖音生活服务", "totalAmount": 1200000.00, "orderCount": 2800},
    {"rank": 3, "channelId": 3, "channelName": "携程商旅", "totalAmount": 850000.00, "orderCount": 950}
  ],
  "success": true
}
```

### 13.3 经营数据趋势

```
GET /biz/cockpit/operation/trend
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| beginMonth | string | ✅ | 开始月份（yyyy-MM） |
| endMonth | string | ✅ | 结束月份（yyyy-MM） |

**响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "monthly": [
      {"month": "2026-01", "revenue": 2800000.00, "profit": 950000.00, "cost": 1850000.00, "customerCount": 38},
      {"month": "2026-02", "revenue": 3100000.00, "profit": 1100000.00, "cost": 2000000.00, "customerCount": 42}
    ],
    "total": {
      "revenue": 5800000.00,
      "profit": 2050000.00,
      "cost": 3750000.00
    }
  },
  "success": true
}
```

### 13.4 驾驶舱首页聚合

```
GET /biz/cockpit/dashboard
```

**响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "summary": {
      "pendingApprovals": 12,
      "todayRevenue": 85000.00,
      "monthRevenue": 3100000.00,
      "customerCount": 42
    },
    "contractStats": {"total": 156, "approved": 138, "rejected": 6, "pending": 12},
    "channelRevenue": [
      {"channelName": "美团到综", "amount": 1800000.00, "growth": 15.0},
      {"channelName": "抖音生活服务", "amount": 1200000.00, "growth": 28.5}
    ],
    "operationTrend": [
      {"month": "2026-01", "revenue": 2800000.00},
      {"month": "2026-02", "revenue": 3100000.00}
    ]
  },
  "success": true
}
```

---

## 十四、通用接口

### 11.1 文件上传

```
POST /common/upload
```

**Content-Type：** `multipart/form-data`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | ✅ | 文件（支持 PDF、图片等） |
| `bizType` | string | 否 | 业务类型：`contract` / `customer` / `channel`，默认 `common` |

**成功响应：**

```json
{
  "code": 200,
  "msg": "上传成功",
  "data": {
    "fileName": "合同附件.pdf",
    "fileUrl": "/uploads/contract/2026/07/xxx.pdf",
    "fileSize": 2048000
  },
  "success": true
}
```

### 11.2 字典数据查询

```
GET /system/dict/data/type/{dictType}
```

**说明**：通过字典类型获取可选值列表，用于下拉框、Radio 等组件。

**成功响应：**

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": [
    {"dictLabel": "业务付款审批单", "dictValue": "payment"},
    {"dictLabel": "业务审批单", "dictValue": "business"}
  ],
  "success": true
}
```

---

## 十五、权限标识汇总

| 权限标识 | 说明 | 适用模块 |
|----------|------|----------|
| `*:*:*` | 超管全部权限 | admin |
| `contract:add` | 新建合同 | 合同管理 |
| `contract:edit` | 编辑合同 | 合同管理 |
| `contract:delete` | 删除合同 | 合同管理 |
| `contract:submit` | 提交审批 | 合同管理 |
| `contract:list` | 查看合同列表 | 合同管理、审批中心 |
| `contract:export` | 导出合同 | 合同管理 |
| `approval:approve` | 审批通过 | 审批中心 |
| `approval:reject` | 审批驳回 | 审批中心 |
| `approval:list` | 查看审批列表 | 审批中心 |
| `customer:add` | 新建客户 | 客户管理 |
| `customer:edit` | 编辑客户 | 客户管理 |
| `customer:delete` | 删除客户 | 客户管理 |
| `customer:list` | 查看客户列表 | 客户管理 |
| `channel:add` | 新建渠道 | 渠道管理 |
| `channel:edit` | 编辑渠道 | 渠道管理 |
| `channel:delete` | 删除渠道 | 渠道管理 |
| `channel:list` | 查看渠道列表 | 渠道管理 |
| `channel:import` | 导入回传数据 | 渠道管理 |
| `invoice:add` | 新建发票 | 发票管理 |
| `invoice:edit` | 编辑发票 | 发票管理 |
| `invoice:list` | 查看发票列表 | 发票管理 |
| `invoice:confirm` | 确认开票 | 发票管理 |
| `invoice:void` | 作废发票 | 发票管理 |
| `operation:add` | 录入经营数据 | 经营数据 |
| `operation:edit` | 编辑经营数据 | 经营数据 |
| `operation:delete` | 删除经营数据 | 经营数据 |
| `operation:list` | 查看经营数据 | 经营数据 |

---

## 十六、与其他设计文档的对应关系

| 本文 API | 对应业务规则 | 关联文档 |
|----------|--------------|----------|
| 5.7 提交审批 | Step 0 自动审批，附加电子签名 | 权限模型设计.md 第三章 |
| 6.2 审批通过 | 推进 current_step 或终态 | 权限模型设计.md 第三章 |
| 6.3 审批驳回 | `rejected` 语义为可重新提交 | ADR-架构决策记录.md D03 |
| 5.1 合同列表 | 数据范围过滤（role.data_scope） | 权限模型设计.md 第七章 |
| 6.1 待我审批列表 | role_sort 匹配 current_step | 权限模型设计.md 第三章 |
| 5.4 新建合同 | party_a=甲方（客户），party_b=乙方（本司） | ADR-架构决策记录.md D06 |
| 5.4 新建合同 | contract_no 手动输入 | ADR-架构决策记录.md D04 |
| 10.1~10.4 经营数据 | 手工录入，不与合同汇总 | ADR-架构决策记录.md D05 |
| 11.5 银行对账导入 | CSV 导入，不做直连银行 API | ADR-架构决策记录.md D10 |
| 12.1~12.3 OTA 导入 | 先 CSV 兜底，API 对接为第二阶段 | ADR-架构决策记录.md D09 |
| 13.1~13.4 战略驾驶舱 | 聚合合同/渠道/财务/经营数据 | 数据库设计.md 第四章 |

---

*文档结束*
