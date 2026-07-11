# 系统接口页 Swagger UI 加载报 YAMLException:相对路径 openapi_url 落进 SPA fallback

**日期**：2026-07-11
**类型**：前端反向代理缺失 / iframe 相对路径解析陷阱
**影响**：用户进入「系统工具 → 系统接口」菜单，iframe 内 swagger UI 报 `YAMLException: end of the stream or a document separator is expected`，整个 API 文档页面无法渲染出接口列表
**根因**：`src/views/tool/swagger/index.vue` 把 iframe src 拼成 `/dev-api/proxy-docs`，但 swagger UI HTML 内部嵌入的 `SwaggerUIBundle({ url: '/openapi.json' })` 是相对路径。iframe 内浏览器以**前端 dev server 的 host**为根解析该相对 URL，最终落到 `http://前端host/openapi.json`——该路径**未被 `/dev-api` 代理规则匹配**（proxy 的 rewrite 会剥掉 `/dev-api` 前缀，这里根本没有 `/dev-api`），因此 Vite 走 SPA fallback 返回项目根 `index.html`（含 MonacoEditor 的 `<script>self["MonacoEnvironment"] = ...`），被 swagger-ui 当 OpenAPI YAML/JSON 解析 → 抛 `YAMLException`

---

## 1. 现象

用户在「系统工具 → 系统接口」菜单（`/tool/swagger`）打开后：

```
YAMLException {name: 'YAMLException', reason: 'end of the stream or a document separator is expected', ...}
message: "end of the stream or a document separator is expected (7:22)

 4 | <head>
 5 |   <script>self["MonacoEnvironment"] = (function (paths) {
 6 |           return {
 7 |             globalAPI: false,
--------------------------^
 8 |             getWorkerUrl : function (moduleId, label) {
 9 |               var result =  paths[label];
"
   at newAction (.../swagger-ui-bundle.js:2:573806)
```

错误在 swagger UI 加载 `openapiUrl` 时抛出，buffer 不是 JSON/YAML，而是 Monaco Editor 的 worker 注入脚本。浏览器开发者工具 Network 面板能看到：`/openapi.json` 这次的响应是 `index.html`（HTML, 200），而不是 JSON。

---

## 2. 链路分析：iframe + 相对路径 + Vite SPA fallback

### 2.1 涉及文件

| 文件 | 行 | 作用 |
|---|---|---|
| `ruoyi-fastapi-frontend/src/views/tool/swagger/index.vue:8` | iframe 入口，src 拼 `VITE_APP_BASE_API + "/proxy-docs"` | 浏览器看到 `/dev-api/proxy-docs`（dev 环境） |
| `ruoyi-fastapi-frontend/.env.development:8` | `VITE_APP_BASE_API = '/dev-api'` | dev 前缀 |
| `ruoyi-fastapi-frontend/vite.config.js:46-52` | Vite 代理（旧） | 只代理 `/dev-api`，`rewrite: p.replace(/^\/dev-api/, '')`，命中后端 `/proxy-docs` |
| `ruoyi-fastapi-backend/utils/server_util.py:24-31, 230-240` | FastAPI 自定义 swagger HTML | `_custom_swagger` 调用 `get_swagger_ui_html(openapi_url='/openapi.json')`，输出 HTML 包含 `SwaggerUIBundle({ url: '/openapi.json', ... })` |

### 2.2 完整请求链路（修复前）

```
[浏览器]
  GET http://127.0.0.1:8080/dev-api/proxy-docs                          (1)
[Vite proxy]
  rewrite: /dev-api/proxy-docs → /proxy-docs
  → 转发 http://127.0.0.1:9099/proxy-docs                              (2)
[FastAPI]
  APIDocsUtil._custom_swagger()
    → get_swagger_ui_html(openapi_url='/openapi.json', ...)
    → 返回 HTML（含 SwaggerUIBundle({ url: '/openapi.json' })）        (3)
[浏览器 iframe 内执行 swagger-ui-bundle.js]
  fetch('/openapi.json')        ← 解析为相对 iframe 当前 URL
  iframe 当前 URL = http://127.0.0.1:8080/dev-api/proxy-docs
  → 浏览器解析 '/openapi.json' 为 http://127.0.0.1:8080/openapi.json  (4)
[Vite]
  没有匹配 '/dev-api' 模式（路径是 '/openapi.json'，开头不是 '/dev-api'）
  走 SPA fallback → 返回 index.html（含 MonacoEditor inline 脚本）  (5)
[swagger-ui]
  把 index.html 当 openapi JSON 解析
  → YAMLException（结构错位 + MonacoEnvironment 关键字）            (6)
```

关键在第 (4) 步：浏览器在 iframe 内**只看 iframe 当前 URL 的 host**作为 base，不会保留 `/dev-api` 这层语义契约前缀。

### 2.3 直连验证（已通过 curl/python 实测）

```bash
# 后端 9099 端所有路径都正常，issue 不在后端
$ python3 -c "
import urllib.request
for path in ['/proxy-docs', '/openapi.json', '/proxy-openapi.json', '/proxy-redoc']:
    r = urllib.request.urlopen('http://127.0.0.1:9099'+path, timeout=2)
    print(path, r.status, r.headers.get('Content-Type'))
"
/proxy-docs             200 text/html; charset=utf-8
/openapi.json           200 application/json       ← 347 KB 合法 OpenAPI
/proxy-openapi.json     200 application/json
/proxy-redoc            200 text/html; charset=utf-8
```

后端**完全正常**，问题纯出在前端代理 + iframe 相对路径解析的相互作用。

### 2.4 为什么 dev 环境的 `http://127.0.0.1:9099/proxy-docs` 直访正常但走 iframe 翻车

> 直访 `9099/proxy-docs`：浏览器地址栏 host 是 `127.0.0.1:9099`，swagger HTML 里的 `'/openapi.json'` 解析为 `http://127.0.0.1:9099/openapi.json`（**同源**），由后端直接返回 200 → ✓
>
> 走 iframe `localhost:8080/dev-api/proxy-docs`：浏览器地址栏 host 是 `127.0.0.1:8080`，但 swagger HTML 是从 `8080` 服务代理拿到的（HTTP 内容体来自 9099，但 URL 仍是 8080 域），`'/openapi.json'` 解析为 `http://127.0.0.1:8080/openapi.json`（**跨域到前端**，且不再带 `/dev-api` 前缀），走到 Vite SPA fallback → ✗

这就是经典的「前后端联调时 iframe + swagger/redoc 的 host 漂移陷阱」——后端服务能独立运行，但嵌进前端 dev server 的 iframe 后，相对路径发生了 base URL 重写。

---

## 3. 根因小结

| 根因 # | 描述 |
|---|---|
| 主因 | swagger UI HTML 内的 `url: '/openapi.json'` 是相对路径，而前端只有一个 `/dev-api` 代理规则，**未覆盖 swagger 内部相对路径解析到的根路径** |
| 助因 | Vite SPA fallback 拦截「非代理命中」的 GET，返回项目 `index.html`（含 MonacoEditor 内联 worker 配置） |
| 设计陷阱 | RuoYi FastAPI 默认提供「`/proxy-*` 一对镜像」URL 是为了让前端走网关代理时还能访问；但开发者**应当仅把这套 URL 当作 backend 直访用**，前端要用的话必须同时配好前端反向代理覆盖这些路径，**而不是**用 `VITE_APP_BASE_API + '/proxy-docs'` 这条拼接 |

---

## 4. 修复方案（业内规范最佳实践）

> **修复方向**：保持「前端反向代理是后端 API 边界」的一致做法，**只改前端**（Vite proxy + iframe src），**后端零改动**。
>
> - 优点：① 不依赖 `request.headers.host`（避免后端和前端 host 强耦合）；② 改动幂等、回归风险低；③ 直接访问 `9099/proxy-docs` 仍然能用（开发自检 / 生产直访都覆盖）；④ 与生产 Nginx/网关模式同源（生产 `nginx.conf` 也只用一套前缀）。
> - 替代方案 B（让 swagger HTML 用 `'/dev-api/openapi.json'` 形式的相对 URL）**否决**：要把前端 base API 前缀写进后端，破坏前后端契约。
> - 替代方案 C（用绝对 URL 把 openapi_url 注成 `http://x.x.x.x:9099/openapi.json`）**否决**：开发/生产/容器/多 IP 部署时 host 会变，配置爆炸。

### 4.1 修复执行（实际 diff）

#### `vite.config.js`：扩展 proxy 规则

```46:82:ruoyi-fastapi-frontend/vite.config.js
      proxy: {
        // https://cn.vitejs.dev/config/#server-proxy
        // 反向代理后端 RESTful API
        '/dev-api': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/dev-api/, '')
        },
        // 反向代理后端 API 文档相关路径（vite.config.js 详解见
        // docs/04-开发/DEBUG/swagger-ui-relative-openapi-yaml-exception-2026-07-11.md）
        //
        // 为什么需要单独代理这些路径：
        //   swagger UI / redoc HTML 内部声明 openapiUrl='/openapi.json'（相对路径），
        //   iframe src='/dev-api/proxy-docs' 内浏览器解析该相对 URL 时，根 host 仍是
        //   前端 dev server，无法被 '/dev-api' 模式匹配 → 走 SPA fallback 拿到
        //   index.html，被 swagger-ui 当 openapi JSON 解析 → YAMLException。
        //   故把后端 docs 路由直接挂在 '/dev-api' 之外，由 Vite 原样转发（rewrite 保持原路径）：
        '/proxy-docs': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        },
        '/proxy-openapi.json': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        },
        '/proxy-redoc': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        },
        // swagger/redoc HTML 内部使用相对路径 '/openapi.json' 加载 schema，
        // iframe 内浏览器把它解析为前端 host 的根路径 '/openapi.json'，
        // 因此需要把 '/openapi.json' 也代理到后端，否则会走 SPA fallback 返回 index.html。
        '/openapi.json': {
          target: 'http://127.0.0.1:9099',
          changeOrigin: true
        }
      }
```

要点：
1. 新增 `/proxy-docs`、`/proxy-openapi.json`、`/proxy-redoc`、`/openapi.json` 四条**不带 rewrite** 的代理规则（原样转发路径）。
2. **没有 rewrite**：因为这些路径直接就是后端的真实路径，不需要去掉前缀。
3. **为什么单独代理 `/openapi.json`**：swagger UI HTML 内 `url:'/openapi.json'` 是 iframe 内相对根解析目标，与 `/dev-api/openapi.json`（被 `/dev-api` 规则接管）**是两个不同的 URL 路径**，必须显式覆盖。

#### `src/views/tool/swagger/index.vue`：iframe src 不再走 `/dev-api`

```1:18:ruoyi-fastapi-frontend/src/views/tool/swagger/index.vue
<template>
  <i-frame v-model:src="url"></i-frame>
</template>

<script setup>
import iFrame from '@/components/iFrame'

// 直接走 '/proxy-docs'（不走 '/dev-api' 前缀），原因见
// docs/04-开发/DEBUG/swagger-ui-relative-openapi-yaml-exception-2026-07-11.md：
// 走 '/dev-api/proxy-docs' 时，swagger UI HTML 内的相对路径 '/openapi.json' 会被
// iframe 浏览器解析为 'http://<frontend-host>/openapi.json'（丢失 /dev-api 前缀），
// 走到 Vite SPA fallback 而非后端 → 触发 YAMLException。
// 因此 vite.config.js 中把 '/proxy-docs'、'/openapi.json'、'/proxy-openapi.json'
// 都做了同源代理，这里直接用 '/proxy-docs' 让整条链路走同一套代理规则。
const url = ref('/proxy-docs')
</script>
```

要点：
1. 不再拼接 `VITE_APP_BASE_API` —— 让 URL 与所有环境（dev / staging / docker / production）的 base API 前缀解耦。
2. 生产 Nginx 反向代理同样适用此模式（详见 §5.2 部署侧要求）。

### 4.2 修复后请求链路

```
[浏览器]
  GET /proxy-docs                                                      (1)
[Vite]
  命中 '/proxy-docs' 规则 → 转发 http://127.0.0.1:9099/proxy-docs      (2)
[FastAPI]
  返回 swagger UI HTML（含 SwaggerUIBundle({ url: '/openapi.json' })）(3)
[iframe 内 swagger-ui-bundle.js]
  fetch('/openapi.json')  → 解析为 http://127.0.0.1:8080/openapi.json (4)
[Vite]
  命中 '/openapi.json' 规则 → 转发 http://127.0.0.1:9099/openapi.json  (5)
[FastAPI]
  返回 347 KB 合法 OpenAPI JSON → 解析成功 ✓                            (6)
```

---

## 5. 验证

### 5.1 dev 模式验证

```bash
# 1) 确认后端进程正常
ps aux | grep -E "uvicorn|fastapi" | grep -v grep

# 2) 启动前端 dev server
cd /Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-frontend
npm run dev     # 监听 80（如已占用会自动 +1，本机此次观察到 8080）

# 3) 浏览器 DevTools Network 面板检查「系统接口」页面：
#    - 第一个请求 /proxy-docs                  200  text/html
#    - 第二个请求 /openapi.json               200  application/json（347 KB）
#    - 控制台无 YAMLException
#    - 页面正常显示 OpenAPI 接口列表
```

### 5.2 部署侧要求（Nginx / 网关）

生产部署若使用 Nginx 反向代理（参考 `docker-compose.my.yml` 与部署规范），需要确保**与 dev Vite proxy 等价的规则**：

```nginx
# 推荐做法：docs 路径走和 /dev-api 不同的 location，但同样指到后端
location /proxy-docs          { proxy_pass http://backend:9099; proxy_set_header Host $host; }
location /proxy-openapi.json  { proxy_pass http://backend:9099; proxy_set_header Host $host; }
location /proxy-redoc         { proxy_pass http://backend:9099; proxy_set_header Host $host; }
location /openapi.json        { proxy_pass http://backend:9099; proxy_set_header Host $host; }
location /prod-api/           {
    proxy_pass http://backend:9099/;
    proxy_set_header Host $host;
    rewrite ^/prod-api/(.*)$ /$1 break;
}
```

> 注意：与 Vite dev 不同，生产**前端页面 + API 文档共用同一 Nginx 域名**，因此 iframe 内 `/openapi.json` 解析的 host 与 iframe src host 一致，**不会**重蹈 dev 模式 host 漂移陷阱。
> 但仍建议保留这些 location，避免有人把 swagger UI HTML 直接挂到不同子域（如 `api.example.com`），或后端因 `app_disable_swagger` 等原因另接 CDN。

### 5.3 回归扫描（自动）

```bash
# 全仓扫描是否还有「拼 VITE_APP_BASE_API + '/proxy-...'」的反模式
rg -n 'VITE_APP_BASE_API\s*\+\s*["\047](/proxy-|/docs|/redoc|/openapi)' \
   ruoyi-fastapi-frontend/src

# 期望输出：0 行（本次修复已彻底把 swagger 工具菜单脱离 VITE_APP_BASE_API 拼接）
```

---

## 6. 后续启示

- **前端反向代理 ≠ 只代理业务 API**：iframe 嵌入的 swagger / redoc / yapi / apifox 等工具页，其 HTML 内相对路径（schema URL、oauth2-redirect）会跨出 `VITE_APP_BASE_API` 边界，必须单独建代理规则或明确文档化"该类工具页的相对路径解析行为"。
- **避免在 `view` 层用 `import.meta.env.VITE_APP_BASE_API + '/proxy-*'` 模式**：这条拼接既破坏前后端契约、又依赖于「前端 base 恰好等于后端 gateway 前缀」的隐含假设。工具菜单的 URL 应当是**前端自己拥有的路由路径**（如 `/proxy-docs`），由反向代理决定去哪。
- **保留后端 `/proxy-*` 镜像路由**：本次修复不删 `server_util.py` 里的 `_PROXY_*_URL` 与 `custom_api_docs_router`，因为这些 URL 仍是：
  ① 后端独立运行时的访问入口（如 k8s readinessprobe、sre 自检）；
  ② 前端 Vite dev / Nginx 网关的反向代理目标。
  这套 `/proxy-*` 设计是 RuoYi FastAPI 的官方约定（详见 `docs/04-开发/ARD/ADR-架构决策记录.md` 中关于「API 文档统一入口」的条目），**不要为了修这个 bug 反向把后端镜像路由删掉**。
- **台账「前后端联调验收项」需补一条**：当前台账（`docs/04-开发/开发进度台账.md`）验收维度是「按钮/字段对齐/视觉/接口契约/主题适配」5 维，建议追加第 6 维「**工具页面 iframe 跨域契约验收**」：进入「系统接口」、「代码生成」、「druid 监控」等 iframe 类工具页，验证页内实际能渲染内容（不只是 iframe src 200）。

---

## 关联文件

- `ruoyi-fastapi-frontend/vite.config.js:46-82` — 新增 4 条 docs proxy 规则
- `ruoyi-fastapi-frontend/src/views/tool/swagger/index.vue:1-18` — iframe src 改为 `/proxy-docs`（脱离 `VITE_APP_BASE_API`）
- `ruoyi-fastapi-backend/utils/server_util.py:24-31, 230-240` — swagger UI HTML 内部声明 `url: '/openapi.json'`（相对路径，**保留不变**，是后端独立运行入口，不能动）
- `ruoyi-fastapi-frontend/.env.development:8` — `VITE_APP_BASE_API = '/dev-api'`（保留不变，仅 swagger 工具菜单脱离它）
- `docs/04-开发/开发进度台账.md` — 待追加「工具页面 iframe 跨域契约验收」条目
- `docs/04-开发/ARD/ADR-架构决策记录.md` — 已有「API 文档统一入口」相关条目，本次修复不与之冲突，可在 ADR 旁补充一句「前端代理必须覆盖 `/proxy-*` 与 `/openapi.json`」

## 关联已有 DEBUG

- `docs/04-开发/DEBUG/approval-dark-mode-hardcoded-colors-2026-07-11.md` — 同类「跨层级契约未对齐」问题（业务页样式 vs 暗色主题），可参考其「修复执行 + 同步 ADR 约束 + 后续启示」三段式。
- `docs/04-开发/DEBUG/role-sort-conflict-2026-07-11.md` — 同类「默认值与本项目语义冲突但脚本作者没改」问题。
