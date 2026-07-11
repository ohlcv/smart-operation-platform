"""渠道 DAO：参数化 SQL，与 ORM 模型一一对应。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from module_biz.entity.do.channel_do import BizChannel


class ChannelDAO:
    @staticmethod
    async def insert(db: AsyncSession, channel: BizChannel) -> int:
        db.add(channel)
        await db.flush()
        return channel.id

    @staticmethod
    async def get_by_id(db: AsyncSession, channel_id: int) -> BizChannel | None:
        result = await db.execute(select(BizChannel).where(BizChannel.id == channel_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_channel_code(db: AsyncSession, channel_code: str, exclude_id: int | None = None) -> BizChannel | None:
        stmt = select(BizChannel).where(BizChannel.channel_code == channel_code)
        if exclude_id is not None:
            stmt = stmt.where(BizChannel.id != exclude_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_by_id(db: AsyncSession, channel_id: int, fields: dict[str, Any]) -> int:
        if not fields:
            return 0
        fields['update_time'] = datetime.now()
        result = await db.execute(
            update(BizChannel).where(BizChannel.id == channel_id).values(**fields)
        )
        return result.rowcount or 0

    @staticmethod
    async def delete_by_ids(db: AsyncSession, ids: list[int]) -> int:
        if not ids:
            return 0
        result = await db.execute(delete(BizChannel).where(BizChannel.id.in_(ids)))
        return result.rowcount or 0

    @staticmethod
    async def list_page(
        db: AsyncSession,
        *,
        keyword: str | None = None,
        category: str | None = None,
        status: int | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> tuple[list[BizChannel], int]:
        """分页查询渠道列表。

        keyword 命中：渠道编码、渠道名称、联系人、联系电话。
        """
        conds = []
        if category:
            conds.append(BizChannel.category == category)
        if status is not None:
            conds.append(BizChannel.status == status)
        if keyword:
            kw = f'%{keyword}%'
            conds.append(
                or_(
                    BizChannel.channel_code.like(kw),
                    BizChannel.channel_name.like(kw),
                    BizChannel.contact_name.like(kw),
                    BizChannel.contact_phone.like(kw),
                )
            )

        where_clause = and_(*conds) if conds else None

        count_stmt = select(func.count(BizChannel.id))
        if where_clause is not None:
            count_stmt = count_stmt.where(where_clause)
        total = (await db.execute(count_stmt)).scalar() or 0

        list_stmt = select(BizChannel)
        if where_clause is not None:
            list_stmt = list_stmt.where(where_clause)
        list_stmt = (
            list_stmt.order_by(BizChannel.sort_order.desc(), BizChannel.create_time.desc())
            .offset((page_num - 1) * page_size)
            .limit(page_size)
        )
        rows = list((await db.execute(list_stmt)).scalars().all())

        return rows, total

    @staticmethod
    async def get_max_channel_seq(db: AsyncSession) -> int:
        """取当前最大渠道序号（用于自动生成 QD-NNN）。"""
        result = await db.execute(
            select(func.max(BizChannel.id))
        )
        return result.scalar() or 0

    @staticmethod
    async def count_by_ids(db: AsyncSession, ids: list[int]) -> int:
        """查询多个 id 的渠道数量（用于校验关联合同删除时拦截）。"""
        if not ids:
            return 0
        result = await db.execute(
            select(func.count(BizChannel.id)).where(BizChannel.id.in_(ids))
        )
        return result.scalar() or 0
