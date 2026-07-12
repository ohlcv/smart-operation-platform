# Pre-commit 钩子

保护 ORM 改动时同步 alembic 迁移，避免运行时 1054 Unknown column 错误。

## 文件结构

```
项目根/
├── .pre-commit-config.yaml                                  # pre-commit 框架配置
└── ruoyi-fastapi-backend/
    └── .pre-commit-hooks/
        ├── README.txt                                        # 本文件说明
        └── check_orm_alembic_sync.py                        # 钩子逻辑
```

## 安装（一次性）

需要 Python 3.6+：

```bash
# 1. 安装 pre-commit 框架
pip install pre-commit

# 2. 安装钩子（会在 .git/hooks/pre-commit 注册）
cd /Users/meow/Desktop/Project/smart-operation-platform
pre-commit install
```

完成后**所有 `git commit` 都会先跑这个钩子**。

## 触发规则

| 你改了 | alembic 改了？ | 结果 |
|---|---|---|
| 无 ORM 改动 | — | ✓ 通过 |
| ORM 改动 | ✓ 也改 | ✓ 通过（打印 "ORM + alembic 同步改动"） |
| ORM 改动 | ✗ 没改 | ❌ 拒绝 commit（exit 1） |

## 跳过方法

钩子拒绝 commit 时的三种合法处理：

```bash
# ① 推荐：写 alembic 迁移
cd ruoyi-fastapi-backend
alembic -c alembic.ini revision --autogenerate -m "describe your change"
# 检查生成的迁移 → git add alembic/versions/0005_xxx.py
git commit -m "..."

# ② 如果只改 nullable/server_default 等元数据（autogenerate 检测不到）：
# 直接改 alembic/versions/0001_baseline_sys_ruoyi.py 即可，baseline 永远会跑
# 但因为 ORM 文件不在 staged，所以钩子不会触发
git add ruoyi-fastapi-backend/alembic/versions/0001_baseline_sys_ruoyi.py
git commit -m "..."

# ③ 确认改动无影响数据库 schema（比如加注释、调整 docstring）：
git commit --no-verify -m "..."
```

## 卸载

```bash
pre-commit uninstall
```

## 设计权衡

- **检测粒度：文件级，不是字段级**。ORM 文件改动 + alembic 文件没改动 → 拒绝。
  - 优点：实现简单、误报少
  - 缺点：如果 ORM 改的是与 schema 无关的内容（如 docstring），会误报
  - 解决方案：误报时用 `git commit --no-verify` 跳过

- **只检 staged**：只对 `git add` 后的文件生效，对未 add 的不影响
  - 这符合 git 标准钩子语义

- **基于本地钩子（repo: local）**：不依赖外部 git 仓库
  - 优点：项目自包含
  - 缺点：钩子不会随 `pre-commit autoupdate` 自动更新（但本项目钩子就是 Python 脚本，跟随代码本身版本管理）

## 测试钩子是否工作

```bash
# 修改一个 ORM 文件 → 暂存
echo "# test" >> ruoyi-fastapi-backend/module_admin/entity/do/menu_do.py
git add ruoyi-fastapi-backend/module_admin/entity/do/menu_do.py

# 跑钩子 → 应该拒绝
python3 ruoyi-fastapi-backend/.pre-commit-hooks/check_orm_alembic_sync.py
# 期望：exit=1 + 报错信息

# 也修改 alembic → 再跑
echo "# test" >> ruoyi-fastapi-backend/alembic/versions/0001_baseline_sys_ruoyi.py
git add ruoyi-fastapi-backend/alembic/versions/0001_baseline_sys_ruoyi.py
python3 ruoyi-fastapi-backend/.pre-commit-hooks/check_orm_alembic_sync.py
# 期望：exit=0 + "✅ ORM + alembic 同步改动"

# 恢复测试改动
git restore --staged ...
git checkout -- ...
```

## 相关文档

- `docs/04-开发/DEBUG/orm-vs-alembic-sync-2026-07-12.md` 第 9 节：本次添加的背景 + AST 比对脚本思路
- `alembic/README.md`：alembic 标准迁移流程
- `alembic/env.py`：`compare_type=True / compare_server_default=True` 配置