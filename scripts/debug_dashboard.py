"""排查仪表盘空白页：登录 → /getRouters → /biz/dashboard/overview

用法：python scripts/debug_dashboard.py
"""
import json
import sys
from urllib import request, error, parse

BASE = 'http://localhost:9099'


def _req(method, path, token=None, body=None, is_form=False, timeout=10):
    url = f"{BASE}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        if is_form:
            data = parse.urlencode(body).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def try_login(username, password):
    _, cap = _req("GET", "/captchaImage")
    try:
        uuid = json.loads(cap).get("uuid", "")
    except Exception:
        uuid = ""
    form = {
        "username": username,
        "password": password,
        "code": "",
        "uuid": uuid or "",
    }
    code, body = _req("POST", "/login", body=form, is_form=True)
    print(f"[login {username}] HTTP {code}")
    if code != 200:
        print(f"  body: {body[:300]}")
        return None
    try:
        obj = json.loads(body)
    except Exception:
        print(f"  非 JSON: {body[:300]}")
        return None
    if obj.get("token"):
        return obj["token"]
    d = obj.get("data")
    if isinstance(d, dict):
        return d.get("token") or d.get("access_token")
    if isinstance(d, str) and d:
        return d
    return None


def get_routers(token):
    code, body = _req("GET", "/getRouters", token=token)
    print(f"\n[getRouters] HTTP {code}")
    if code != 200:
        print(f"  body: {body[:500]}")
        return
    data = json.loads(body).get("data", [])
    print(f"  共 {len(data)} 个顶级路由")
    for r in data:
        children = r.get("children") or []
        print(f"  - name={r.get('name')!r} path={r.get('path')!r} component={r.get('component')!r} hidden={r.get('hidden')} children={len(children)}")
        for c in children:
            print(f"      child: path={c.get('path')!r} component={c.get('component')!r}")
    print("\n  找 dashboard 相关菜单:")
    found = False
    for r in data:
        rp = (r.get("path") or "").lower()
        rc = (r.get("component") or "").lower()
        if "dashboard" in rp or "dashboard" in rc:
            print(f"  ★ FOUND 顶级: path={r.get('path')!r} component={r.get('component')!r}")
            print(f"    raw: {json.dumps(r, ensure_ascii=False)[:600]}")
            found = True
        for c in (r.get("children") or []):
            cp = (c.get("path") or "").lower()
            cc = (c.get("component") or "").lower()
            if "dashboard" in cp or "dashboard" in cc:
                print(f"  ★ FOUND 子: path={c.get('path')!r} component={c.get('component')!r}")
                print(f"    raw: {json.dumps(c, ensure_ascii=False)[:600]}")
                found = True
    if not found:
        print("  ⚠️ 路由列表中没找到 dashboard 相关菜单！")


def call_dashboard(token):
    code, body = _req("GET", "/biz/dashboard/overview", token=token)
    print(f"\n[dashboard/overview] HTTP {code}")
    if code != 200:
        print(f"  body: {body[:800]}")
        return
    try:
        d = json.loads(body).get("data", {})
    except Exception:
        print(f"  非 JSON: {body[:400]}")
        return
    print(f"  顶层字段: {list(d.keys())}")
    print(f"  kpi: {d.get('kpi')}")
    print(f"  trend7d 条数: {len(d.get('trend7d') or [])}")
    print(f"  statusDistribution 条数: {len(d.get('statusDistribution') or [])}")
    print(f"  topCustomers 条数: {len(d.get('topCustomers') or [])}")
    print(f"  recentApprovals 条数: {len(d.get('recentApprovals') or [])}")
    print(f"  channelLocations 条数: {len(d.get('channelLocations') or [])}")
    print(f"  generatedAt: {d.get('generatedAt')}")


def main():
    token = None
    for u, p in [("admin", "admin123"), ("admin", "admin"), ("ry", "admin123")]:
        token = try_login(u, p)
        if token:
            break
    if not token:
        print("\n❌ 登录失败，无法继续")
        return 1
    print(f"\n✅ TOKEN 长度: {len(token)}")
    get_routers(token)
    call_dashboard(token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
