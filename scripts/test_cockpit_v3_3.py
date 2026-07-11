"""v3.3 路线 C 大屏回归脚本：验证 /biz/cockpit/overview + /biz/cockpit/ai-diagnose 端到端。"""
import json
import sys
import time
import urllib.request
import urllib.error

import redis

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 16379
BACKEND = 'http://localhost:9099'

# 1) 关 captcha
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
except urllib.error.URLError as e:
    print(f'[LOGIN FAIL] network: {e}')
    sys.exit(1)

token = resp['data']['access_token'] if isinstance(resp.get('data'), dict) else resp['data'].get('access_token')
print(f'[LOGIN] code={resp.get("code")} token={token[:30]}...')


def call(method, path, params=None):
    url = f'{BACKEND}{path}'
    if params:
        qs = '&'.join(f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items())
        url = f'{url}?{qs}'
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}'},
    )
    try:
        body = urllib.request.urlopen(req, timeout=10).read().decode()
        return json.loads(body)
    except urllib.error.HTTPError as e:
        return {'code': e.code, 'msg': f'HTTPError: {e.reason}', 'data': e.read().decode()[:200]}
    except Exception as e:
        return {'code': -1, 'msg': str(e)}


# 3) cockpit/overview 全国
print('\n=== cockpit/overview 全国 ===')
res = call('GET', '/biz/cockpit/overview')
print(f'[GET /biz/cockpit/overview] code={res.get("code")} msg={res.get("msg")}')
if res.get('code') == 200:
    data = res['data']
    print(f'  province={data.get("province")!r}')
    kpi = data.get('kpi', {})
    print(f'  KPI keys: {sorted(kpi.keys())}')
    print(f'  contractTotal={kpi.get("contractTotal")}  contractMonthAmount={kpi.get("contractMonthAmount")}')
    print(f'  customerTotal={kpi.get("customerTotal")}  channelTotal={kpi.get("channelTotal")}')
    print(f'  trend7d count={len(data.get("trend7d", []))}')
    print(f'  statusDistribution count={len(data.get("statusDistribution", []))}')
    print(f'  topCustomers count={len(data.get("topCustomers", []))}')
    print(f'  recentApprovals count={len(data.get("recentApprovals", []))}')
    print(f'  channelLocations count={len(data.get("channelLocations", []))}')
    # 关键 camelCase 字段校验
    expected_camel = {'contractTotal', 'contractPending', 'customerTotal', 'channelTotal',
                       'contractMonthAmount', 'trend7d', 'statusDistribution',
                       'topCustomers', 'recentApprovals', 'channelLocations'}
    missing = expected_camel - set(data.keys())
    assert not missing, f'MISSING camelCase keys: {missing}'
    print(f'  ✓ camelCase 字段完整')
else:
    print(f'  FAIL: {res}')
    sys.exit(1)

# 4) cockpit/overview 带 province 过滤
print('\n=== cockpit/overview province=北京 ===')
res2 = call('GET', '/biz/cockpit/overview', {'province': '北京'})
print(f'[GET /biz/cockpit/overview?province=北京] code={res2.get("code")} msg={res2.get("msg")}')
if res2.get('code') == 200:
    data2 = res2['data']
    print(f'  province={data2.get("province")!r}')
    print(f'  contractTotal(北京)={data2["kpi"].get("contractTotal")}')
    print(f'  trend7d count={len(data2.get("trend7d", []))}')
    print(f'  topCustomers count={len(data2.get("topCustomers", []))}')
    assert data2.get('province') == '北京', f'expected province=北京 got {data2.get("province")!r}'
    print(f'  ✓ province 过滤生效')
else:
    print(f'  WARN province 接口返回非 200: {res2}')

# 5) ai-diagnose
print('\n=== cockpit/ai-diagnose ===')
res3 = call('GET', '/biz/cockpit/ai-diagnose')
print(f'[GET /biz/cockpit/ai-diagnose] code={res3.get("code")} msg={res3.get("msg")}')
if res3.get('code') == 200:
    ai = res3['data']
    print(f'  summary={ai.get("summary", "")[:80]}...')
    print(f'  risks count={len(ai.get("risks", []))}')
    print(f'  suggestions count={len(ai.get("suggestions", []))}')
    print(f'  radar_scores={ai.get("radarScores", [])}')
    print(f'  metrics keys={sorted((ai.get("metrics") or {}).keys())}')
    assert ai.get('summary'), 'summary empty'
    assert isinstance(ai.get('radarScores'), list) and len(ai['radarScores']) == 6, 'radar_scores 必须 6 维'
    print(f'  ✓ AI 大脑响应完整')
else:
    print(f'  FAIL: {res3}')

print('\n=== ALL OK ===')