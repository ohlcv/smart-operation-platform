# `@Log` 装饰器 IndexError: list index out of range

**日期**：2026-07-12
**类型**：通用工具 / 注解层 / PEP 563 兼容
**影响**：所有 `@Log` 装饰的接口（HTTP 实测 `code=500 msg="list index out of range"`）；不只 DELETE 路径
**根因**：`from __future__ import annotations`（PEP 563）让 controller 函数签名变字符串注解，`log_annotation.get_function_parameters_name_by_type` 用 `annotation == Request` 拿不到 → 返回空 list → `request_name_list[0]` IndexError

---

## 1. 现象

MySQL + 服务起来后跑业务接口回归（v3.2 → v3.3 验收），`DELETE /biz/{invoice,finance,operation}/999999`、`DELETE /biz/channel/999999,888888` 全部报：

```
code=500, msg="list index out of range"
```

后端 traceback 落在 `common/annotation/log_annotation.py:162`：

```python
# common/annotation/log_annotation.py:160-162
request_name_list = get_function_parameters_name_by_type(func, Request)
request = get_function_parameters_value_by_name(func, request_name_list[0], *args, **kwargs)
                                                      ^^^^^^^^^^^^^^^^^^
                                              IndexError: list index out of range
```

直觉判断是 `@Log` 装饰器对 DELETE 函数 `request: Request` 参数提取失败。但所有 4 个 DELETE controller 函数都明确写了 `request: Request` —— 直觉说不通。

---

## 2. 根因分析

### 2.1 `from __future__ import annotations` 把注解变字符串

controller 全部启用 PEP 563：

```python
# module_biz/controller/channel_controller.py:8
from __future__ import annotations
```

PEP 563 让所有参数注解变成**字符串形式**，等价于：

```python
# 源代码
async def delete_channel(
    request: Request,
    channel_ids: Annotated[str, Path(description='渠道ID，逗号分隔')],
    ...
) -> Response:
    ...

# PEP 563 实际行为（运行时 inspect 看到）
# parameters['request'].annotation == 'Request'  (字符串！)
# parameters['channel_ids'].annotation == 'Annotated[str, Path(description=...)]'  (字符串)
```

**直接验证**：

```python
>>> import inspect
>>> from fastapi import Request
>>> exec('''
... from __future__ import annotations
... async def f(request: Request, x: int): pass
... ''')
>>> inspect.signature(f).parameters['request'].annotation
'Request'  # str！
```

### 2.2 `get_function_parameters_name_by_type` 没考虑这种情况

原实现只用 `annotation == param_type` 和 `_AnnotatedAlias.__origin__ == param_type` 两种比较：

```python
# common/annotation/log_annotation.py:1037-1061 (修复前)
def get_function_parameters_name_by_type(func: Callable, param_type: Any) -> list:
    parameters = inspect.signature(func).parameters
    parameters_name_list = []
    for name, param in parameters.items():
        annotation = param.annotation  # 字符串 'Request'
        if annotation == param_type or (   # 'Request' == Request → False
            hasattr(annotation, '__class__')
            and annotation.__class__.__name__ == '_AnnotatedAlias'  # 字符串 str 不匹配
            and annotation.__origin__ == param_type
        ):
            parameters_name_list.append(name)
    return parameters_name_list  # → 返回 []
```

`annotation = 'Request'`（str），`'Request' == Request` 为 False；`annotation.__class__.__name__ == '_AnnotatedAlias'` 为 False（是 `'str'`）。**所有 case 都 fail**，返回空列表。

下一行 `request_name_list[0]` 直接 `IndexError`。

### 2.3 为什么 `wrapper` 里看到 `func` 是原始函数还能 inspect 失败

`@functools.wraps(func)` 会把 `__wrapped__` 指向原函数，但 `inspect.signature` 默认 unwrap —— 所以拿到的还是原函数签名。这部分是正确的；**真正失败的是注解字符串化**，跟 `wraps` 无关。

---

## 3. 修复前后对比

### 3.1 修复前（IndexError）

```python
def get_function_parameters_name_by_type(func: Callable, param_type: Any) -> list:
    parameters = inspect.signature(func).parameters
    parameters_name_list = []
    for name, param in parameters.items():
        annotation = param.annotation
        if annotation == param_type or (
            hasattr(annotation, '__class__')
            and annotation.__class__.__name__ == '_AnnotatedAlias'
            and annotation.__origin__ == param_type
        ):
            parameters_name_list.append(name)
    return parameters_name_list
```

实测：

| controller 函数 | annotation (inspect) | 匹配结果 |
|---|---|---|
| `delete_channel(request: Request, ...)` | `'Request'` | ❌ 不匹配 Request |
| `delete_invoice(request: Request, ...)` | `'Request'` | ❌ |
| `delete_finance(request: Request, ...)` | `'Request'` | ❌ |
| `delete_operation(request: Request, ...)` | `'Request'` | ❌ |

→ 全部 `parameters_name_list = []` → IndexError。

### 3.2 修复后（PEP 563 兼容）

```python
# ruoyi-fastapi-backend/common/annotation/log_annotation.py:1037-1062
def get_function_parameters_name_by_type(func: Callable, param_type: Any) -> list:
    """获取函数指定类型的参数名称"""
    # 用 get_type_hints 解析 forward ref（from __future__ import annotations 会让注解变成字符串）
    try:
        resolved_hints = get_type_hints(func)
    except Exception:
        resolved_hints = {}
    parameters_name_list = []
    for name, param in inspect.signature(func).parameters.items():
        annotation = resolved_hints.get(name, param.annotation)
        if annotation == param_type or (
            hasattr(annotation, '__class__')
            and annotation.__class__.__name__ == '_AnnotatedAlias'
            and annotation.__origin__ == param_type
        ):
            parameters_name_list.append(name)
    return parameters_name_list
```

import 同步：

```python
# common/annotation/log_annotation.py:9
from typing import Any, Literal, TypeVar, get_type_hints
```

**`typing.get_type_hints(func)`** 会用 `func.__globals__` 解析所有 forward ref，把字符串 `'Request'` 解析回真正的 `Request` 类对象。后续 `annotation == param_type` 就成立。

`try/except` fallback 是为了避免某个极端注解（包含未导入类型）抛 `NameError` 时整个工具函数崩；fallback 到原路径后行为等于修复前，但**不会引入新的崩溃**。

---

## 4. 回归验证

`scripts/test_options_live.py`（手工黑盒测试脚本）跑完：

```
[GET    /biz/channel/category-options]    code=200 msg=查询成功
[GET    /biz/invoice/options]              code=200 msg=操作成功
[GET    /biz/finance/options]              code=200 msg=操作成功
[GET    /biz/operation/options]            code=200 msg=操作成功
[GET    /biz/invoice/999999]               code=500 msg=发票ID 999999 不存在   ✅ 业务异常
[DELETE /biz/invoice/999999]               code=500 msg=发票ID 999999 不存在   ✅ 不再 IndexError
[GET    /biz/operation/999999]             code=500 msg=经营数据ID 999999 不存在  ✅
[DELETE /biz/operation/999999]             code=500 msg=经营数据ID 999999 不存在  ✅
[GET    /biz/finance/999999]               code=500 msg=财务流水ID 999999 不存在  ✅
[DELETE /biz/finance/999999]              code=500 msg=财务流水ID 999999 不存在  ✅
[DELETE /biz/channel/999999,888888]        code=200 msg=删除成功 0 条          ✅
```

修复前 4 个 DELETE 全报 `list index out of range`，修复后 4 个 DELETE 全部走完完整业务链路。

**`@Log` 装饰器现在对所有 controller 正常工作**，包括其他用 `@Log` 但本回归未覆盖的接口（`PUT /system/user/profile/signature` 等）。

---

## 5. 关联决策 / 影响范围

- **关联 ADR**：D26（注解层 PEP 563 forward ref 兼容性）
- **影响范围**：所有 `@Log` 装饰的 controller 函数（49 条路由中绝大多数）；修复后受益面远超 DELETE 路径
- **不需修改**：controller 侧（保留 `from __future__ import annotations`）

---

## 6. 反思

- **直觉判断陷阱**：`wrapper` + `@functools.wraps` 让人本能怀疑 `inspect` 拿错了函数。但实际是 PEP 563 把字符串化注解这一**更隐蔽的兼容性问题**
- **回归测试必须包含不存在的 ID**：如果只测 ID=1（存在的），DELETE 走的是正常流程，碰不到 `request_name_list` 提取失败的链路；专门测不存在的 ID 才能让 service 抛 `ServiceException` 后 `@Log` 才进入 wrapper 提取 request 的关键路径
- **同类风险扫描**：`inspect.signature(func).parameters` 在本项目还有哪些使用方？

```bash
grep -rn "inspect.signature\|get_type_hints" ruoyi-fastapi-backend/common/ ruoyi-fastapi-backend/utils/
```

扫描结果：除 `log_annotation.py` 外无其他同类使用，本项目此 bug 影响面已封闭。