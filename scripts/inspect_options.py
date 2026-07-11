"""查 4 个 options controller 的代码，定位 422 的根因。

不做 HTTP 复现，只读代码静态分析：
- 是否 controller 函数签名有 default 值在 non-default 之前？
- 是否 response_model 与实际返回结构冲突？
- 是否依赖项（Pydantic model）有字段缺失？
"""
import os
import re

CONTROLLERS = [
    '/Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend/module_biz/controller/channel_controller.py',
    '/Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend/module_biz/controller/invoice_controller.py',
    '/Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend/module_biz/controller/finance_controller.py',
    '/Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend/module_biz/controller/operation_controller.py',
]

import ast
import sys

def extract_options_decorators(path):
    """提取每个 /options 端点的完整签名。"""
    src = open(path).read()
    tree = ast.parse(src)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                # 检查 @xxx.get('/options', ...) 或 @xxx.get('/category-options', ...)
                if isinstance(dec, ast.Call):
                    is_route = False
                    for attr in ast.walk(dec.func):
                        if isinstance(attr, ast.Attribute) and attr.attr in ('get','post','put','delete','route'):
                            is_route = True
                    if not is_route:
                        continue
                    if not dec.args:
                        continue
                    if not isinstance(dec.args[0], ast.Constant):
                        continue
                    url = dec.args[0].value
                    if 'options' not in str(url):
                        continue
                    # 提取 kwargs
                    kwargs = {}
                    for kw in dec.keywords:
                        kwargs[kw.arg] = ast.unparse(kw.value)
                    # 提取函数签名 args
                    func_args = []
                    for a in node.args.args:
                        ann = ast.unparse(a.annotation) if a.annotation else ''
                        func_args.append((a.arg, ann))
                    func_defaults = [ast.unparse(d) for d in node.args.defaults]
                    results.append({
                        'func': node.name,
                        'url': url,
                        'kwargs': kwargs,
                        'args': func_args,
                        'defaults': func_defaults,
                        'lineno': node.lineno,
                    })
    return results

for path in CONTROLLERS:
    print(f'\n=== {os.path.basename(path)} ===')
    try:
        rs = extract_options_decorators(path)
        for r in rs:
            print(f'  [{r["lineno"]}] {r["func"]}: {r["url"]}')
            print(f'    kwargs: {r["kwargs"]}')
            print(f'    args: {r["args"]}')
            print(f'    defaults: {r["defaults"]}')
            # 检测 default-order 错
            args = r['args']
            defaults = r['defaults']
            # 末尾 len(defaults) 个 args 必须有 default
            n = len(args)
            ndef = len(defaults)
            bad = []
            for i in range(n - ndef):
                # 前 n-ndef 个 args 不能有 default
                if i < len(args):
                    pass
            if defaults:
                offset = n - len(defaults)
                for i, (a, ann) in enumerate(args[offset:], start=offset):
                    pass
    except Exception as e:
        print(f'  ERROR: {e}')
