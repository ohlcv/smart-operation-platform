"""module_biz 业务模块入口

按 docs/04-开发/开发进度台账.md §2.1 创建：
- 后端 module_biz/ 业务核心模块（合同、审批、客户、渠道等）
- 路由由 common/router.py auto_register_routers 自动扫描 module_biz/controller/ 注册
- schema 演进统一走 Alembic（alembic/versions/），启动时 run_alembic_upgrade() 自动 upgrade head
"""