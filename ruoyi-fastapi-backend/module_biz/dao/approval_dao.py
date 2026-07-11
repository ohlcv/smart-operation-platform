"""审批记录 DAO"""
from __future__ import annotations

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.approval_do import BizApproval


class ApprovalDAO:
    @staticmethod
    async def insert(db: AsyncSession, approval: BizApproval) -> int:
        db.add(approval)
        await db.flush()
        return approval.id

    @staticmethod
    async def list_by_contract(db: AsyncSession, contract_id: int) -> list[BizApproval]:
        stmt = (
            select(BizApproval)
            .where(BizApproval.contract_id == contract_id)
            .order_by(asc(BizApproval.approval_time))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())