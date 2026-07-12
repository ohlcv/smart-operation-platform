"""baseline sys_ruoyi schema

Revision ID: 0001_baseline_sys_ruoyi
Revises:
Create Date: 2026-07-12 18:30:00.000000

v4.0 重构：
- 把原 ruoyi-fastapi.sql 的 sys_* 表结构（不含数据）迁移到 Alembic
- 字符集/排序规则：utf8mb4 / utf8mb4_general_ci（与原 SQL 一致）
- 字段、索引、默认值与原 SQL 一一对应
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


def _mysql_table_kwargs(bind) -> dict:
    """返回表选项 kwargs，MySQL 用 ENGINE/CHARSET/COLLATE，PG 走空 dict。

    用法：
        op.create_table(..., **_mysql_table_kwargs(bind))
    这样 alembic 在 PG 上跑时不会携带 MySQL 专属表选项（Django-style postgres default）。
    """
    if bind is not None and getattr(bind.dialect, 'name', '') == 'mysql':
        return {
            'mysql_engine': 'InnoDB',
            'mysql_default_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci',
        }
    return {}


# revision identifiers, used by Alembic.
revision = '0001_baseline_sys_ruoyi'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """建 RuoYi 原生 sys_* 全套表（不含数据，数据见 0003 seed）"""
    bind = op.get_bind()
    # ============== sys_dept ==============
    op.create_table(
        'sys_dept',
        sa.Column('dept_id', sa.BigInteger, autoincrement=True, nullable=False, comment='部门id'),
        sa.Column('parent_id', sa.BigInteger, server_default='0', nullable=True, comment='父部门id'),
        sa.Column('ancestors', sa.String(50), server_default='', nullable=True, comment='祖级列表'),
        sa.Column('dept_name', sa.String(30), server_default='', nullable=True, comment='部门名称'),
        sa.Column('order_num', sa.Integer, server_default='0', nullable=True, comment='显示顺序'),
        sa.Column('leader', sa.String(20), nullable=True, comment='负责人'),
        sa.Column('phone', sa.String(11), nullable=True, comment='联系电话'),
        sa.Column('email', sa.String(50), nullable=True, comment='邮箱'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='部门状态（0正常 1停用）'),
        sa.Column('del_flag', sa.CHAR(1), server_default='0', nullable=True, comment='删除标志'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('dept_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='部门表',
    )

    # ============== sys_user（注意：含 v2.9 signature 字段） ==============
    op.create_table(
        'sys_user',
        sa.Column('user_id', sa.BigInteger, autoincrement=True, nullable=False, comment='用户ID'),
        sa.Column('dept_id', sa.BigInteger, nullable=True, comment='部门ID'),
        sa.Column('user_name', sa.String(30), nullable=False, comment='用户账号'),
        sa.Column('nick_name', sa.String(30), nullable=False, comment='用户昵称'),
        sa.Column('user_type', sa.String(2), server_default='00', nullable=True, comment='用户类型'),
        sa.Column('email', sa.String(50), server_default='', nullable=True, comment='用户邮箱'),
        sa.Column('phonenumber', sa.String(11), server_default='', nullable=True, comment='手机号码'),
        sa.Column('sex', sa.CHAR(1), server_default='0', nullable=True, comment='用户性别'),
        sa.Column('avatar', sa.String(100), server_default='', nullable=True, comment='头像地址'),
        sa.Column('password', sa.String(100), server_default='', nullable=True, comment='密码'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='帐号状态'),
        sa.Column('del_flag', sa.CHAR(1), server_default='0', nullable=True, comment='删除标志'),
        sa.Column('login_ip', sa.String(128), server_default='', nullable=True, comment='最后登录IP'),
        sa.Column('login_date', sa.DateTime, nullable=True, comment='最后登录时间'),
        sa.Column('pwd_update_date', sa.DateTime, nullable=True, comment='密码最后更新时间'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.Column('signature', sa.String(500), nullable=True, comment='电子签名 base64 data URI（v2.9）'),
        sa.PrimaryKeyConstraint('user_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='用户信息表',
    )

    # ============== sys_user_role / sys_user_post ==============
    op.create_table(
        'sys_user_role',
        sa.Column('user_id', sa.BigInteger, nullable=False, comment='用户ID'),
        sa.Column('role_id', sa.BigInteger, nullable=False, comment='角色ID'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='用户和角色关联表',
    )
    op.create_table(
        'sys_user_post',
        sa.Column('user_id', sa.BigInteger, nullable=False, comment='用户ID'),
        sa.Column('post_id', sa.BigInteger, nullable=False, comment='岗位ID'),
        sa.PrimaryKeyConstraint('user_id', 'post_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='用户与岗位关联表',
    )

    # ============== sys_role / sys_role_dept / sys_role_menu ==============
    op.create_table(
        'sys_role',
        sa.Column('role_id', sa.BigInteger, autoincrement=True, nullable=False, comment='角色ID'),
        sa.Column('role_name', sa.String(30), nullable=False, comment='角色名称'),
        sa.Column('role_key', sa.String(100), nullable=False, comment='角色权限字符串'),
        sa.Column('role_sort', sa.Integer, nullable=False, comment='显示顺序'),
        sa.Column('data_scope', sa.CHAR(1), server_default='1', nullable=True, comment='数据范围'),
        sa.Column('menu_check_strictly', sa.Integer, server_default='1', nullable=True, comment='菜单树选择项是否关联显示'),
        sa.Column('dept_check_strictly', sa.Integer, server_default='1', nullable=True, comment='部门树选择项是否关联显示'),
        sa.Column('status', sa.CHAR(1), nullable=False, comment='角色状态'),
        sa.Column('del_flag', sa.CHAR(1), server_default='0', nullable=True, comment='删除标志'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('role_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='角色信息表',
    )
    op.create_table(
        'sys_role_dept',
        sa.Column('role_id', sa.BigInteger, nullable=False, comment='角色ID'),
        sa.Column('dept_id', sa.BigInteger, nullable=False, comment='部门ID'),
        sa.PrimaryKeyConstraint('role_id', 'dept_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='角色和部门关联表',
    )
    op.create_table(
        'sys_role_menu',
        sa.Column('role_id', sa.BigInteger, nullable=False, comment='角色ID'),
        sa.Column('menu_id', sa.BigInteger, nullable=False, comment='菜单ID'),
        sa.PrimaryKeyConstraint('role_id', 'menu_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='角色和菜单关联表',
    )

    # ============== sys_menu ==============
    op.create_table(
        'sys_menu',
        sa.Column('menu_id', sa.BigInteger, autoincrement=True, nullable=False, comment='菜单ID'),
        sa.Column('menu_name', sa.String(50), nullable=False, comment='菜单名称'),
        sa.Column('parent_id', sa.BigInteger, server_default='0', nullable=True, comment='父菜单ID'),
        sa.Column('order_num', sa.Integer, server_default='0', nullable=True, comment='显示顺序'),
        sa.Column('path', sa.String(200), server_default='', nullable=True, comment='路由地址'),
        sa.Column('component', sa.String(255), nullable=True, comment='组件路径'),
        sa.Column('is_frame', sa.Integer, server_default='1', nullable=True, comment='是否为外链'),
        sa.Column('is_cache', sa.Integer, server_default='0', nullable=True, comment='是否缓存'),
        sa.Column('menu_type', sa.CHAR(1), nullable=True, comment='菜单类型'),
        sa.Column('visible', sa.CHAR(1), server_default='0', nullable=True, comment='菜单状态'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='菜单状态'),
        sa.Column('perms', sa.String(100), nullable=True, comment='权限标识'),
        sa.Column('icon', sa.String(100), server_default='#', nullable=True, comment='菜单图标'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), server_default='', nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('menu_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='菜单权限表',
    )

    # ============== sys_post ==============
    op.create_table(
        'sys_post',
        sa.Column('post_id', sa.BigInteger, autoincrement=True, nullable=False, comment='岗位ID'),
        sa.Column('post_code', sa.String(64), nullable=False, comment='岗位编码'),
        sa.Column('post_name', sa.String(50), nullable=False, comment='岗位名称'),
        sa.Column('post_sort', sa.Integer, nullable=False, comment='显示顺序'),
        sa.Column('status', sa.CHAR(1), nullable=False, comment='状态'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('post_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='岗位信息表',
    )

    # ============== sys_dict_type / sys_dict_data ==============
    op.create_table(
        'sys_dict_type',
        sa.Column('dict_id', sa.BigInteger, autoincrement=True, nullable=False, comment='字典主键'),
        sa.Column('dict_name', sa.String(100), nullable=True, comment='字典名称'),
        sa.Column('dict_type', sa.String(100), server_default='', nullable=True, comment='字典类型'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='状态'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('dict_id'),
        sa.UniqueConstraint('dict_type'),
        **_mysql_table_kwargs(op.get_bind())
        comment='字典类型表',
    )
    op.create_table(
        'sys_dict_data',
        sa.Column('dict_code', sa.BigInteger, autoincrement=True, nullable=False, comment='字典编码'),
        sa.Column('dict_sort', sa.Integer, server_default='0', nullable=True, comment='字典排序'),
        sa.Column('dict_label', sa.String(100), server_default='', nullable=True, comment='字典标签'),
        sa.Column('dict_value', sa.String(100), server_default='', nullable=True, comment='字典键值'),
        sa.Column('dict_type', sa.String(100), server_default='', nullable=True, comment='字典类型'),
        sa.Column('css_class', sa.String(100), nullable=True, comment='样式属性'),
        sa.Column('list_class', sa.String(100), nullable=True, comment='表格回显样式'),
        sa.Column('is_default', sa.CHAR(1), server_default='N', nullable=True, comment='是否默认'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='状态'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('dict_code'),
        **_mysql_table_kwargs(op.get_bind())
        comment='字典数据表',
    )

    # ============== sys_config ==============
    op.create_table(
        'sys_config',
        sa.Column('config_id', sa.Integer, autoincrement=True, nullable=False, comment='参数主键'),
        sa.Column('config_name', sa.String(100), server_default='', nullable=True, comment='参数名称'),
        sa.Column('config_key', sa.String(100), server_default='', nullable=True, comment='参数键名'),
        sa.Column('config_value', sa.String(500), server_default='', nullable=True, comment='参数键值'),
        sa.Column('config_type', sa.CHAR(1), server_default='N', nullable=True, comment='系统内置'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('config_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='参数配置表',
    )

    # ============== sys_notice ==============
    op.create_table(
        'sys_notice',
        sa.Column('notice_id', sa.Integer, autoincrement=True, nullable=False, comment='公告ID'),
        sa.Column('notice_title', sa.String(50), nullable=False, comment='公告标题'),
        sa.Column('notice_type', sa.CHAR(1), nullable=False, comment='公告类型'),
        sa.Column('notice_content', sa.Text, nullable=True, comment='公告内容'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='公告状态'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('notice_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='通知公告表',
    )

    # ============== sys_job / sys_job_log ==============
    op.create_table(
        'sys_job',
        sa.Column('job_id', sa.BigInteger, autoincrement=True, nullable=False, comment='任务ID'),
        sa.Column('job_name', sa.String(64), server_default='', nullable=True, comment='任务名称'),
        sa.Column('job_group', sa.String(64), server_default='default', nullable=True, comment='任务组名'),
        sa.Column('invoke_target', sa.String(500), nullable=False, comment='调用目标字符串'),
        sa.Column('cron_expression', sa.String(255), server_default='', nullable=True, comment='cron执行表达式'),
        sa.Column('misfire_policy', sa.String(20), server_default='3', nullable=True, comment='计划执行错误策略'),
        sa.Column('concurrent', sa.CHAR(1), server_default='1', nullable=True, comment='是否并发执行'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='状态'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('job_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='定时任务调度表',
    )
    op.create_table(
        'sys_job_log',
        sa.Column('job_log_id', sa.BigInteger, autoincrement=True, nullable=False, comment='任务日志ID'),
        sa.Column('job_name', sa.String(64), nullable=True, comment='任务名称'),
        sa.Column('job_group', sa.String(64), nullable=True, comment='任务组名'),
        sa.Column('invoke_target', sa.String(500), nullable=True, comment='调用目标字符串'),
        sa.Column('job_message', sa.String(500), nullable=True, comment='日志信息'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='执行状态'),
        sa.Column('exception_info', sa.String(2000), server_default='', nullable=True, comment='异常信息'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.PrimaryKeyConstraint('job_log_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='定时任务调度日志表',
    )

    # ============== sys_logininfor / sys_oper_log ==============
    op.create_table(
        'sys_logininfor',
        sa.Column('info_id', sa.BigInteger, autoincrement=True, nullable=False, comment='访问ID'),
        sa.Column('user_name', sa.String(50), server_default='', nullable=True, comment='登录账号'),
        sa.Column('ipaddr', sa.String(128), server_default='', nullable=True, comment='登录IP地址'),
        sa.Column('login_location', sa.String(255), server_default='', nullable=True, comment='登录地点'),
        sa.Column('browser', sa.String(50), server_default='', nullable=True, comment='浏览器类型'),
        sa.Column('os', sa.String(50), server_default='', nullable=True, comment='操作系统'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='登录状态'),
        sa.Column('msg', sa.String(255), server_default='', nullable=True, comment='提示消息'),
        sa.Column('login_time', sa.DateTime, nullable=True, comment='访问时间'),
        sa.PrimaryKeyConstraint('info_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='系统访问记录',
    )
    op.create_table(
        'sys_oper_log',
        sa.Column('oper_id', sa.BigInteger, autoincrement=True, nullable=False, comment='日志主键'),
        sa.Column('title', sa.String(50), server_default='', nullable=True, comment='模块标题'),
        sa.Column('business_type', sa.Integer, server_default='0', nullable=True, comment='业务类型'),
        sa.Column('method', sa.String(100), server_default='', nullable=True, comment='方法名称'),
        sa.Column('request_method', sa.String(10), server_default='', nullable=True, comment='请求方式'),
        sa.Column('operator_type', sa.Integer, server_default='0', nullable=True, comment='操作类别'),
        sa.Column('oper_name', sa.String(50), server_default='', nullable=True, comment='操作人员'),
        sa.Column('dept_name', sa.String(50), server_default='', nullable=True, comment='部门名称'),
        sa.Column('oper_url', sa.String(255), server_default='', nullable=True, comment='请求URL'),
        sa.Column('oper_ip', sa.String(128), server_default='', nullable=True, comment='主机地址'),
        sa.Column('oper_param', sa.String(2000), server_default='', nullable=True, comment='请求参数'),
        sa.Column('json_result', sa.String(2000), server_default='', nullable=True, comment='返回参数'),
        sa.Column('status', sa.Integer, server_default='0', nullable=True, comment='操作状态'),
        sa.Column('error_msg', sa.String(2000), server_default='', nullable=True, comment='错误消息'),
        sa.Column('oper_time', sa.DateTime, nullable=True, comment='操作时间'),
        sa.Column('cost_time', sa.BigInteger, server_default='0', nullable=True, comment='消耗时间'),
        sa.PrimaryKeyConstraint('oper_id'),
        **_mysql_table_kwargs(op.get_bind())
        comment='操作日志记录',
    )


def downgrade() -> None:
    """downgrade sys_ruoyi 全套表（删除顺序：先删子表后删父表）"""
    op.drop_table('sys_oper_log')
    op.drop_table('sys_logininfor')
    op.drop_table('sys_job_log')
    op.drop_table('sys_job')
    op.drop_table('sys_notice')
    op.drop_table('sys_config')
    op.drop_table('sys_dict_data')
    op.drop_table('sys_dict_type')
    op.drop_table('sys_post')
    op.drop_table('sys_menu')
    op.drop_table('sys_role_menu')
    op.drop_table('sys_role_dept')
    op.drop_table('sys_role')
    op.drop_table('sys_user_post')
    op.drop_table('sys_user_role')
    op.drop_table('sys_user')
    op.drop_table('sys_dept')