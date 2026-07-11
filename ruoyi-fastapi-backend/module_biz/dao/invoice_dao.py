"""发票 DAO：参数化 SQL。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.invoice_do import BizInvoice


class InvoiceDAO:
    @staticmethod
    async def insert(db: AsyncSession, inv: BizInvoice) -> int:
        db.add(inv)
        await db.flush()
        return inv.id

    @staticmethod
    async def get_by_id(db: AsyncSession, invoice_id: int) -> BizInvoice | None:
        result = await db.execute(select(BizInvoice).where(BizInvoice.id == invoice_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_invoice_no(db: AsyncSession, invoice_no: str, exclude_id: int | None = None) -> BizInvoice | None:
        stmt = select(BizInvoice).where(BizInvoice.invoice_no == invoice_no)
        if exclude_id is not None:
            stmt = stmt.where(BizInvoice.id != exclude_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_contract_id(db: AsyncSession, contract_id: int) -> BizInvoice | None:
        """1:1 关联，唯一合同只能有一张发票。"""
        result = await db.execute(select(BizInvoice).where(BizInvoice.contract_id == contract_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_by_id(db: AsyncSession, invoice_id: int, fields: dict[str, Any]) -> int:
        if not fields:
            return 0
        fields['update_time'] = datetime.now()
        result = await db.execute(
            update(BizInvoice).where(BizInvoice.id == invoice_id).values(**fields)
        )
        return result.rowcount or 0

    @staticmethod
    async def delete_by_id(db: AsyncSession, invoice_id: int) -> int:
        result = await db.execute(delete(BizInvoice).where(BizInvoice.id == invoice_id))
        return result.rowcount or 0

    @staticmethod
    async def list_page(
        db: AsyncSession,
        *,
        keyword: str | None = None,
        status: str | None = None,
        invoice_type: str | None = None,
        contract_id: int | None = None,
        begin_date: date | None = None,
        end_date: date | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> tuple[list[BizInvoice], int]:
        conds = []
        if status:
            conds.append(BizInvoice.status == status)
        if invoice_type:
            conds.append(BizInvoice.invoice_type == invoice_type)
        if contract_id is not None:
            conds.append(BizInvoice.contract_id == contract_id)
        if begin_date:
            conds.append(BizInvoice.issue_date >= begin_date)
        if end_date:
            conds.append(BizInvoice.issue_date <= end_date)
        if keyword:
            kw = f'%{keyword}%'
            conds.append(
                or_(
                    BizInvoice.invoice_no.like(kw),
                    BizInvoice.contract_no.like(kw),
                    BizInvoice.party_name.like(kw),
                )
            )

        where_clause = and_(*conds) if conds else None

        count_stmt = select(func.count(BizInvoice.id))
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        total = (await db.execute(count_stmt)).scalar() or 0

        list_stmt = select(BizInvoice)
        if where_clause is not None:
            list_stmt = list_stmt.where(where_clause)
        list_stmt = list_stmt.order_by(BizInvoice.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size)
        rows = list((await db.execute(list_stmt)).scalars().all())

        return rows, total

    @staticmethod
    async def get_max_invoice_seq(db: AsyncSession) -> int:
        """取发票序号（用于自动生成 FP-NNN）。"""
        result = await db.execute(select(func.max(BizInvoice.id)))
        return result.scalar() or 0
