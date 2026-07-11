"""财务 DAO。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, case, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.finance_do import BizBankStatement, BizFinanceEntry


class FinanceDAO:
    # ----------------- Entry -----------------

    @staticmethod
    async def insert_entry(db: AsyncSession, e: BizFinanceEntry) -> int:
        db.add(e)
        await db.flush()
        return e.id

    @staticmethod
    async def get_entry_by_id(db: AsyncSession, entry_id: int) -> BizFinanceEntry | None:
        result = await db.execute(select(BizFinanceEntry).where(BizFinanceEntry.id == entry_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_entry_by_no(db: AsyncSession, entry_no: str) -> BizFinanceEntry | None:
        result = await db.execute(select(BizFinanceEntry).where(BizFinanceEntry.entry_no == entry_no))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_entry_by_id(db: AsyncSession, entry_id: int, fields: dict[str, Any]) -> int:
        if not fields:
            return 0
        fields['update_time'] = datetime.now()
        result = await db.execute(
            update(BizFinanceEntry).where(BizFinanceEntry.id == entry_id).values(**fields)
        )
        return result.rowcount or 0

    @staticmethod
    async def delete_entry_by_id(db: AsyncSession, entry_id: int) -> int:
        result = await db.execute(delete(BizFinanceEntry).where(BizFinanceEntry.id == entry_id))
        return result.rowcount or 0

    @staticmethod
    async def list_entry_page(
        db: AsyncSession,
        *,
        keyword: str | None = None,
        entry_type: str | None = None,
        cleared: int | None = None,
        invoice_id: int | None = None,
        begin_date: date | None = None,
        end_date: date | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> tuple[list[BizFinanceEntry], int]:
        conds = []
        if entry_type:
            conds.append(BizFinanceEntry.entry_type == entry_type)
        if cleared is not None:
            conds.append(BizFinanceEntry.cleared == cleared)
        if invoice_id is not None:
            conds.append(BizFinanceEntry.invoice_id == invoice_id)
        if begin_date:
            conds.append(BizFinanceEntry.transaction_date >= begin_date)
        if end_date:
            conds.append(BizFinanceEntry.transaction_date <= end_date)
        if keyword:
            kw = f'%{keyword}%'
            conds.append(
                or_(
                    BizFinanceEntry.entry_no.like(kw),
                    BizFinanceEntry.invoice_no.like(kw),
                    BizFinanceEntry.contract_no.like(kw),
                    BizFinanceEntry.party_name.like(kw),
                )
            )
        where_clause = and_(*conds) if conds else None

        count_stmt = select(func.count(BizFinanceEntry.id))
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        total = (await db.execute(count_stmt)).scalar() or 0

        list_stmt = select(BizFinanceEntry)
        if where_clause is not None:
            list_stmt = list_stmt.where(where_clause)
        list_stmt = list_stmt.order_by(BizFinanceEntry.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size)
        rows = list((await db.execute(list_stmt)).scalars().all())
        return rows, total

    @staticmethod
    async def get_max_entry_seq(db: AsyncSession) -> int:
        result = await db.execute(select(func.max(BizFinanceEntry.id)))
        return result.scalar() or 0

    @staticmethod
    async def summary_by_period(
        db: AsyncSession,
        period: str,  # e.g. '2026-07'
    ) -> dict[str, Decimal]:
        """按月汇总：receivable/payable/cleared。"""
        stmt = select(
            func.coalesce(
                func.sum(case((BizFinanceEntry.entry_type == 'receivable', BizFinanceEntry.amount), else_=0)),
                0,
            ).label('receivable'),
            func.coalesce(
                func.sum(case((BizFinanceEntry.entry_type == 'payable', BizFinanceEntry.amount), else_=0)),
                0,
            ).label('payable'),
            func.coalesce(
                func.sum(case((BizFinanceEntry.cleared == 1, BizFinanceEntry.amount), else_=0)),
                0,
            ).label('cleared'),
        ).where(func.date_format(BizFinanceEntry.transaction_date, '%Y-%m') == period)

        result = (await db.execute(stmt)).one()
        receivable = result.receivable or Decimal('0.00')
        payable = result.payable or Decimal('0.00')
        cleared = result.cleared or Decimal('0.00')
        uncleared = receivable + payable - cleared
        return {
            'receivable_total': receivable,
            'payable_total': payable,
            'cleared_total': cleared,
            'uncleared_total': uncleared,
        }

    # ----------------- Bank Statement -----------------

    @staticmethod
    async def insert_statement(db: AsyncSession, s: BizBankStatement) -> int:
        db.add(s)
        await db.flush()
        return s.id

    @staticmethod
    async def list_unmatched_statements(db: AsyncSession, limit: int = 50) -> list[BizBankStatement]:
        stmt = (
            select(BizBankStatement)
            .where(BizBankStatement.matched == 0)
            .order_by(BizBankStatement.transaction_date.desc())
            .limit(limit)
        )
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def update_statement_match(db: AsyncSession, statement_id: int, entry_id: int) -> int:
        result = await db.execute(
            update(BizBankStatement)
            .where(BizBankStatement.id == statement_id)
            .values(matched=1, matched_entry_id=entry_id)
        )
        return result.rowcount or 0