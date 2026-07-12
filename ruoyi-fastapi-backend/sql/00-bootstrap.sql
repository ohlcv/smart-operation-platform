-- =====================================================================
-- 数据库冷启动 Bootstrap 脚本（v4.0 重构）
-- 作用：仅创建数据库本身，不建任何业务表
-- 业务表的演进由 Alembic 接管（启动 backend 时自动 alembic upgrade head）
--
-- 维护原则：
--   1. 本文件是 MySQL 容器 /docker-entrypoint-initdb.d 唯一挂载的 SQL
--   2. 任何 schema 演进都走 Alembic（alembic/versions/*.py）
--   3. 历史 init SQL 全部冻结到 _legacy_init/，仅供冷启动参考
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `ruoyi-fastapi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;