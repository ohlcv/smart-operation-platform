"""经营数据 Service 层（遵循 ADR D24）。

业务规则（ADR D05）：
- 当前阶段手工录入，不与合同自动汇总
- (period, period_type, business_line) 三元组唯一
- 毛利 = 营收 - 成本（实时计算，DB 冗余存储）
- 客单价 = 营收 / max(1, 合同数)
- 同比环比：根据 period_type 自动算上期（年/月/季）
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.operation_dao import OperationDAO
from module_biz.entity.do.operation_do import BizOperation
from module_biz.entity.vo.operation_vo import (
    OperationComparisonItemModel,
    OperationComparisonQueryModel,
    OperationComparisonResponseModel,
    OperationCreateModel,
    OperationQueryModel,
    OperationResponseModel,
    OperationTypeOptionModel,
    OperationUpdateModel,
)
from module_biz.enums import OperationBusinessLineEnum, OperationPeriodEnum


VALID_PERIOD_TYPES = {e.value for e in OperationPeriodEnum}
VALID_BUSINESS_LINES = {e.value for e in OperationBusinessLineEnum}


def _user_id(current_user: CurrentUserModel) -> int:
    if not current_user or not current_user.user:
        raise ServiceException(message='未识别当前用户')
    return current_user.user.user_id


def _user_name(current_user: CurrentUserModel) -> str | None:
    if current_user and current_user.user:
        return current_user.user.user_name or current_user.user.nick_name
    return None


def _validate_period_type(p: str) -> str:
    if p not in VALID_PERIOD_TYPES:
        raise ServiceException(message=f'周期类型 "{p}" 非法', data='400')
    return p


def _validate_business_line(b: str | None) -> str | None:
    if b is None:
        return None
    if b not in VALID_BUSINESS_LINES:
        raise ServiceException(message=f'业务线 "{b}" 非法', data='400')
    return b


def _calc_gross_profit(revenue: Decimal, cost: Decimal) -> Decimal:
    return (revenue - cost).quantize(Decimal('0.01'))


def _calc_avg_order_value(revenue: Decimal, contract_count: int) -> Decimal:
    if contract_count <= 0:
        return Decimal('0.00')
    return (revenue / Decimal(contract_count)).quantize(Decimal('0.01'))


def _shift_period(period: str, period_type: str) -> tuple[str, str]:
    """计算上期（环比）和去年同期（同比）period。

    返回 (mom_period, yoy_period)。
    """
    if period_type == 'month':
        # period = "YYYY-MM"
        try:
            year, month = period.split('-')
            year, month = int(year), int(month)
        except (ValueError, AttributeError):
            return period, period
        # 环比：上个月
        prev_m = month - 1
        prev_y = year
        if prev_m == 0:
            prev_m = 12
            prev_y -= 1
        mom = f'{prev_y:04d}-{prev_m:02d}'
        # 同比：去年同月
        yoy = f'{year - 1:04d}-{month:02d}'
        return mom, yoy
    if period_type == 'quarter':
        # period = "YYYY-Qn"
        try:
            year_s, qpart = period.split('-Q')
            year, q = int(year_s), int(qpart)
        except (ValueError, AttributeError):
            return period, period
        prev_q = q - 1
        prev_y = year
        if prev_q == 0:
            prev_q = 4
            prev_y -= 1
        mom = f'{prev_y:04d}-Q{prev_q}'
        yoy = f'{year - 1:04d}-Q{q}'
        return mom, yoy
    if period_type == 'year':
        # period = "YYYY"
        try:
            year = int(period)
        except ValueError:
            return period, period
        mom = f'{year - 1:04d}'
        yoy = f'{year - 1:04d}'
        return mom, yoy
    return period, period


def _to_response(op: BizOperation) -> OperationResponseModel:
    return OperationResponseModel(
        id=op.id,
        period=op.period,
        period_type=op.period_type,
        period_type_label=OperationPeriodEnum.label(op.period_type),
        business_line=op.business_line,
        business_line_label=OperationBusinessLineEnum.label(op.business_line) if op.business_line else None,
        revenue=op.revenue,
        cost=op.cost,
        gross_profit=op.gross_profit,
        customer_count=op.customer_count,
        contract_count=op.contract_count,
        avg_order_value=op.avg_order_value,
        remark=op.remark,
        created_by=op.created_by,
        created_by_name=op.created_by_name,
        create_time=op.create_time,
        update_time=op.update_time,
    )


class OperationService:
    @staticmethod
    async def list_services(
        db: AsyncSession,
        query: OperationQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        rows, total = await OperationDAO.list_page(
            db,
            period_type=query.period_type,
            business_line=query.business_line,
            period=query.period,
            page_num=query.page_num,
            page_size=query.page_size,
        )
        return {
            'rows': [_to_response(op).model_dump(by_alias=True) for op in rows],
            'total': total,
            'page_num': query.page_num,
            'page_size': query.page_size,
        }

    @staticmethod
    async def detail_services(db: AsyncSession, op_id: int, current_user: CurrentUserModel) -> dict[str, Any]:
        op = await OperationDAO.get_by_id(db, op_id)
        if not op:
            raise ServiceException(message=f'经营数据ID {op_id} 不存在', data='404')
        return _to_response(op).model_dump(by_alias=True)

    @staticmethod
    async def create_services(
        db: AsyncSession,
        payload: OperationCreateModel,
        current_user: CurrentUserModel,
    ) -> int:
        _validate_period_type(payload.period_type)
        business_line = _validate_business_line(payload.business_line)

        existed = await OperationDAO.get_by_unique(
            db, payload.period, payload.period_type, business_line
        )
        if existed:
            raise ServiceException(
                message=f'周期 {payload.period}（{payload.period_type}/{business_line or "ALL"}）已存在',
                data='409',
            )

        gross = _calc_gross_profit(payload.revenue, payload.cost)
        aov = _calc_avg_order_value(payload.revenue, payload.contract_count)

        op = BizOperation(
            period=payload.period,
            period_type=payload.period_type,
            business_line=business_line,
            revenue=payload.revenue,
            cost=payload.cost,
            gross_profit=gross,
            customer_count=payload.customer_count,
            contract_count=payload.contract_count,
            avg_order_value=aov,
            remark=payload.remark,
            created_by=_user_id(current_user),
            created_by_name=_user_name(current_user),
            create_time=datetime.now(),
        )
        new_id = await OperationDAO.insert(db, op)
        await db.commit()
        return new_id

    @staticmethod
    async def update_services(
        db: AsyncSession,
        op_id: int,
        payload: OperationUpdateModel,
        current_user: CurrentUserModel,
    ) -> None:
        op = await OperationDAO.get_by_id(db, op_id)
        if not op:
            raise ServiceException(message=f'经营数据ID {op_id} 不存在', data='404')

        fields = payload.model_dump(exclude_unset=True, exclude_none=False)
        fields.pop('id', None)
        if not fields:
            return

        # 重新计算毛利 + 客单价
        new_revenue = fields.get('revenue', op.revenue)
        new_cost = fields.get('cost', op.cost)
        new_count = fields.get('contract_count', op.contract_count)
        fields['gross_profit'] = _calc_gross_profit(new_revenue, new_cost)
        fields['avg_order_value'] = _calc_avg_order_value(new_revenue, new_count)
        fields['update_by'] = _user_name(current_user) or ''

        await OperationDAO.update_by_id(db, op_id, fields)
        await db.commit()

    @staticmethod
    async def delete_services(
        db: AsyncSession,
        op_id: int,
        current_user: CurrentUserModel,
    ) -> int:
        op = await OperationDAO.get_by_id(db, op_id)
        if not op:
            raise ServiceException(message=f'经营数据ID {op_id} 不存在', data='404')
        deleted = await OperationDAO.delete_by_id(db, op_id)
        await db.commit()
        return deleted

    @staticmethod
    async def comparison_services(
        db: AsyncSession,
        query: OperationComparisonQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """同比环比对比。"""
        current = await OperationDAO.get_by_period_and_type(
            db, query.period, 'month', query.business_line
        )
        if not current:
            raise ServiceException(
                message=f'当期 {query.period} 经营数据不存在，请先录入',
                data='404',
            )

        mom_period, yoy_period = _shift_period(query.period, 'month')
        prev = await OperationDAO.get_by_period_and_type(
            db, mom_period, 'month', query.business_line
        )
        last_year = await OperationDAO.get_by_period_and_type(
            db, yoy_period, 'month', query.business_line
        )

        metrics = [
            ('revenue', '营收'),
            ('cost', '成本'),
            ('gross_profit', '毛利'),
            ('avg_order_value', '客单价'),
            ('customer_count', '客户数'),
            ('contract_count', '合同数'),
        ]

        items = []
        for key, label in metrics:
            cur_val = Decimal(str(getattr(current, key, 0)))
            mom_val = Decimal(str(getattr(prev, key, 0))) if prev else Decimal('0')
            yoy_val = Decimal(str(getattr(last_year, key, 0))) if last_year else Decimal('0')

            mom_change = cur_val - mom_val
            yoy_change = cur_val - yoy_val
            mom_rate = float(mom_change / mom_val * 100) if mom_val else 0.0
            yoy_rate = float(yoy_change / yoy_val * 100) if yoy_val else 0.0

            items.append(
                OperationComparisonItemModel(
                    metric=key,
                    label=label,
                    current=cur_val,
                    previous=mom_val,
                    yoy_change=yoy_change,
                    yoy_rate=round(yoy_rate, 2),
                    mom_change=mom_change,
                    mom_rate=round(mom_rate, 2),
                ).model_dump(by_alias=True)
            )

        return OperationComparisonResponseModel(
            period=query.period,
            period_type='month',
            business_line=query.business_line,
            items=items,
        ).model_dump(by_alias=True)

    @staticmethod
    async def options_services(current_user: CurrentUserModel) -> dict[str, list[dict[str, str]]]:
        periods = [
            OperationTypeOptionModel(value=e.value, label=e.label(e.value)).model_dump(by_alias=True)
            for e in OperationPeriodEnum
        ]
        lines = [
            OperationTypeOptionModel(value=e.value, label=e.label(e.value)).model_dump(by_alias=True)
            for e in OperationBusinessLineEnum
        ]
        return {'periodTypes': periods, 'businessLines': lines}