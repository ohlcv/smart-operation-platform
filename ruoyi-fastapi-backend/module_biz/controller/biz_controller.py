"""
业务模块路由 — 合同审批/客户/渠道/发票/财务/经营数据/OTA/驾驶舱

所有子模块控制器遵循：
  - controller/*.py  放在本目录（自动被 APIRouterPro 扫描注册）
  - 统一前缀 /biz/*（业务模块统一前缀）
  - 权限：依赖 PreAuthDependency（登录后可访问，具体按钮级权限在 @Log/@PreAuth 注解中控制）

子模块规划：
  - contract_controller.py   合同管理
  - approval_controller.py   审批记录
  - customer_controller.py   客户档案
  - channel_controller.py    渠道平台
  - invoice_controller.py   发票管理
  - finance_controller.py    财务记录（银行对账）
  - operation_controller.py  经营数据
  - ota_controller.py       OTA 导入
  - cockpit_controller.py   驾驶舱/战略总览
"""

from typing import Annotated

from fastapi import Path, Response
from fastapi.responses import JSONResponse

from common.aspect.pre_auth import CurrentUserDependency
from common.router import APIRouterPro
from common.vo import ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel

biz_controller = APIRouterPro(
    prefix='/biz', order_num=20, tags=['业务模块'], dependencies=[CurrentUserDependency()]
)


@biz_controller.get(
    '/health',
    summary='业务模块健康检查',
    description='用于验证业务模块路由是否正常注册',
    response_model=ResponseBaseModel,
)
async def biz_health(
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """业务模块根路由，健康检查占位接口。"""
    return JSONResponse(content={'code': 200, 'msg': '业务模块正常', 'data': None})
