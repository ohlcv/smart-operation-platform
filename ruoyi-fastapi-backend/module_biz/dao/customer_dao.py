"""客户 DAO"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.customer_do import BizCustomer


class CustomerDAO:
    @staticmethod
    async def insert(db: AsyncSession, customer: BizCustomer) -> int:
        db.add(customer)
        await db.flush()
        return customer.id

    @staticmethod
    async def get_by_id(db: AsyncSession, customer_id: int) -> BizCustomer | None:
        result = await db.execute(select(BizCustomer).where(BizCustomer.id == customer_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_customer_code(db: AsyncSession, customer_code: str) -> BizCustomer | None:
        result = await db.execute(
            select(BizCustomer).where(BizCustomer.customer_code == customer_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_max_customer_seq(db: AsyncSession) -> int:
        """查询当前最大的 customer_code 序号（KH-NNN 中 NNN 部分），返回数字。

        无记录或解析失败时返回 0。
        """
        import re

        result = await db.execute(
            select(BizCustomer.customer_code).where(BizCustomer.customer_code.is_not(None))
        )
        codes = [row[0] for row in result.all() if row[0]]
        max_seq = 0
        for code in codes:
            m = re.match(r'^KH-(\d+)$', code)
            if m:
                max_seq = max(max_seq, int(m.group(1)))
        return max_seq

    @staticmethod
    async def update_by_id(db: AsyncSession, customer_id: int, fields: dict[str, Any]) -> int:
        if not fields:
            return 0
        fields['update_time'] = datetime.now()
        result = await db.execute(
            update(BizCustomer).where(BizCustomer.id == customer_id).values(**fields)
        )
        return result.rowcount or 0

    @staticmethod
    async def delete_by_ids(db: AsyncSession, ids: list[int]) -> int:
        if not ids:
            return 0
        result = await db.execute(delete(BizCustomer).where(BizCustomer.id.in_(ids)))
        return result.rowcount or 0

    @staticmethod
    async def list_page(
        db: AsyncSession,
        *,
        keyword: str | None = None,
        customer_type: str | None = None,
        level: str | None = None,
        status: int | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> tuple[list[BizCustomer], int]:
        conds = []
        if keyword:
            kw = f'%{keyword}%'
            conds.append(
                or_(
                    BizCustomer.customer_code.like(kw),
                    BizCustomer.customer_name.like(kw),
                    BizCustomer.contact_name.like(kw),
                    BizCustomer.contact_phone.like(kw),
                )
            )
        if customer_type:
            conds.append(BizCustomer.customer_type == customer_type)
        if level:
            conds.append(BizCustomer.level == level)
        if status is not None:
            conds.append(BizCustomer.status == status)

        where_clause = and_(*conds) if conds else None

        count_stmt = select(func.count(BizCustomer.id))
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        total = (await db.execute(count_stmt)).scalar() or 0

        list_stmt = select(BizCustomer)
        if where_clause is not None:
            list_stmt = list_stmt.where(where_clause)
        list_stmt = list_stmt.order_by(desc(BizCustomer.create_time)).offset((page_num - 1) * page_size).limit(page_size)
        rows = list((await db.execute(list_stmt)).scalars().all())

        return rows, total