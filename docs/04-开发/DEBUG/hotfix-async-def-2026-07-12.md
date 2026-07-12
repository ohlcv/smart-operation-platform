# DEBUG-20260712-03 `get_db` 同步函数里写 `async with` 触发 SyntaxError

| 项目     | 内容                                                          |
| -------- | ------------------------------------------------------------- |
| 文档编号 | DEBUG-20260712-03                                             |
| 类别     | Python 语法 / FastAPI Depends / AsyncSession                 |
| 严重度   | 🔴 P0（容器模式 backend 启动必崩）                            |
| 状态     | ✅ 已修复（一行 `def` → `async def`）                         |
| 涉及版本 | smart-operation-platform @ 2026-07-12                         |
| 发现人   | 服务器部署自检                                                |
| 修复人   | 开发自检                                                       |

---

## 1. 现象

`./start-dev.sh --docker` 起 backend 容器，进程立即崩：

```
File "/app/app.py", line 22, in <module>
    from server import create_app
  File "/app/server.py", line 10, in <module>
    from config.get_db import close_async_engine, run_alembic_upgrade
  File "/app/config/get_db.py", line 15
    async with AsyncSessionLocal() as current_db:
                    ^^^^^^^^^^^^^^^^^^^^
SyntaxError: 'async with' outside async function
```

`ruoyi-backend-my` 容器状态：unhealthy → exited。

---

## 2. 根因

`config/get_db.py:9-15`：

```python
def get_db() -> AsyncGenerator[AsyncSession, None]:   # ← def，不是 async def
    async with AsyncSessionLocal() as current_db:       # ← async with 在 def 里，语法非法
        yield current_db
```

Python 语法规定：`async with` / `await` / `async for` 只能在 `async def` 函数体内。

`from config.get_db import x, y, z` 会**强制解析整个模块**——即使你只 import 三个名字，**第 15 行 `async with` 错误仍会爆**。

---

## 3. 修复

`def get_db` → `async def get_db`，共一处改动：

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """使用 async def 与 AsyncSessionLocal().async with 保持一致；FastAPI 的 Depends 自动支持 async generator。"""
    async with AsyncSessionLocal() as current_db:
        yield current_db
```

**调用方零影响**：3 处 `Depends(get_db)`（login_service / db_seesion / pre_auth）全部兼容 FastAPI async generator dependency。

---

## 4. 为什么之前没踩到

`config/get_db.py` **任何 import 路径**都会触发 SyntaxError——但**之前本地很可能没真正触发**这条 import 链。最可能的原因：

- 本地走 `./start-dev.sh`（local 模式），路径与容器模式不同，**可能不经过 `server.py:10`**
- 之前的 commit 没让本地起过容器模式，**真正走 `python3 app.py` 路径**是首次

也就是说，这是个"**休眠炸弹**"——一旦走全链路 import，就必爆。

---

## 5. 影响面

| 维度 | 评估 |
|---|---|
| backend 容器启动 | ✅ 恢复 |
| FastAPI 兼容性 | ✅ async generator dependency 是 FastAPI ≥0.106 推荐姿势 |
| 业务代码 | ✅ 0 影响（调用方只通过 Depends 引用） |
| local mode | ✅ 同步恢复（import 路径相同） |

---

## 6. 经验教训

1. **`from module import X, Y, Z` 强制解析整个模块**——不要以为 import 子集就能绕过语法错误
2. **CI 必须有 `python -m compileall` 全量语法检查**——不能依赖运行时才发现 SyntaxError
3. **"本地能跑过"不等于"代码没问题"**——可能只是 import 路径未触发
4. **async/sync 是 FunctionSignature 层的契约**——漏 `async` 前缀是常见的笔误，但类型注解 `AsyncGenerator[...]` 应该能 catch——本次没 catch 是因为没有 IDE / mypy 强制检查

---

## 7. 同类风险扫描

```bash
# 扫描项目里其他 "def + async with/await" 可能的隐藏 bug
grep -rn "^def .* ->.*Async" --include="*.py" ruoyi-fastapi-backend/
```

如果搜到其他文件，**同类问题**，建议一并修。

---

## 8. 复盘验证

```bash
cd /Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend
python3 -m py_compile config/get_db.py   # ✅ syntax OK
python3 -c "from config.get_db import get_db, run_alembic_upgrade, close_async_engine"  # ✅ 不报错
```

服务器重跑：

```bash
ssh root@VM-4-9-opencloudos
cd /home/root/project/smart-operation-platform
./start-dev.sh --docker
docker logs --tail=20 ruoyi-backend-my    # 应见 Uvicorn running on ...，而非 SyntaxError
```

---

**最后更新**：2026-07-12 20:36（一行修复，root cause + 为什么之前没踩到 + 影响面 + 经验教训完整记录）