"""合同 DAO：参数化 SQL，避免 ORM 复杂查询时的低效；与 ORM 模型一一对应。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.contract_do import BizContract


class ContractDAO:
    @staticmethod
    async def insert(db: AsyncSession, contract: BizContract) -> int:
        db.add(contract)
        await db.flush()
        return contract.id

    @staticmethod
    async def get_by_id(db: AsyncSession, contract_id: int) -> BizContract | None:
        result = await db.execute(select(BizContract).where(BizContract.id == contract_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_contract_no(db: AsyncSession, contract_no: str, exclude_id: int | None = None) -> BizContract | None:
        stmt = select(BizContract).where(BizContract.contract_no == contract_no)
        if exclude_id is not None:
            stmt = stmt.where(BizContract.id != exclude_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_by_id(db: AsyncSession, contract_id: int, fields: dict[str, Any]) -> int:
        if not fields:
            return 0
        fields['update_time'] = datetime.now()
        result = await db.execute(
            update(BizContract).where(BizContract.id == contract_id).values(**fields)
        )
        return result.rowcount or 0

    @staticmethod
    async def delete_by_ids(db: AsyncSession, ids: list[int]) -> int:
        if not ids:
            return 0
        result = await db.execute(delete(BizContract).where(BizContract.id.in_(ids)))
        return result.rowcount or 0

    @staticmethod
    async def list_page(
        db: AsyncSession,
        *,
        contract_no: str | None = None,
        title: str | None = None,
        contract_type: str | None = None,
        status: str | None = None,
        current_step: int | None = None,
        customer_id: int | None = None,
        keyword: str | None = None,
        begin_time: datetime | None = None,
        end_time: datetime | None = None,
        created_by: int | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> tuple[list[BizContract], int]:
        """分页查询合同列表。

        当 created_by 不为空时按 created_by 过滤（用于「我的合同」接口）；
        当 keyword 不为空时按合同编号/名称/客户/乙方模糊搜索。
        """

        conds = []
        if contract_no:
            conds.append(BizContract.contract_no.like(f'%{contract_no}%'))
        if title:
            conds.append(BizContract.title.like(f'%{title}%'))
        if contract_type:
            conds.append(BizContract.contract_type == contract_type)
        if status:
            conds.append(BizContract.status == status)
        if current_step is not None:
            conds.append(BizContract.current_step == current_step)
        if customer_id is not None:
            conds.append(BizContract.customer_id == customer_id)
        if created_by is not None:
            conds.append(BizContract.created_by == created_by)
        if keyword:
            kw = f'%{keyword}%'
            conds.append(
                or_(
                    BizContract.contract_no.like(kw),
                    BizContract.title.like(kw),
                    BizContract.customer_name.like(kw),
                    BizContract.party_b.like(kw),
                )
            )
        if begin_time:
            conds.append(BizContract.create_time >= begin_time)
        if end_time:
            conds.append(BizContract.create_time <= end_time)

        where_clause = and_(*conds) if conds else None

        count_stmt = select(func.count(BizContract.id))
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        list_stmt = select(BizContract)
        if where_clause is not None:
            list_stmt = list_stmt.where(where_clause)
        list_stmt = list_stmt.order_by(desc(BizContract.create_time)).offset((page_num - 1) * page_size).limit(page_size)
        rows_result = await db.execute(list_stmt)
        rows = list(rows_result.scalars().all())

        return rows, total