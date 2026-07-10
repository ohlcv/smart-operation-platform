# RuoYi 现状盘点

**文档版本**：V1.0  
**编写日期**：2026-07-10  
**对应目录**：`ruoyi-fastapi-backend/`、`ruoyi-fastapi-frontend/`、`ruoyi-fastapi-app/`  
**说明**：本清单基于 RuoYi FastAPI 项目现有代码实际实现整理，覆盖后端核心模块、前端功能页面、权限模型、数据模型及当前限制。

---

## 一、整体目录结构

```
ruoyi-fastapi-backend/
├── cli/                          # CLI 工具入口（内部命令、TUI、wizard）
├── common/                       # 公共模块
│   ├── aspect/                   # 切面：认证、权限、数据范围
│   ├── annotation/               # 注解：日志、缓存、限流
│   ├── router.py                 # 路由基类
│   ├── vo.py                     # 通用响应模型
│   ├── constant.py               # 常量
│   └── enums.py                  # 枚举
├── config/                       # 配置：数据库、环境、Redis
├── exceptions/                   # 异常处理
├── middlewares/                   # 中间件：CORS、上下文、追踪
├── module_admin/                 # 系统管理模块
│   ├── controller/               # 控制器：用户、角色、菜单、部门、字典、配置、通知、任务、日志
│   ├── service/                  # 服务层
│   ├── dao/                      # 数据访问层
│   └── entity/
│       ├── do/                   # 数据库实体
│       └── vo/                   # 视图对象 / Pydantic 模型
├── module_ai/                    # AI 模块
│   ├── controller/               # AI 对话、模型管理
│   ├── service/
│   ├── dao/
│   └── entity/
│       ├── do/                   # AI 模型、对话配置
│       └── vo/
├── module_generator/             # 代码生成模块
│   ├── controller/
│   ├── dao/
│   ├── entity/do/
│   └── templates/                # 前后端代码模板
├── sql/                          # 数据库初始化脚本
│   ├── ruoyi-fastapi.sql         # MySQL
│   └── ruoyi-fastapi-pg.sql      # PostgreSQL
├── tests/                        # 测试
├── utils/                        # 工具类
├── alembic/                      # 数据库迁移
├── Dockerfile.pg
├── requirements.txt
└── pyproject.toml

ruoyi-fastapi-frontend/
├── src/
│   ├── api/                      # API 请求封装
│   ├── components/               # 公共组件
│   ├── layout/                   # 布局组件
│   │   └── components/
│   │       ├── Navbar.vue
│   │       ├── Sidebar/
│   │       ├── TagsView/
│   │       ├── TopBar/
│   │       └── AppMain.vue
│   ├── router/                   # 路由配置
│   ├── store/                    # 状态管理
│   ├── utils/                    # 工具函数
│   ├── views/                    # 页面视图
│   │   ├── system/               # 系统管理
│   │   │   ├── user/             # 用户管理
│   │   │   ├── role/             # 角色管理
│   │   │   ├── menu/             # 菜单管理
│   │   │   ├── dept/             # 部门管理
│   │   │   ├── dict/             # 字典管理
│   │   │   ├── config/           # 参数配置
│   │   │   ├── post/             # 岗位管理
│   │   │   └── notice/           # 通知公告
│   │   ├── monitor/              # 监控管理
│   │   │   ├── operlog/          # 操作日志
│   │   │   ├── logininfor/       # 登录日志
│   │   │   ├── online/           # 在线用户
│   │   │   ├── job/              # 定时任务
│   │   │   ├── cache/            # 缓存监控
│   │   │   ├── druid/            # 数据库监控
│   │   │   ├── server/           # 服务监控
│   │   │   └── transportCrypto/  # 加解密监控
│   │   ├── tool/                 # 工具
│   │   │   ├── gen/              # 代码生成
│   │   │   ├── build/            # 表单构建
│   │   │   └── swagger/          # API 文档
│   │   ├── ai/                   # AI 模块
│   │   │   ├── chat/             # AI 对话
│   │   │   └── model/            # AI 模型管理
│   │   ├── dashboard/            # 首页
│   │   ├── login.vue             # 登录页
│   │   ├── register.vue          # 注册页
│   │   └── error/                # 错误页面
│   ├── App.vue
│   └── main.js
├── vite.config.js
├── package.json
└── .env.docker

ruoyi-fastapi-app/                 # 小程序/App 端（uni-app）
├── src/
│   ├── pages/                    # 页面
│   │   ├── login.vue
│   │   ├── index.vue
│   │   ├── register.vue
│   │   └── mine/
│   ├── api/
│   ├── utils/
│   ├── permission.js
│   └── App.vue
└── tsconfig.json
```

---

## 二、后端模块清单

### 2.1 模块概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 系统管理 | `module_admin/` | 用户、角色、菜单、部门、字典、配置、通知、岗位、任务、日志 |
| AI 模块 | `module_ai/` | AI 对话配置、模型管理 |
| 代码生成 | `module_generator/` | 基于表结构的代码生成 |
| 公共组件 | `common/` | 认证、权限、数据范围、缓存、日志注解 |
| CLI 工具 | `cli/` | 开发、配置、数据库、任务、加密等 CLI 命令 |

### 2.2 系统管理模块详细清单

| 子模块 | 控制器 | 服务 | DAO | 实体 DO | 实体 VO |
|--------|--------|------|-----|---------|---------|
| 用户管理 | `user_controller.py` | `user_service.py` | `user_dao.py` | `SysUser`、`SysUserRole`、`SysUserPost` | `UserModel`、`UserInfoModel`、`CurrentUserModel` |
| 角色管理 | `role_controller.py` | `role_service.py` | `role_dao.py` | `SysRole`、`SysRoleMenu`、`SysRoleDept` | `RoleModel`、`RoleMenuModel`、`RoleDeptModel` |
| 菜单管理 | `menu_controller.py` | `menu_service.py` | `menu_dao.py` | `SysMenu` | `MenuModel`、`MenuTreeModel` |
| 部门管理 | `dept_controller.py` | `dept_service.py` | `dept_dao.py` | `SysDept` | `DeptModel` |
| 字典管理 | `dict_controller.py` | - | `dict_dao.py` | `SysDictType`、`SysDictData` | `DictModel`、`DictDataModel` |
| 参数配置 | `config_controller.py` | `config_service.py` | `config_dao.py` | `SysConfig` | `ConfigModel` |
| 通知公告 | `notice_controller.py` | - | - | `SysNotice` | `NoticeModel` |
| 岗位管理 | `post_controller.py` | `post_service.py` | - | `SysPost` | `PostModel` |
| 定时任务 | `job_controller.py` | `job_service.py`、`job_log_service.py` | `job_dao.py`、`job_log_dao.py` | `SysJob`、`SysJobLog` | `JobModel`、`JobLogModel` |
| 操作日志 | `log_controller.py` | `log_service.py` | - | `SysLogininfor`、`SysOperLog` | `LogininforModel`、`OperLogModel` |
| 服务监控 | `server_controller.py` | `server_service.py` | - | - | `ServerModel` |
| 缓存监控 | `cache_controller.py` | `cache_service.py` | - | - | - |
| 在线用户 | `online_controller.py` | - | - | - | - |
| 加解密监控 | `transport_crypto_controller.py` | - | - | - | - |

### 2.3 AI 模块

| 子模块 | 控制器 | 服务 | DAO | 实体 DO | 说明 |
|--------|--------|------|-----|---------|------|
| AI 对话 | `ai_chat_controller.py` | `ai_chat_service.py` | `ai_chat_dao.py` | `AiChatConfig` | 用户级对话配置 |
| AI 模型管理 | `ai_model_controller.py` | `ai_model_service.py` | `ai_model_dao.py` | `AiModels` | 模型配置、API Key、Base URL |

### 2.4 代码生成模块

| 子模块 | 说明 |
|--------|------|
| `gen_controller.py` | 代码生成入口 |
| `gen_dao.py` | 代码生成数据访问 |
| `entity/do/gen_do.py` | `GenTable`、`GenTableColumn` |
| `templates/` | Python/Vue/JS/SQL 模板 |

---

## 三、前端模块清单

### 3.1 页面清单

| 模块 | 页面路径 | 功能说明 |
|------|----------|----------|
| 登录/注册 | `login.vue`、`register.vue` | 账号密码登录、注册 |
| 首页 | `dashboard/index.vue` | 工作台 |
| 个人中心 | `system/user/profile/index.vue` | 个人信息、头像、密码修改 |
| 系统管理-用户 | `system/user/index.vue`、`authRole.vue` | 用户列表、分配角色 |
| 系统管理-角色 | `system/role/index.vue`、`authUser.vue` | 角色列表、分配用户、数据权限、菜单权限 |
| 系统管理-菜单 | `system/menu/index.vue` | 菜单树管理 |
| 系统管理-部门 | `system/dept/index.vue` | 部门树管理 |
| 系统管理-字典 | `system/dict/index.vue`、`data.vue` | 字典类型、字典数据 |
| 系统管理-参数 | `system/config/index.vue` | 系统参数配置 |
| 系统管理-通知 | `system/notice/index.vue` | 通知公告管理 |
| 系统管理-岗位 | `system/post/index.vue` | 岗位管理 |
| 监控管理-登录日志 | `monitor/logininfor/index.vue` | 登录日志查询 |
| 监控管理-操作日志 | `monitor/operlog/index.vue` | 操作日志查询 |
| 监控管理-在线用户 | `monitor/online/index.vue` | 在线用户管理 |
| 监控管理-定时任务 | `monitor/job/index.vue`、`log.vue` | 任务列表、调度日志 |
| 监控管理-缓存 | `monitor/cache/index.vue`、`list.vue` | 缓存监控 |
| 监控管理-数据库 | `monitor/druid/index.vue` | Druid 监控 |
| 监控管理-服务 | `monitor/server/index.vue` | 服务监控 |
| 监控管理-加解密 | `monitor/transportCrypto/index.vue` | 加解密监控 |
| 工具-代码生成 | `tool/gen/index.vue`、`editTable.vue`、`createTable.vue`、`importTable.vue` | 代码生成 |
| 工具-表单构建 | `tool/build/index.vue` | 可视化表单构建 |
| 工具-Swagger | `tool/swagger/index.vue` | API 文档 |
| AI-对话 | `ai/chat/index.vue` | AI 对话界面 |
| AI-模型管理 | `ai/model/index.vue` | AI 模型配置 |

### 3.2 布局与公共组件

| 组件 | 路径 | 说明 |
|------|------|------|
| 主布局 | `layout/index.vue` | 侧边栏 + 顶栏 + 内容区 |
| 侧边栏 | `layout/components/Sidebar/` | 菜单渲染、折叠 |
| 顶部栏 | `layout/components/TopBar/` | 用户信息、全屏、主题 |
| 标签页 | `layout/components/TagsView/` | 多标签页导航 |
| 面包屑 | `layout/components/Breadcrumb/` | 面包屑导航 |
| 图标选择 | `components/SvgIcon/` | SVG 图标 |
| 文件上传 | `components/FileUpload/` | 文件上传组件 |
| 分页 | `components/Pagination/` | 分页组件 |
| 富文本 | `components/Editor/` | Markdown/富文本编辑器 |
| 图片预览 | `components/ImagePreview/` | 图片预览 |
| 全屏 | `components/Screenfull/` | 全屏切换 |
| 字典标签 | `components/DictTag/` | 字典值标签渲染 |

### 3.3 路由结构

| 类型 | 路由 | 说明 |
|------|------|------|
| 公共路由 | `/login`、`/register`、`/401`、`/404` | 无需登录 |
| 动态路由 | `/system/**`、`/monitor/**`、`/tool/**`、`/ai/**` | 基于权限动态加载 |
| 隐藏路由 | `/redirect/**`、`/user/profile/**` | 不显示在侧边栏 |

---

## 四、权限模型

### 4.1 核心表关系

```
sys_user
  ├── sys_user_role (多对多) → sys_role
  │                             ├── sys_role_menu (多对多) → sys_menu
  │                             └── sys_role_dept (多对多) → sys_dept
  └── sys_user_post (多对多) → sys_post

sys_menu
  ├── 父菜单/子菜单 (parent_id)
  └── perms (权限标识，如 system:user:list)
```

### 4.2 用户模型

**表名**：`sys_user`

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | bigint | 主键 |
| `dept_id` | bigint | 部门 ID |
| `user_name` | varchar(30) | 用户账号，唯一 |
| `nick_name` | varchar(30) | 用户昵称 |
| `user_type` | char(2) | 用户类型（00 系统用户） |
| `email` | varchar(50) | 邮箱 |
| `phonenumber` | varchar(11) | 手机号 |
| `sex` | char(1) | 性别（0男 1女 2未知） |
| `avatar` | varchar(100) | 头像地址 |
| `password` | varchar(100) | 密码 |
| `status` | char(1) | 账号状态（0正常 1停用） |
| `del_flag` | char(1) | 删除标志（0存在 2删除） |
| `login_ip` | varchar(128) | 最后登录 IP |
| `login_date` | datetime | 最后登录时间 |
| `pwd_update_date` | datetime | 密码最后更新时间 |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

**关联表**：
- `sys_user_role(user_id, role_id)` - 用户角色关联
- `sys_user_post(user_id, post_id)` - 用户岗位关联

### 4.3 角色模型

**表名**：`sys_role`

| 字段 | 类型 | 说明 |
|------|------|------|
| `role_id` | bigint | 主键 |
| `role_name` | varchar(30) | 角色名称 |
| `role_key` | varchar(100) | 角色权限字符串 |
| `role_sort` | int | 显示顺序 |
| `data_scope` | char(1) | 数据范围（1-5） |
| `menu_check_strictly` | tinyint | 菜单树选择是否关联显示 |
| `dept_check_strictly` | tinyint | 部门树选择是否关联显示 |
| `status` | char(1) | 角色状态（0正常 1停用） |
| `del_flag` | char(1) | 删除标志（0存在 2删除） |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

**关联表**：
- `sys_role_menu(role_id, menu_id)` - 角色菜单关联
- `sys_role_dept(role_id, dept_id)` - 角色部门关联

### 4.4 菜单模型

**表名**：`sys_menu`

| 字段 | 类型 | 说明 |
|------|------|------|
| `menu_id` | bigint | 主键 |
| `menu_name` | varchar(50) | 菜单名称 |
| `parent_id` | bigint | 父菜单 ID |
| `order_num` | int | 显示顺序 |
| `path` | varchar(200) | 路由地址 |
| `component` | varchar(255) | 组件路径 |
| `query` | varchar(255) | 路由参数 |
| `route_name` | varchar(50) | 路由名称 |
| `is_frame` | int | 是否为外链（0是 1否） |
| `is_cache` | int | 是否缓存（0缓存 1不缓存） |
| `menu_type` | char(1) | 菜单类型（M目录 C菜单 F按钮） |
| `visible` | char(1) | 菜单状态（0显示 1隐藏） |
| `status` | char(1) | 菜单状态（0正常 1停用） |
| `perms` | varchar(100) | 权限标识 |
| `icon` | varchar(100) | 菜单图标 |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

### 4.5 部门模型

**表名**：`sys_dept`

| 字段 | 类型 | 说明 |
|------|------|------|
| `dept_id` | bigint | 主键 |
| `parent_id` | bigint | 父部门 ID |
| `ancestors` | varchar(50) | 祖级列表 |
| `dept_name` | varchar(30) | 部门名称 |
| `order_num` | int | 显示顺序 |
| `leader` | varchar(20) | 负责人 |
| `phone` | varchar(11) | 联系电话 |
| `email` | varchar(50) | 邮箱 |
| `status` | char(1) | 部门状态（0正常 1停用） |
| `del_flag` | char(1) | 删除标志（0存在 2删除） |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |

### 4.6 5 级数据权限

**字段**：`sys_role.data_scope`

| 值 | 说明 | 实现逻辑 |
|----|------|----------|
| `1` | 全部数据权限 | 可查看所有数据 |
| `2` | 自定数据权限 | 通过 `sys_role_dept` 关联部门 |
| `3` | 本部门数据权限 | 仅可查看本部门数据 |
| `4` | 本部门及以下数据权限 | 可查看本部门及子部门数据 |
| `5` | 仅本人数据权限 | 仅可查看自己创建的数据 |

**使用方式**：
```python
# 在查询时自动注入数据权限 SQL
data_scope_sql = DataScopeDependency(SysDept)
# 或指定字段别名
data_scope_sql = DataScopeDependency(SysUser, user_alias='user_id', dept_alias='dept_id')
```

### 4.7 接口权限与角色权限

**接口权限校验**：
```python
# 按权限标识鉴权
dependencies=[UserInterfaceAuthDependency('system:role:list')]
dependencies=[UserInterfaceAuthDependency(['system:role:list', 'system:role:export'])]
dependencies=[UserInterfaceAuthDependency(['system:role:list', 'system:role:export'], is_strict=True)]

# 按角色标识鉴权
dependencies=[RoleInterfaceAuthDependency('admin')]
dependencies=[RoleInterfaceAuthDependency(['admin', 'common'])]
```

**前端权限指令**：
```javascript
// 权限标识校验
v-hasPermi="['system:user:add']"

// 角色校验
v-hasRole="['admin']"
```

### 4.8 登录认证流程

```
1. 用户提交账号密码
2. 后端校验验证码（可选）
3. 校验用户名密码
4. 生成 JWT Token
5. 存入 Redis（支持单点登录）
6. 返回 Token 给前端
7. 后续请求携带 Token 进行认证
```

**Token 结构**：
```python
{
    "user_id": "1",
    "user_name": "admin",
    "dept_name": "研发部",
    "session_id": "uuid",
    "login_info": {...}
}
```

---

## 五、数据模型

### 5.1 系统管理模型

#### 5.1.1 用户与角色关联

**表名**：`sys_user_role`

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | bigint | 用户 ID（联合主键） |
| `role_id` | bigint | 角色 ID（联合主键） |

#### 5.1.2 用户与岗位关联

**表名**：`sys_user_post`

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | bigint | 用户 ID（联合主键） |
| `post_id` | bigint | 岗位 ID（联合主键） |

#### 5.1.3 角色与菜单关联

**表名**：`sys_role_menu`

| 字段 | 类型 | 说明 |
|------|------|------|
| `role_id` | bigint | 角色 ID（联合主键） |
| `menu_id` | bigint | 菜单 ID（联合主键） |

#### 5.1.4 角色与部门关联

**表名**：`sys_role_dept`

| 字段 | 类型 | 说明 |
|------|------|------|
| `role_id` | bigint | 角色 ID（联合主键） |
| `dept_id` | bigint | 部门 ID（联合主键） |

### 5.2 监控管理模型

#### 5.2.1 系统访问记录

**表名**：`sys_logininfor`

| 字段 | 类型 | 说明 |
|------|------|------|
| `info_id` | bigint | 主键 |
| `user_name` | varchar(50) | 用户账号 |
| `ipaddr` | varchar(128) | 登录 IP 地址 |
| `login_location` | varchar(255) | 登录地点 |
| `browser` | varchar(50) | 浏览器类型 |
| `os` | varchar(50) | 操作系统 |
| `status` | char(1) | 登录状态（0成功 1失败） |
| `msg` | varchar(255) | 提示消息 |
| `login_time` | datetime | 访问时间 |

#### 5.2.2 操作日志记录

**表名**：`sys_oper_log`

| 字段 | 类型 | 说明 |
|------|------|------|
| `oper_id` | bigint | 主键 |
| `title` | varchar(50) | 模块标题 |
| `business_type` | int | 业务类型（0其它 1新增 2修改 3删除） |
| `method` | varchar(100) | 方法名称 |
| `request_method` | varchar(10) | 请求方式 |
| `operator_type` | int | 操作类别（0其它 1后台用户 2手机端用户） |
| `oper_name` | varchar(50) | 操作人员 |
| `dept_name` | varchar(50) | 部门名称 |
| `oper_url` | varchar(255) | 请求 URL |
| `oper_ip` | varchar(128) | 主机地址 |
| `oper_location` | varchar(255) | 操作地点 |
| `oper_param` | varchar(2000) | 请求参数 |
| `json_result` | varchar(2000) | 返回参数 |
| `status` | int | 操作状态（0正常 1异常） |
| `error_msg` | varchar(2000) | 错误消息 |
| `oper_time` | datetime | 操作时间 |
| `cost_time` | bigint | 消耗时间 |

### 5.3 任务调度模型

#### 5.3.1 定时任务调度

**表名**：`sys_job`

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | bigint | 主键 |
| `job_name` | varchar(64) | 任务名称 |
| `job_group` | varchar(64) | 任务组名 |
| `job_executor` | varchar(64) | 任务执行器 |
| `invoke_target` | varchar(500) | 调用目标字符串 |
| `job_args` | varchar(255) | 位置参数 |
| `job_kwargs` | varchar(255) | 关键字参数 |
| `cron_expression` | varchar(255) | cron 执行表达式 |
| `misfire_policy` | varchar(20) | 计划执行错误策略 |
| `concurrent` | char(1) | 是否并发执行（0允许 1禁止） |
| `status` | char(1) | 状态（0正常 1暂停） |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注信息 |

#### 5.3.2 定时任务调度日志

**表名**：`sys_job_log`

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_log_id` | bigint | 主键 |
| `job_name` | varchar(64) | 任务名称 |
| `job_group` | varchar(64) | 任务组名 |
| `job_executor` | varchar(64) | 任务执行器 |
| `invoke_target` | varchar(500) | 调用目标字符串 |
| `job_args` | varchar(255) | 位置参数 |
| `job_kwargs` | varchar(255) | 关键字参数 |
| `job_trigger` | varchar(255) | 任务触发器 |
| `job_message` | varchar(500) | 日志信息 |
| `status` | char(1) | 执行状态（0正常 1失败） |
| `exception_info` | varchar(2000) | 异常信息 |
| `create_time` | datetime | 创建时间 |

### 5.4 字典与配置模型

#### 5.4.1 字典类型

**表名**：`sys_dict_type`

| 字段 | 类型 | 说明 |
|------|------|------|
| `dict_id` | bigint | 主键 |
| `dict_name` | varchar(100) | 字典名称 |
| `dict_type` | varchar(100) | 字典类型，唯一 |
| `status` | char(1) | 状态（0正常 1停用） |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

#### 5.4.2 字典数据

**表名**：`sys_dict_data`

| 字段 | 类型 | 说明 |
|------|------|------|
| `dict_code` | bigint | 主键 |
| `dict_sort` | int | 字典排序 |
| `dict_label` | varchar(100) | 字典标签 |
| `dict_value` | varchar(100) | 字典键值 |
| `dict_type` | varchar(100) | 字典类型 |
| `css_class` | varchar(100) | 样式属性 |
| `list_class` | varchar(100) | 表格回显样式 |
| `is_default` | char(1) | 是否默认（Y是 N否） |
| `status` | char(1) | 状态（0正常 1停用） |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

#### 5.4.3 参数配置

**表名**：`sys_config`

| 字段 | 类型 | 说明 |
|------|------|------|
| `config_id` | int | 主键 |
| `config_name` | varchar(100) | 参数名称 |
| `config_key` | varchar(100) | 参数键名 |
| `config_value` | varchar(500) | 参数键值 |
| `config_type` | char(1) | 系统内置（Y是 N否） |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

### 5.5 通知公告模型

**表名**：`sys_notice`

| 字段 | 类型 | 说明 |
|------|------|------|
| `notice_id` | int | 主键 |
| `notice_title` | varchar(50) | 公告标题 |
| `notice_type` | char(1) | 公告类型（1通知 2公告） |
| `notice_content` | blob | 公告内容 |
| `status` | char(1) | 公告状态（0正常 1关闭） |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(255) | 备注 |

### 5.6 AI 模块模型

#### 5.6.1 AI 模型

**表名**：`ai_models`

| 字段 | 类型 | 说明 |
|------|------|------|
| `model_id` | bigint | 主键 |
| `model_code` | varchar(100) | 模型编码 |
| `model_name` | varchar(100) | 模型名称 |
| `provider` | varchar(50) | 提供商 |
| `model_sort` | int | 显示顺序 |
| `api_key` | varchar(255) | API Key |
| `base_url` | varchar(255) | Base URL |
| `model_type` | varchar(50) | 模型类型 |
| `max_tokens` | int | 最大输出 token |
| `temperature` | float | 默认温度 |
| `support_reasoning` | char(1) | 是否支持推理 |
| `support_images` | char(1) | 是否支持图片 |
| `status` | char(1) | 模型状态 |
| `user_id` / `dept_id` | bigint | 所属用户/部门 |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

#### 5.6.2 AI 对话配置

**表名**：`ai_chat_config`

| 字段 | 类型 | 说明 |
|------|------|------|
| `chat_config_id` | bigint | 主键 |
| `user_id` | bigint | 用户 ID，唯一 |
| `temperature` | float | 默认温度 |
| `add_history_to_context` | char(1) | 是否添加历史记录 |
| `num_history_runs` | int | 历史记录条数 |
| `system_prompt` | text | 系统提示词 |
| `metrics_default_visible` | char(1) | 默认显示指标 |
| `vision_enabled` | char(1) | 是否开启视觉 |
| `image_max_size_mb` | int | 图片最大大小 |
| `create_time` / `update_time` | datetime | 创建/更新时间 |

### 5.7 代码生成模型

#### 5.7.1 代码生成业务表

**表名**：`gen_table`

| 字段 | 类型 | 说明 |
|------|------|------|
| `table_id` | bigint | 主键 |
| `table_name` | varchar(200) | 表名称 |
| `table_comment` | varchar(500) | 表描述 |
| `sub_table_name` | varchar(64) | 关联子表名 |
| `sub_table_fk_name` | varchar(64) | 子表外键名 |
| `class_name` | varchar(100) | 实体类名称 |
| `tpl_category` | varchar(200) | 模板类别 |
| `tpl_web_type` | varchar(30) | 前端模板类型 |
| `package_name` | varchar(100) | 包路径 |
| `module_name` | varchar(30) | 模块名 |
| `business_name` | varchar(30) | 业务名 |
| `function_name` | varchar(50) | 功能名 |
| `function_author` | varchar(50) | 功能作者 |
| `gen_type` | char(1) | 生成代码方式 |
| `gen_path` | varchar(200) | 生成路径 |
| `options` | varchar(1000) | 其它生成选项 |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |
| `remark` | varchar(500) | 备注 |

#### 5.7.2 代码生成业务表字段

**表名**：`gen_table_column`

| 字段 | 类型 | 说明 |
|------|------|------|
| `column_id` | bigint | 主键 |
| `table_id` | bigint | 归属表编号 |
| `column_name` | varchar(200) | 列名称 |
| `column_comment` | varchar(500) | 列描述 |
| `column_type` | varchar(100) | 列类型 |
| `python_type` | varchar(500) | Python 类型 |
| `python_field` | varchar(200) | Python 字段名 |
| `is_pk` | char(1) | 是否主键 |
| `is_increment` | char(1) | 是否自增 |
| `is_required` | char(1) | 是否必填 |
| `is_unique` | char(1) | 是否唯一 |
| `is_insert` | char(1) | 是否为插入字段 |
| `is_edit` | char(1) | 是否编辑字段 |
| `is_list` | char(1) | 是否列表字段 |
| `is_query` | char(1) | 是否查询字段 |
| `query_type` | varchar(200) | 查询方式 |
| `html_type` | varchar(200) | 显示类型 |
| `dict_type` | varchar(200) | 字典类型 |
| `sort` | int | 排序 |
| `create_by` / `create_time` | - | 创建信息 |
| `update_by` / `update_time` | - | 更新信息 |

---

## 六、核心业务流程

### 6.1 用户认证流程

```
1. 用户访问登录页
2. 输入账号密码（可选验证码）
3. 后端验证账号密码
4. 生成 JWT Token
5. Token 存入 Redis
6. 返回 Token 给前端
7. 前端存储 Token 并跳转首页
8. 后续请求在 Header 携带 Token
9. 后端通过 PreAuthDependency 验证 Token
10. 加载用户权限、角色、菜单路由
```

### 6.2 权限加载流程

```
1. 用户登录成功
2. 调用 /getInfo 获取用户信息
   - 用户基本信息
   - 角色列表
   - 权限标识列表
   - 菜单列表
3. 调用 /getRouters 获取动态路由
   - 根据用户角色过滤菜单
   - 生成前端路由配置
4. 前端动态添加路由
5. 渲染侧边栏菜单
```

### 6.3 数据权限流程

```
1. 用户发起数据查询请求
2. DataScopeDependency 注入数据权限 SQL
3. 根据用户角色 data_scope 值生成查询条件：
   - 1：不限制，查询全部
   - 2：查询自定义部门数据
   - 3：查询本部门数据
   - 4：查询本部门及子部门数据
   - 5：查询本人数据
4. 将权限 SQL 拼接到业务查询中
5. 返回过滤后的数据
```

### 6.4 代码生成流程

```
1. 选择数据库表
2. 导入表结构信息
3. 配置生成选项：
   - 包路径、模块名、业务名
   - 前端模板类型
   - 生成方式（压缩包/自定义路径）
4. 预览生成代码
5. 生成并下载代码
   - 后端：Model、DAO、Service、Controller、VO
   - 前端：API、Index.vue
```

---

## 七、前端功能清单

### 7.1 系统管理功能

| 功能 | 页面 | 操作 |
|------|------|------|
| 用户管理 | `system/user/index.vue` | 查询、新增、编辑、删除、重置密码、分配角色、查看详情 |
| 角色管理 | `system/role/index.vue` | 查询、新增、编辑、删除、分配用户、数据权限、菜单权限、修改状态 |
| 菜单管理 | `system/menu/index.vue` | 查询、新增、编辑、删除菜单树 |
| 部门管理 | `system/dept/index.vue` | 查询、新增、编辑、删除部门树 |
| 字典管理 | `system/dict/index.vue` | 查询、新增、编辑、删除字典类型 |
| 字典数据 | `system/dict/data.vue` | 查询、新增、编辑、删除字典数据 |
| 参数配置 | `system/config/index.vue` | 查询、新增、编辑、删除系统参数 |
| 通知公告 | `system/notice/index.vue` | 查询、新增、编辑、删除通知 |
| 岗位管理 | `system/post/index.vue` | 查询、新增、编辑、删除岗位 |
| 个人中心 | `system/user/profile/index.vue` | 查看信息、修改头像、修改密码 |

### 7.2 监控管理功能

| 功能 | 页面 | 操作 |
|------|------|------|
| 在线用户 | `monitor/online/index.vue` | 查看在线用户、强退 |
| 登录日志 | `monitor/logininfor/index.vue` | 查询、删除、导出 |
| 操作日志 | `monitor/operlog/index.vue` | 查询、删除、导出 |
| 定时任务 | `monitor/job/index.vue` | 查询、新增、编辑、删除、执行、日志 |
| 缓存监控 | `monitor/cache/index.vue` | 查看缓存、删除缓存 |
| 数据库监控 | `monitor/druid/index.vue` | Druid 监控面板 |
| 服务监控 | `monitor/server/index.vue` | CPU、内存、JVM 信息 |
| 加解密监控 | `monitor/transportCrypto/index.vue` | 加解密配置监控 |

### 7.3 工具功能

| 功能 | 页面 | 操作 |
|------|------|------|
| 代码生成 | `tool/gen/index.vue` | 导入表、生成代码、预览、下载 |
| 表单构建 | `tool/build/index.vue` | 可视化拖拽构建表单 |
| API 文档 | `tool/swagger/index.vue` | 查看 API 文档 |

### 7.4 AI 功能

| 功能 | 页面 | 操作 |
|------|------|------|
| AI 对话 | `ai/chat/index.vue` | 多轮对话、历史记录、配置 |
| AI 模型管理 | `ai/model/index.vue` | 模型配置、API Key 管理 |

---

## 八、技术栈

### 8.1 后端技术栈

| 技术 | 版本/说明 |
|------|-----------|
| 框架 | FastAPI |
| 数据库 ORM | SQLAlchemy 2.0（异步） |
| 数据库 | MySQL 8.0 / PostgreSQL |
| 认证 | JWT + OAuth2PasswordBearer |
| 缓存 | Redis |
| 数据验证 | Pydantic v2 |
| 异步任务 | APScheduler |
| 日志 | 操作日志 + 登录日志 + 异常日志 |
| 限流 | 自定义注解 |
| 代码生成 | Jinja2 模板 |

### 8.2 前端技术栈

| 技术 | 版本/说明 |
|------|-----------|
| 框架 | Vue 3 |
| UI 组件库 | Element Plus |
| 构建工具 | Vite |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios |
| 权限指令 | 自定义 `v-hasPermi`、`v-hasRole` |
| 图表 | ECharts |
| 富文本 | Markdown 编辑器 |
| 小程序 | uni-app（ruoyi-fastapi-app） |

---

## 九、当前实现限制与备注

| 维度 | 现状 |
|------|------|
| 业务模块 | 以系统管理、监控、代码生成、AI 为主，无业务审批流 |
| AI 能力 | 有模型管理和对话配置，未接入真实大模型 |
| 前端页面 | 标准管理后台，无科技感 UI/大屏 |
| 数据权限 | 5 级数据权限已实现，但前端配合不完整 |
| 代码生成 | 支持单表/树表，模板为通用 CRUD |
| 部署 | 支持 Docker，无 Kubernetes 配置 |
| 小程序 | 有独立 ruoyi-fastapi-app，功能简单 |
| 国际化 | 无 |
| 多租户 | 无 |

---

## 十、与 v1 项目对比

| 维度 | v1 项目 | RuoYi |
|------|---------|-------|
| 定位 | 供应链业务平台 Demo | 通用后台管理框架 |
| 核心功能 | 7 级审批流、渠道集成、经营数据 | 系统管理、监控、代码生成、AI |
| 权限模型 | 单角色 7 级链 | 多角色 + 菜单权限 + 数据权限 |
| 前端风格 | 科技感暗色主题 | 标准管理后台 |
| 数据模型 | 6 张业务表 | 12+ 张系统表 + AI 表 |
| 扩展性 | 低（硬编码业务） | 高（代码生成 + 动态菜单） |
| 生产就绪 | 否 | 部分就绪（有日志、监控、缓存） |

---

*文档结束*
