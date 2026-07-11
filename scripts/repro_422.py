"""复现 /biz/{channel,invoice,finance,operation}/options 的 422。

策略：用 FastAPI TestClient 直接发 HTTP 请求，避开浏览器/CORS。
拿到真实的 validation error body，定位出错字段。
"""
import asyncio
import json
import os
import sys

# 必须先加载 .env.merged（合并 .env.dev + .env.local），与 uvicorn 启动一致
from dotenv import load_dotenv

sys.path.insert(0, '/Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend')
load_dotenv('/Users/meow/Desktop/Project/smart-operation-platform/ruoyi-fastapi-backend/.env.merged', override=True)

# 强制使用与生产一致的端口
os.environ['DB_PORT'] = '13306'
os.environ['REDIS_PORT'] = '16379'


async def step1_disable_captcha():
    """关闭验证码（DB + Redis）。"""
    import redis
    from config.get_db import get_db
    from sqlalchemy import text

    # Redis
    r = redis.Redis(host='127.0.0.1', port=16379, db=0)
    r.set('sys_config:sys.account.captchaEnabled', 'false')

    # DB
    gen = get_db()
    db = await gen.__anext__()
    try:
        await db.execute(text("UPDATE sys_config SET config_value='false' WHERE config_key='sys.account.captchaEnabled'"))
        await db.commit()
        print('[OK] captcha disabled')
    finally:
        await db.close()


def step2_login_and_test():
    """用 TestClient 登录 → 拿 token → 调 4 个 /options 接口。"""
    from fastapi.testclient import TestClient
    import app  # 触发 app.py 加载

    client = TestClient(app.app)

    # 1. 登录
    login_res = client.post(
        '/login',
        data={'username': 'admin', 'password': 'admin123'},
    )
    print(f'[LOGIN] {login_res.status_code} {login_res.json()}')
    if login_res.status_code != 200 or login_res.json().get('code') != 200:
        return
    token = login_res.json().get('token', '')
    if not token:
        print('[FAIL] no token in login response')
        return
    print(f'[OK] token: {token[:30]}...')

    # 2. 调 4 个 options
    endpoints = [
        'GET /biz/channel/category-options',
        'GET /biz/invoice/options',
        'GET /biz/finance/options',
        'GET /biz/operation/options',
    ]
    import requests as _r  # noqa
    for ep in endpoints:
        method, url = ep.split(' ')
        res = client.request(method, url, headers={'Authorization': f'Bearer {token}'})
        body = res.text
        try:
            j = res.json()
        except Exception:
            j = {'_raw': body[:500]}
        # 截短 detail
        if isinstance(j, dict) and 'detail' in j:
            j['detail'] = json.dumps(j['detail'], ensure_ascii=False)[:300]
        print(f'\n[{ep}] status={res.status_code}')
        print(json.dumps(j, ensure_ascii=False, indent=2)[:800])


async def main():
    await step1_disable_captcha()
    step2_login_and_test()


asyncio.run(main())
