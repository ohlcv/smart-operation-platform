"""在线复现 4 个 options 接口 + 回归 detail/delete。"""
import json
import sys
import time
import urllib.request
import urllib.error

import redis

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 16379
BACKEND = 'http://localhost:9099'

# 1) 关 captcha（DB=2 是 uvicorn 启动用的 db）
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=2, decode_responses=True)
r.set('sys_config:sys.account.captchaEnabled', 'false')
print(f'[OK] captcha disabled on db=2, current value: {r.get("sys_config:sys.account.captchaEnabled")}')

# 2) 登录
login_req = urllib.request.Request(
    f'{BACKEND}/login',
    data=b'username=admin&password=admin123',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
)
try:
    body = urllib.request.urlopen(login_req, timeout=5).read().decode()
    resp = json.loads(body)
    if resp.get('code') != 200:
        print(f'[LOGIN FAIL] {resp}')
        sys.exit(1)
    token = resp.get('token', '')
    print(f'[LOGIN] code=200 token={token[:30]}...')
except urllib.error.HTTPError as e:
    print(f'[LOGIN FAIL] {e.code} {e.read().decode()[:500]}')
    sys.exit(1)

# 3) 测试接口
endpoints = [
    ('GET', '/biz/channel/category-options'),
    ('GET', '/biz/invoice/options'),
    ('GET', '/biz/finance/options'),
    ('GET', '/biz/operation/options'),
    # 回归：ID=1 应存在（任何一张表都有首条）；ID=999999 应触发"不存在"业务异常
    ('GET', '/biz/invoice/1'),
    ('GET', '/biz/invoice/999999'),
    ('DELETE', '/biz/invoice/999999'),
    ('GET', '/biz/operation/1'),
    ('GET', '/biz/operation/999999'),
    ('DELETE', '/biz/operation/999999'),
    ('GET', '/biz/finance/1'),
    ('GET', '/biz/finance/999999'),
    ('DELETE', '/biz/finance/999999'),
    ('DELETE', '/biz/channel/999999,888888'),
]

for method, url in endpoints:
    req = urllib.request.Request(
        f'{BACKEND}{url}',
        headers={'Authorization': f'Bearer {token}'},
        method=method,
    )
    try:
        body = urllib.request.urlopen(req, timeout=5).read().decode()
        resp = json.loads(body)
        code = resp.get('code')
        msg = resp.get('msg', '')
        data = resp.get('data')
        print(f'[{method} {url}] code={code} msg={msg[:80]}')
        if code == 200 and isinstance(data, dict) and 'rows' in data:
            print(f'  rows: {len(data["rows"])} items')
        elif code == 200 and isinstance(data, dict):
            print(f'  data keys: {list(data.keys())}')
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'[{method} {url}] HTTP {e.code}: {body[:300]}')
    except Exception as e:
        print(f'[{method} {url}] ERR: {e}')
    time.sleep(0.05)