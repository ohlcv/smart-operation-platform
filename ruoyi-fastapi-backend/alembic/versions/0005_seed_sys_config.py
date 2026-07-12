"""seed sys_config：8 条 RuoYi 默认参数配置

Revision ID: 0005_seed_sys_config
Revises: 0004_seed_biz
Create Date: 2026-07-12 22:05:00.000000

背景：
  v4.0 重构时 0003_seed_sys 漏了 sys_config 的种子数据，导致：
    - sys_config 表为空
    - 启动时 init_cache_sys_config_services 把空表灌进 Redis
    - 登录接口读 captcha_enabled = None → None == 'true' 为 False → 跳过验证码
  本迁移把 RuoYi 原生 8 条默认配置灌进 sys_config 表。
"""
from __future__ import annotations

from alembic import op

revision = '0005_seed_sys_config'
down_revision = '0004_seed_biz'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # INSERT IGNORE 保持幂等，重复执行不会报重复键错误
    op.execute("""
        INSERT IGNORE INTO sys_config (config_id, config_name, config_key, config_value, config_type, create_by, create_time, update_by, update_time, remark)
        VALUES
          (1, '主框架页-默认皮肤样式名称',         'sys.index.skinName',              'skin-blue',     'Y', 'admin', NOW(), '', NULL, '蓝色 skin-blue、绿色 skin-green、紫色 skin-purple、红色 skin-red、黄色 skin-yellow'),
          (2, '用户管理-账号初始密码',             'sys.user.initPassword',           '123456',        'Y', 'admin', NOW(), '', NULL, '初始化密码 123456'),
          (3, '主框架页-侧边栏主题',               'sys.index.sideTheme',             'theme-dark',    'Y', 'admin', NOW(), '', NULL, '深色主题theme-dark，浅色主题theme-light'),
          (4, '账号自助-验证码开关',               'sys.account.captchaEnabled',      'true',          'Y', 'admin', NOW(), '', NULL, '是否开启验证码功能（true开启，false关闭）'),
          (5, '账号自助-是否开启用户注册功能',     'sys.account.registerUser',        'false',         'Y', 'admin', NOW(), '', NULL, '是否开启注册用户功能（true开启，false关闭）'),
          (6, '用户登录-黑名单列表',               'sys.login.blackIPList',           '',              'Y', 'admin', NOW(), '', NULL, '设置登录IP黑名单限制，多个匹配项以;分隔，支持匹配（*通配、网段）'),
          (7, '用户管理-初始密码修改策略',         'sys.account.initPasswordModify',  '1',             'Y', 'admin', NOW(), '', NULL, '0：初始密码修改策略关闭，没有任何提示，1：提醒用户，如果未修改初始密码，则在登录时就会提醒修改密码对话框'),
          (8, '用户管理-账号密码更新周期',         'sys.account.passwordValidateDays','0',             'Y', 'admin', NOW(), '', NULL, '密码更新周期（填写数字，数据初始化值为0不限制，若修改必须为大于0小于365的正整数），如果超过这个周期登录系统时，则在登录时就会提醒修改密码对话框');
    """)


def downgrade() -> None:
    op.execute("DELETE FROM sys_config WHERE config_id BETWEEN 1 AND 8;")
