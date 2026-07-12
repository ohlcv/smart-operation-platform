#!/usr/bin/env python3
"""本地 pre-commit 钩子：ORM 改动时强制检查 alembic 迁移。

规则：
  ① 检测 ruoyi-fastapi-backend/module_admin/entity/do/*.py 或
     ruoyi-fastapi-backend/module_biz/entity/do/*.py 的改动
  ② 若 ORM 改动但 alembic/versions/*.py 未改动 → 报错提醒
  ③ 若 ORM 改动且 alembic 改动 → 通过
  ④ 提供 --no-verify 跳过
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORM_GLOB_ADMIN = 'ruoyi-fastapi-backend/module_admin/entity/do/'
ORM_GLOB_BIZ = 'ruoyi-fastapi-backend/module_biz/entity/do/'
MIG_GLOB = 'ruoyi-fastapi-backend/alembic/versions/'

ORM_GLOBS = (ORM_GLOB_ADMIN, ORM_GLOB_BIZ)


def run(cmd, **kw):
    return subprocess.check_output(cmd, cwd=str(ROOT), **kw).decode()


def main():
    try:
        staged = run(['git', 'diff', '--cached', '--name-only'])
    except subprocess.CalledProcessError as e:
        print(f'⚠️  无法读取 git staged files: {e}')
        return 0

    files = [f for f in staged.splitlines() if f.strip()]

    orm_changed = [f for f in files if any(f.startswith(g) for g in ORM_GLOBS)
                   and f.endswith('.py')]
    mig_changed = [f for f in files if f.startswith(MIG_GLOB) and f.endswith('.py')]

    if orm_changed and not mig_changed:
        print('❌ ORM 模型改动但 alembic 迁移未改动！')
        print('')
        print('   ORM 改动文件：')
        for f in orm_changed:
            print(f'     - {f}')
        print('')
        print('   请二选一：')
        print('   ① 写 alembic 迁移（推荐）：')
        print('        cd ruoyi-fastapi-backend')
        print('        alembic -c alembic.ini revision --autogenerate -m "describe change"')
        print('        # 检查生成文件 → git add ruoyi-fastapi-backend/alembic/versions/0005_xxx.py')
        print('        git commit -m "..."')
        print('')
        print('   ② 仅改 nullable/default 这种元数据，autogenerate 不会检测：')
        print('        直接把 baseline 改了即可（baseline 永远会跑）')
        print('        然后 git commit --no-verify 跳过本钩子')
        print('')
        print('   ③ 确认改动无影响数据库：')
        print('        git commit --no-verify')
        print('')
        print('   💡 详细文档：docs/04-开发/DEBUG/orm-vs-alembic-sync-2026-07-12.md')
        return 1

    if orm_changed and mig_changed:
        print('✅ ORM + alembic 同步改动')

    return 0


if __name__ == '__main__':
    sys.exit(main())