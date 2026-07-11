"""客户 Service 层（遵循 ADR D24：JSON 字段统一 camelCase）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.customer_dao import CustomerDAO
from module_biz.entity.do.customer_do import BizCustomer
from module_biz.entity.vo.customer_vo import (
    CustomerCreateModel,
    CustomerQueryModel,
    CustomerResponseModel,
    CustomerUpdateModel,
)
from module_biz.enums import CustomerTypeEnum


async def _next_customer_code(db: AsyncSession) -> str:
    """生成下一个业务编号 KH-NNN（NNN 自增 3 位）。"""
    seq = await CustomerDAO.get_max_customer_seq(db)
    return f'KH-{seq + 1:03d}'


def _to_response(c: BizCustomer) -> CustomerResponseModel:
    """DO → 响应 Pydantic 模型（ADR D24：返回 Pydantic，禁止返回裸 dict）。"""
    return CustomerResponseModel(
        id=c.id,
        customer_code=c.customer_code,
        customer_name=c.customer_name,
        customer_type=c.customer_type,
        customer_type_label=CustomerTypeEnum.label(c.customer_type) if c.customer_type else None,
        contact_name=c.contact_name,
        contact_phone=c.contact_phone,
        contact_email=c.contact_email,
        address=c.address,
        business_license=c.business_license,
        tax_no=c.tax_no,
        qualification_files=c.qualification_files,
        level=c.level,
        tags=c.tags,
        status=c.status,
        create_time=c.create_time,
        update_time=c.update_time,
        remark=c.remark,
    )


class CustomerService:
    @staticmethod
    async def list_services(
        db: AsyncSession,
        query: CustomerQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        rows, total = await CustomerDAO.list_page(
            db,
            keyword=query.keyword,
            customer_type=query.customer_type,
            level=query.level,
            status=query.status,
            page_num=query.page_num,
            page_size=query.page_size,
        )
        return {
            'rows': [_to_response(c).model_dump(by_alias=True) for c in rows],
            'total': total,
            'page_num': query.page_num,
            'page_size': query.page_size,
        }

    @staticmethod
    async def detail_services(db: AsyncSession, customer_id: int, current_user: CurrentUserModel) -> dict[str, Any]:
        c = await CustomerDAO.get_by_id(db, customer_id)
        if not c:
            raise ServiceException(message=f'客户ID {customer_id} 不存在', data='404')
        return _to_response(c).model_dump(by_alias=True)

    @staticmethod
    async def create_services(
        db: AsyncSession,
        payload: CustomerCreateModel,
        current_user: CurrentUserModel,
    ) -> int:
        uid = current_user.user.user_id if current_user and current_user.user else None

        # 业务编号处理：若前端未传，自动生成 KH-NNN
        customer_code = payload.customer_code
        if not customer_code:
            customer_code = await _next_customer_code(db)
        else:
            existed = await CustomerDAO.get_by_customer_code(db, customer_code)
            if existed:
                raise ServiceException(message=f'客户业务编号 {customer_code} 已存在', data='409')

        customer = BizCustomer(
            customer_code=customer_code,
            customer_name=payload.customer_name,
            customer_type=payload.customer_type,
            contact_name=payload.contact_name,
            contact_phone=payload.contact_phone,
            contact_email=payload.contact_email,
            address=payload.address,
            business_license=payload.business_license,
            tax_no=payload.tax_no,
            qualification_files=payload.qualification_files,
            level=payload.level,
            tags=payload.tags,
            status=payload.status,
            created_by=uid,
            create_time=datetime.now(),
            remark=payload.remark,
        )
        new_id = await CustomerDAO.insert(db, customer)
        await db.commit()
        return new_id

    @staticmethod
    async def update_services(
        db: AsyncSession,
        customer_id: int,
        payload: CustomerUpdateModel,
        current_user: CurrentUserModel,
    ) -> None:
        c = await CustomerDAO.get_by_id(db, customer_id)
        if not c:
            raise ServiceException(message=f'客户ID {customer_id} 不存在', data='404')
        fields = payload.model_dump(exclude_unset=True, exclude_none=False)
        fields.pop('id', None)
        fields.pop('customer_code', None)  # 业务编号不可通过 update 修改
        if not fields:
            return
        fields['update_by'] = current_user.user.user_name if current_user and current_user.user else ''
        await CustomerDAO.update_by_id(db, customer_id, fields)
        await db.commit()

    @staticmethod
    async def delete_services(db: AsyncSession, ids: list[int], current_user: CurrentUserModel) -> int:
        if not ids:
            return 0
        deleted = await CustomerDAO.delete_by_ids(db, ids)
        await db.commit()
        return deleted