"""经营数据 DAO。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.operation_do import BizOperation


class OperationDAO:
    @staticmethod
    async def insert(db: AsyncSession, op: BizOperation) -> int:
        db.add(op)
        await db.flush()
        return op.id

    @staticmethod
    async def get_by_id(db: AsyncSession, op_id: int) -> BizOperation | None:
        result = await db.execute(select(BizOperation).where(BizOperation.id == op_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_unique(
        db: AsyncSession,
        period: str,
        period_type: str,
        business_line: str | None,
    ) -> BizOperation | None:
        stmt = select(BizOperation).where(
            BizOperation.period == period,
            BizOperation.period_type == period_type,
        )
        if business_line is None:
            stmt = stmt.where(BizOperation.business_line.is_(None))
        else:
            stmt = stmt.where(BizOperation.business_line == business_line)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_by_id(db: AsyncSession, op_id: int, fields: dict[str, Any]) -> int:
        if not fields:
            return 0
        fields['update_time'] = datetime.now()
        result = await db.execute(
            update(BizOperation).where(BizOperation.id == op_id).values(**fields)
        )
        return result.rowcount or 0

    @staticmethod
    async def delete_by_id(db: AsyncSession, op_id: int) -> int:
        result = await db.execute(delete(BizOperation).where(BizOperation.id == op_id))
        return result.rowcount or 0

    @staticmethod
    async def list_page(
        db: AsyncSession,
        *,
        period_type: str | None = None,
        business_line: str | None = None,
        period: str | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> tuple[list[BizOperation], int]:
        conds = []
        if period_type:
            conds.append(BizOperation.period_type == period_type)
        if business_line:
            conds.append(BizOperation.business_line == business_line)
        if period:
            conds.append(BizOperation.period == period)
        where_clause = and_(*conds) if conds else None

        count_stmt = select(func.count(BizOperation.id))
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        total = (await db.execute(count_stmt)).scalar() or 0

        list_stmt = select(BizOperation)
        if where_clause is not None:
            list_stmt = list_stmt.where(where_clause)
        list_stmt = list_stmt.order_by(BizOperation.period.desc(), BizOperation.create_time.desc()).offset((page_num - 1) * page_size).limit(page_size)
        rows = list((await db.execute(list_stmt)).scalars().all())
        return rows, total

    @staticmethod
    async def get_by_period_and_type(
        db: AsyncSession,
        period: str,
        period_type: str,
        business_line: str | None,
    ) -> BizOperation | None:
        """用于同比环比查询：根据 period 找同类型的历史数据。"""
        stmt = select(BizOperation).where(
            BizOperation.period == period,
            BizOperation.period_type == period_type,
        )
        if business_line is None:
            stmt = stmt.where(BizOperation.business_line.is_(None))
        else:
            stmt = stmt.where(BizOperation.business_line == business_line)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()