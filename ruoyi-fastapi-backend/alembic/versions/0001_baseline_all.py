"""baseline all schema：sys_* + biz_* 全套表结构（v4.0 合并版）

Revision ID: 0001_baseline_all
Revises:
Create Date: 2026-07-12 22:30:00.000000

v4.0 重构：把原 0001_baseline_sys_ruoyi + 0002_baseline_biz 合并为一个 baseline
- 建 RuoYi 原生 sys_* 全套表（dept/user/role/menu/post/dict/config/notice/job/log）
- 建业务 8 张表（customer/contract/approval/channel/invoice/finance/bank/operation）
- 字符集/排序规则：utf8mb4 / utf8mb4_general_ci（与原 SQL 一致）
- 字段、索引、默认值与原 SQL 一一对应
- 不含任何数据，种子数据见 0002_seed_all
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


def _mysql_table_kwargs(bind) -> dict:
    """返回表选项 kwargs，MySQL 用 ENGINE/CHARSET/COLLATE，PG 走空 dict。

    用法：
        op.create_table(..., **_mysql_table_kwargs(bind))
    这样 alembic 在 PG 上跑时不会携带 MySQL 专属表选项。
    """
    if bind is not None and getattr(bind.dialect, 'name', '') == 'mysql':
        return {
            'mysql_engine': 'InnoDB',
            'mysql_default_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci',
        }
    return {}


revision = '0001_baseline_all'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """建 sys_* + biz_* 全套表（不含数据，数据见 0002 seed）"""
    bind = op.get_bind()

    # ============================================================
    # Part 1: sys_ruoyi 原生表
    # ============================================================

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
        **_mysql_table_kwargs(bind),
        comment='部门表',
    )

    # ============== sys_user（含 v2.9 signature 字段） ==============
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
        **_mysql_table_kwargs(bind),
        comment='用户信息表',
    )

    # ============== sys_user_role / sys_user_post ==============
    op.create_table(
        'sys_user_role',
        sa.Column('user_id', sa.BigInteger, nullable=False, comment='用户ID'),
        sa.Column('role_id', sa.BigInteger, nullable=False, comment='角色ID'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
        **_mysql_table_kwargs(bind),
        comment='用户和角色关联表',
    )
    op.create_table(
        'sys_user_post',
        sa.Column('user_id', sa.BigInteger, nullable=False, comment='用户ID'),
        sa.Column('post_id', sa.BigInteger, nullable=False, comment='岗位ID'),
        sa.PrimaryKeyConstraint('user_id', 'post_id'),
        **_mysql_table_kwargs(bind),
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
        **_mysql_table_kwargs(bind),
        comment='角色信息表',
    )
    op.create_table(
        'sys_role_dept',
        sa.Column('role_id', sa.BigInteger, nullable=False, comment='角色ID'),
        sa.Column('dept_id', sa.BigInteger, nullable=False, comment='部门ID'),
        sa.PrimaryKeyConstraint('role_id', 'dept_id'),
        **_mysql_table_kwargs(bind),
        comment='角色和部门关联表',
    )
    op.create_table(
        'sys_role_menu',
        sa.Column('role_id', sa.BigInteger, nullable=False, comment='角色ID'),
        sa.Column('menu_id', sa.BigInteger, nullable=False, comment='菜单ID'),
        sa.PrimaryKeyConstraint('role_id', 'menu_id'),
        **_mysql_table_kwargs(bind),
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
        sa.Column('query', sa.String(255), nullable=True, comment='路由参数'),
        sa.Column('route_name', sa.String(50), server_default='', nullable=True, comment='路由名称'),
        sa.Column('is_frame', sa.Integer, server_default='1', nullable=True, comment='是否为外链'),
        sa.Column('is_cache', sa.Integer, server_default='0', nullable=True, comment='是否缓存'),
        sa.Column('menu_type', sa.CHAR(1), server_default='', nullable=True, comment='菜单类型'),
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
        **_mysql_table_kwargs(bind),
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
        **_mysql_table_kwargs(bind),
        comment='岗位信息表',
    )

    # ============== sys_dict_type / sys_dict_data ==============
    op.create_table(
        'sys_dict_type',
        sa.Column('dict_id', sa.BigInteger, autoincrement=True, nullable=False, comment='字典主键'),
        sa.Column('dict_name', sa.String(100), server_default='', nullable=True, comment='字典名称'),
        sa.Column('dict_type', sa.String(100), server_default='', nullable=True, comment='字典类型'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='状态'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('dict_id'),
        sa.UniqueConstraint('dict_type'),
        **_mysql_table_kwargs(bind),
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
        **_mysql_table_kwargs(bind),
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
        **_mysql_table_kwargs(bind),
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
        **_mysql_table_kwargs(bind),
        comment='通知公告表',
    )

    # ============== sys_job / sys_job_log ==============
    op.create_table(
        'sys_job',
        sa.Column('job_id', sa.BigInteger, autoincrement=True, nullable=False, comment='任务ID'),
        sa.Column('job_name', sa.String(64), server_default='', nullable=False, comment='任务名称'),
        sa.Column('job_group', sa.String(64), server_default='default', nullable=False, comment='任务组名'),
        sa.Column('job_executor', sa.String(64), server_default='default', nullable=True, comment='任务执行器'),
        sa.Column('invoke_target', sa.String(500), nullable=False, comment='调用目标字符串'),
        sa.Column('job_args', sa.String(255), server_default='', nullable=True, comment='位置参数'),
        sa.Column('job_kwargs', sa.String(255), server_default='', nullable=True, comment='关键字参数'),
        sa.Column('cron_expression', sa.String(255), server_default='', nullable=True, comment='cron执行表达式'),
        sa.Column('misfire_policy', sa.String(20), server_default='3', nullable=True, comment='计划执行错误策略'),
        sa.Column('concurrent', sa.CHAR(1), server_default='1', nullable=True, comment='是否并发执行'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='状态'),
        sa.Column('create_by', sa.String(64), server_default='', nullable=True, comment='创建者'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.Column('update_by', sa.String(64), server_default='', nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), server_default='', nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('job_id'),
        **_mysql_table_kwargs(bind),
        comment='定时任务调度表',
    )
    op.create_table(
        'sys_job_log',
        sa.Column('job_log_id', sa.BigInteger, autoincrement=True, nullable=False, comment='任务日志ID'),
        sa.Column('job_name', sa.String(64), nullable=False, comment='任务名称'),
        sa.Column('job_group', sa.String(64), nullable=False, comment='任务组名'),
        sa.Column('job_executor', sa.String(64), nullable=False, comment='任务执行器'),
        sa.Column('invoke_target', sa.String(500), nullable=False, comment='调用目标字符串'),
        sa.Column('job_args', sa.String(255), server_default='', nullable=True, comment='位置参数'),
        sa.Column('job_kwargs', sa.String(255), server_default='', nullable=True, comment='关键字参数'),
        sa.Column('job_trigger', sa.String(255), server_default='', nullable=True, comment='任务触发器'),
        sa.Column('job_message', sa.String(500), nullable=True, comment='日志信息'),
        sa.Column('status', sa.CHAR(1), server_default='0', nullable=True, comment='执行状态'),
        sa.Column('exception_info', sa.String(2000), server_default='', nullable=True, comment='异常信息'),
        sa.Column('create_time', sa.DateTime, nullable=True, comment='创建时间'),
        sa.PrimaryKeyConstraint('job_log_id'),
        **_mysql_table_kwargs(bind),
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
        **_mysql_table_kwargs(bind),
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
        sa.Column('oper_location', sa.String(255), server_default='', nullable=True, comment='操作地点'),
        sa.Column('oper_param', sa.String(2000), server_default='', nullable=True, comment='请求参数'),
        sa.Column('json_result', sa.String(2000), server_default='', nullable=True, comment='返回参数'),
        sa.Column('status', sa.Integer, server_default='0', nullable=True, comment='操作状态'),
        sa.Column('error_msg', sa.String(2000), server_default='', nullable=True, comment='错误消息'),
        sa.Column('oper_time', sa.DateTime, nullable=True, comment='操作时间'),
        sa.Column('cost_time', sa.BigInteger, server_default='0', nullable=True, comment='消耗时间'),
        sa.PrimaryKeyConstraint('oper_id'),
        **_mysql_table_kwargs(bind),
        comment='操作日志记录',
    )

    # ============================================================
    # Part 2: biz_* 业务表
    # ============================================================

    # ============== biz_customer（含 v3.3 路线 C province） ==============
    op.create_table(
        'biz_customer',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='客户ID'),
        sa.Column('customer_code', sa.String(50), nullable=True, comment='业务编号 KH-NNN（唯一键）'),
        sa.Column('customer_name', sa.String(200), nullable=False, comment='客户名称（公司全称）'),
        sa.Column('customer_type', sa.String(20), nullable=True, comment='客户类型 scenic/hotel/agency/publish'),
        sa.Column('contact_name', sa.String(50), nullable=True, comment='联系人'),
        sa.Column('contact_phone', sa.String(20), nullable=True, comment='联系电话'),
        sa.Column('contact_email', sa.String(100), nullable=True, comment='邮箱'),
        sa.Column('address', sa.String(300), nullable=True, comment='地址'),
        sa.Column('province', sa.String(40), nullable=True, comment='省份（v3.3 路线 C）'),
        sa.Column('business_license', sa.String(200), nullable=True, comment='营业执照编号'),
        sa.Column('tax_no', sa.String(50), nullable=True, comment='纳税人识别号'),
        sa.Column('qualification_files', sa.JSON, nullable=True, comment='资质文件列表 [{name,url}]'),
        sa.Column('level', sa.String(10), nullable=True, comment='客户等级 A/B/C'),
        sa.Column('tags', sa.JSON, nullable=True, comment='标签 ["景区","文旅"]'),
        sa.Column('status', sa.SmallInteger, nullable=False, server_default='1', comment='状态 0=停用 1=启用'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.Column('remark', sa.String(500), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_code', name='uk_customer_code'),
        **_mysql_table_kwargs(bind),
        comment='客户档案表',
    )
    op.create_index('idx_customer_type', 'biz_customer', ['customer_type'])
    op.create_index('idx_level', 'biz_customer', ['level'])
    op.create_index('idx_status', 'biz_customer', ['status'])

    # ============== biz_contract（含 v3.3 路线 C province） ==============
    op.create_table(
        'biz_contract',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='合同ID'),
        sa.Column('contract_no', sa.String(50), nullable=False, comment='合同编号（唯一）'),
        sa.Column('title', sa.String(200), nullable=False, comment='合同名称'),
        sa.Column('contract_type', sa.String(20), nullable=False, comment='payment / business'),
        sa.Column('party_a', sa.String(200), nullable=False, comment='甲方（客户）'),
        sa.Column('party_b', sa.String(200), nullable=False, comment='乙方（本司）'),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='合同金额（元）'),
        sa.Column('amount_in_words', sa.String(100), nullable=True, comment='金额大写'),
        sa.Column('sign_date', sa.Date, nullable=True, comment='签订日期'),
        sa.Column('department', sa.String(100), nullable=True, comment='申请部门'),
        sa.Column('business_type', sa.String(50), nullable=True, comment='业务类型'),
        sa.Column('customer_id', sa.BigInteger, nullable=True, comment='关联客户ID biz_customer.id'),
        sa.Column('customer_name', sa.String(200), nullable=True, comment='冗余客户名称'),
        sa.Column('province', sa.String(40), nullable=True, comment='客户省份（v3.3 路线 C 冗余）'),
        sa.Column('remark', sa.Text, nullable=True, comment='合同备注'),
        sa.Column('attachments', sa.JSON, nullable=True, comment='附件列表 [{name,url}]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft', comment='draft/pending/approved/rejected'),
        sa.Column('current_step', sa.Integer, nullable=False, server_default='0', comment='当前审批步骤 0-6'),
        sa.Column('current_role', sa.String(50), nullable=True, comment='当前待审角色 role_key'),
        sa.Column('reject_count', sa.Integer, nullable=False, server_default='0', comment='累计驳回次数'),
        sa.Column('created_by', sa.BigInteger, nullable=False, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(50), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_no', name='uk_contract_no'),
        **_mysql_table_kwargs(bind),
        comment='合同主表',
    )
    op.create_index('idx_status', 'biz_contract', ['status'])
    op.create_index('idx_current_step', 'biz_contract', ['current_step'])
    op.create_index('idx_created_by', 'biz_contract', ['created_by'])
    op.create_index('idx_create_time', 'biz_contract', ['create_time'])
    op.create_index('idx_customer_id', 'biz_contract', ['customer_id'])

    # ============== biz_approval ==============
    op.create_table(
        'biz_approval',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='审批记录ID'),
        sa.Column('contract_id', sa.BigInteger, nullable=False, comment='关联合同ID biz_contract.id'),
        sa.Column('approver_id', sa.BigInteger, nullable=True, comment='审批人 sys_user.user_id'),
        sa.Column('approver_name', sa.String(50), nullable=True, comment='审批人姓名（冗余）'),
        sa.Column('step', sa.Integer, nullable=False, comment='审批步骤 0-6'),
        sa.Column('approver_role', sa.String(50), nullable=False, comment='审批时角色标识'),
        sa.Column('action', sa.String(20), nullable=False, comment='approve=通过 / reject=驳回'),
        sa.Column('comment', sa.Text, nullable=True, comment='审批意见'),
        sa.Column('reject_reason', sa.Text, nullable=True, comment='驳回原因'),
        sa.Column('signature_snapshot', sa.Text, nullable=True, comment='签名快照 base64 data URI'),
        sa.Column('approval_ip', sa.String(50), nullable=True, comment='审批操作 IP'),
        sa.Column('approval_time', sa.DateTime, nullable=False, comment='审批时间'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='记录创建时间'),
        sa.PrimaryKeyConstraint('id'),
        **_mysql_table_kwargs(bind),
        comment='审批记录表',
    )
    op.create_index('idx_contract_id', 'biz_approval', ['contract_id'])
    op.create_index('idx_approver_id', 'biz_approval', ['approver_id'])
    op.create_index('idx_step', 'biz_approval', ['step'])
    op.create_index('idx_approval_time', 'biz_approval', ['approval_time'])

    # ============== biz_channel（含 v3.3 路线 C province/city/lng/lat） ==============
    op.create_table(
        'biz_channel',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='渠道ID'),
        sa.Column('channel_code', sa.String(50), nullable=False, comment='渠道编码 QD-NNN'),
        sa.Column('channel_name', sa.String(100), nullable=False, comment='渠道名称'),
        sa.Column('category', sa.String(20), nullable=False, comment='渠道分类 meituan/douyin/ctrip/tongcheng'),
        sa.Column('contact_name', sa.String(50), nullable=True, comment='联系人'),
        sa.Column('contact_phone', sa.String(20), nullable=True, comment='联系电话'),
        sa.Column('contact_email', sa.String(100), nullable=True, comment='联系邮箱'),
        sa.Column('platform_url', sa.String(255), nullable=True, comment='平台地址'),
        sa.Column('account', sa.String(128), nullable=True, comment='登录账号（演示用）'),
        sa.Column('password', sa.String(128), nullable=True, comment='登录密码（演示用，明文不加密）'),
        sa.Column('commission_rate', sa.Numeric(5, 4), nullable=True, comment='佣金比例（0-1）'),
        sa.Column('province', sa.String(40), nullable=True, comment='省份（v3.3 路线 C）'),
        sa.Column('city', sa.String(40), nullable=True, comment='城市（v3.3 路线 C）'),
        sa.Column('lng', sa.Float(53), nullable=True, comment='经度（v3.3 路线 C）'),
        sa.Column('lat', sa.Float(53), nullable=True, comment='纬度（v3.3 路线 C）'),
        sa.Column('status', sa.Integer, nullable=False, server_default='1', comment='状态 0=停用 1=启用'),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0', comment='排序值'),
        sa.Column('description', sa.Text, nullable=True, comment='渠道说明'),
        sa.Column('attachments', sa.JSON, nullable=True, comment='资质附件 [{name,url}]'),
        sa.Column('contract_ids', sa.JSON, nullable=True, comment='关联合同ID列表（冗余便于展示）'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('channel_code', name='uk_channel_code'),
        **_mysql_table_kwargs(bind),
        comment='渠道主表',
    )
    op.create_index('idx_category', 'biz_channel', ['category'])
    op.create_index('idx_status', 'biz_channel', ['status'])

    # ============== biz_invoice ==============
    op.create_table(
        'biz_invoice',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='发票ID'),
        sa.Column('invoice_no', sa.String(50), nullable=False, comment='发票号（唯一）'),
        sa.Column('contract_id', sa.BigInteger, nullable=False, comment='关联合同ID biz_contract.id（1:1）'),
        sa.Column('contract_no', sa.String(50), nullable=True, comment='冗余合同编号（便于展示）'),
        sa.Column('invoice_type', sa.String(20), nullable=False, comment='specialized/general/electronic'),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='开票金额（含税）'),
        sa.Column('tax_rate', sa.Numeric(5, 4), nullable=False, server_default='0.0000', comment='税率'),
        sa.Column('tax_amount', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='税额'),
        sa.Column('party_name', sa.String(200), nullable=False, comment='购方名称（抬头）'),
        sa.Column('party_tax_no', sa.String(50), nullable=True, comment='购方税号'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='pending/issued/void'),
        sa.Column('apply_date', sa.Date, nullable=True, comment='申请日期'),
        sa.Column('issue_date', sa.Date, nullable=True, comment='开票日期'),
        sa.Column('void_reason', sa.String(500), nullable=True, comment='作废原因'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_no', name='uk_invoice_no'),
        sa.UniqueConstraint('contract_id', name='uk_contract_id'),
        **_mysql_table_kwargs(bind),
        comment='发票主表',
    )
    op.create_index('idx_invoice_status', 'biz_invoice', ['status'])
    op.create_index('idx_invoice_create_time', 'biz_invoice', ['create_time'])

    # ============== biz_finance_entry ==============
    op.create_table(
        'biz_finance_entry',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='流水ID'),
        sa.Column('entry_no', sa.String(50), nullable=False, comment='流水号 FN-NNN'),
        sa.Column('entry_type', sa.String(20), nullable=False, comment='payable/receivable'),
        sa.Column('direction', sa.String(10), nullable=False, server_default='out', comment='out/in'),
        sa.Column('invoice_id', sa.BigInteger, nullable=True, comment='关联发票ID biz_invoice.id'),
        sa.Column('invoice_no', sa.String(50), nullable=True, comment='冗余发票号'),
        sa.Column('contract_id', sa.BigInteger, nullable=True, comment='关联合同ID biz_contract.id'),
        sa.Column('contract_no', sa.String(50), nullable=True, comment='冗余合同号'),
        sa.Column('party_name', sa.String(200), nullable=True, comment='对手方名称'),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='金额'),
        sa.Column('account', sa.String(50), nullable=True, comment='银行账号'),
        sa.Column('account_name', sa.String(100), nullable=True, comment='账户名'),
        sa.Column('bank_name', sa.String(100), nullable=True, comment='开户行'),
        sa.Column('transaction_date', sa.Date, nullable=True, comment='交易日期'),
        sa.Column('cleared', sa.Integer, nullable=False, server_default='0', comment='是否已对账'),
        sa.Column('cleared_time', sa.DateTime, nullable=True, comment='对账时间'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_no', name='uk_entry_no'),
        **_mysql_table_kwargs(bind),
        comment='财务流水台账',
    )
    op.create_index('idx_entry_type', 'biz_finance_entry', ['entry_type'])
    op.create_index('idx_cleared', 'biz_finance_entry', ['cleared'])
    op.create_index('idx_transaction_date', 'biz_finance_entry', ['transaction_date'])
    op.create_index('idx_invoice_id', 'biz_finance_entry', ['invoice_id'])
    op.create_index('idx_contract_id', 'biz_finance_entry', ['contract_id'])

    # ============== biz_bank_statement ==============
    op.create_table(
        'biz_bank_statement',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='对账单ID'),
        sa.Column('batch_no', sa.String(50), nullable=False, comment='导入批次号 BS-YYYYMMDDHHMMSS'),
        sa.Column('transaction_date', sa.Date, nullable=False, comment='交易日期'),
        sa.Column('account', sa.String(50), nullable=False, comment='银行账号'),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='金额'),
        sa.Column('direction', sa.String(10), nullable=False, server_default='in', comment='in/out'),
        sa.Column('counterparty', sa.String(100), nullable=True, comment='交易对手'),
        sa.Column('counterparty_account', sa.String(50), nullable=True, comment='对手账号'),
        sa.Column('summary', sa.String(200), nullable=True, comment='摘要'),
        sa.Column('matched', sa.Integer, nullable=False, server_default='0', comment='是否已匹配'),
        sa.Column('matched_entry_id', sa.BigInteger, nullable=True, comment='匹配的财务流水ID'),
        sa.Column('import_time', sa.DateTime, nullable=False, comment='导入时间'),
        sa.Column('imported_by', sa.BigInteger, nullable=True, comment='导入人 sys_user.user_id'),
        sa.PrimaryKeyConstraint('id'),
        **_mysql_table_kwargs(bind),
        comment='银行对账单导入表',
    )
    op.create_index('idx_batch_no', 'biz_bank_statement', ['batch_no'])
    op.create_index('idx_statement_transaction_date', 'biz_bank_statement', ['transaction_date'])
    op.create_index('idx_matched', 'biz_bank_statement', ['matched'])
    op.create_index('idx_account', 'biz_bank_statement', ['account'])

    # ============== biz_operation ==============
    op.create_table(
        'biz_operation',
        sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, comment='记录ID'),
        sa.Column('period', sa.String(20), nullable=False, comment='周期 key 2026-07/2026-Q3/2026'),
        sa.Column('period_type', sa.String(20), nullable=False, comment='month/quarter/year'),
        sa.Column('business_line', sa.String(20), nullable=True, comment='scenic/digital/logistics'),
        sa.Column('revenue', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='营收'),
        sa.Column('cost', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='成本'),
        sa.Column('gross_profit', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='毛利（实时计算冗余）'),
        sa.Column('customer_count', sa.Integer, nullable=False, server_default='0', comment='客户数'),
        sa.Column('contract_count', sa.Integer, nullable=False, server_default='0', comment='合同数'),
        sa.Column('avg_order_value', sa.Numeric(18, 2), nullable=False, server_default='0.00', comment='客单价'),
        sa.Column('remark', sa.Text, nullable=True, comment='备注'),
        sa.Column('created_by', sa.BigInteger, nullable=True, comment='创建人 sys_user.user_id'),
        sa.Column('created_by_name', sa.String(64), nullable=True, comment='创建人姓名（冗余）'),
        sa.Column('create_time', sa.DateTime, nullable=False, comment='创建时间'),
        sa.Column('update_by', sa.String(64), nullable=True, comment='更新者'),
        sa.Column('update_time', sa.DateTime, nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period', 'period_type', 'business_line', name='uk_period_type_line'),
        **_mysql_table_kwargs(bind),
        comment='经营数据表',
    )
    op.create_index('idx_op_period_type', 'biz_operation', ['period_type'])
    op.create_index('idx_op_business_line', 'biz_operation', ['business_line'])
    op.create_index('idx_op_period', 'biz_operation', ['period'])


def downgrade() -> None:
    """downgrade sys + biz 全套表（删除顺序：先删子表后删父表）"""
    # biz 表（无外键依赖，按业务关联反向删）
    op.drop_table('biz_operation')
    op.drop_table('biz_bank_statement')
    op.drop_table('biz_finance_entry')
    op.drop_table('biz_invoice')
    op.drop_table('biz_channel')
    op.drop_table('biz_approval')
    op.drop_table('biz_contract')
    op.drop_table('biz_customer')
    # sys 表
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
