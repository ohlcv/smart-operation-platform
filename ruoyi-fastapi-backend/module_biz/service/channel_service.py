"""渠道 Service 层（遵循 ADR D24：JSON 字段统一 camelCase）。

业务规则：
- D09：渠道分类枚举与 sys_dict_data dict_type='channel_type' 一致（meituan/douyin/ctrip/tongcheng）
- D12：资质附件存本地文件系统，本期暂存 URL 列表（不入库文件内容）
- 删除拦截：若渠道关联合同（contract_ids 非空），禁止删除
- CSV 导入：跳过编码冲突（按 skip_duplicates 选择）
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_biz.dao.channel_dao import ChannelDAO
from module_biz.entity.do.channel_do import BizChannel
from module_biz.entity.vo.channel_vo import (
    ChannelCategoryOptionModel,
    ChannelCreateModel,
    ChannelImportItemModel,
    ChannelImportModel,
    ChannelQueryModel,
    ChannelResponseModel,
    ChannelUpdateModel,
)
from module_biz.enums import ChannelCategoryEnum


def _user_id(current_user: CurrentUserModel) -> int:
    if not current_user or not current_user.user:
        raise ServiceException(message='未识别当前用户')
    return current_user.user.user_id


def _user_name(current_user: CurrentUserModel) -> str | None:
    if current_user and current_user.user:
        return current_user.user.user_name or current_user.user.nick_name
    return None


async def _next_channel_code(db: AsyncSession) -> str:
    """生成下一个渠道编码 QD-NNN（3 位自增）。"""
    seq = await ChannelDAO.get_max_channel_seq(db)
    return f'QD-{seq + 1:03d}'


def _normalize_code(code: str | None) -> str:
    code = (code or '').strip()
    if not code:
        return ''
    if not re.match(r'^[A-Za-z0-9_\-]+$', code):
        raise ServiceException(message=f'渠道编码 "{code}" 只能包含字母数字下划线和短横线', data='400')
    return code


def _validate_category(category: str | None) -> str:
    if not category:
        raise ServiceException(message='渠道分类不能为空', data='400')
    valid = {e.value for e in ChannelCategoryEnum}
    if category not in valid:
        raise ServiceException(
            message=f'渠道分类 "{category}" 非法，必须是 {sorted(valid)} 之一',
            data='400',
        )
    return category


def _to_response(c: BizChannel) -> ChannelResponseModel:
    """DO → Pydantic 响应，禁止裸 dict。"""
    return ChannelResponseModel(
        id=c.id,
        channel_code=c.channel_code,
        channel_name=c.channel_name,
        category=c.category,
        category_label=ChannelCategoryEnum.label(c.category),
        contact_name=c.contact_name,
        contact_phone=c.contact_phone,
        contact_email=c.contact_email,
        platform_url=c.platform_url,
        account=c.account,
        commission_rate=c.commission_rate,
        sort_order=c.sort_order or 0,
        description=c.description,
        attachments=c.attachments,
        contract_ids=c.contract_ids,
        status=c.status,
        created_by=c.created_by,
        created_by_name=c.created_by_name,
        create_time=c.create_time,
        update_time=c.update_time,
        remark=c.remark,
    )


class ChannelService:
    @staticmethod
    async def list_services(
        db: AsyncSession,
        query: ChannelQueryModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        rows, total = await ChannelDAO.list_page(
            db,
            keyword=query.keyword,
            category=query.category,
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
    async def detail_services(db: AsyncSession, channel_id: int, current_user: CurrentUserModel) -> dict[str, Any]:
        c = await ChannelDAO.get_by_id(db, channel_id)
        if not c:
            raise ServiceException(message=f'渠道ID {channel_id} 不存在', data='404')
        return _to_response(c).model_dump(by_alias=True)

    @staticmethod
    async def create_services(
        db: AsyncSession,
        payload: ChannelCreateModel,
        current_user: CurrentUserModel,
    ) -> int:
        _validate_category(payload.category)

        code = _normalize_code(payload.channel_code)
        if not code:
            code = await _next_channel_code(db)

        existed = await ChannelDAO.get_by_channel_code(db, code)
        if existed:
            raise ServiceException(message=f'渠道编码 {code} 已存在', data='409')

        uid = _user_id(current_user)
        u_name = _user_name(current_user)

        channel = BizChannel(
            channel_code=code,
            channel_name=payload.channel_name,
            category=payload.category,
            contact_name=payload.contact_name,
            contact_phone=payload.contact_phone,
            contact_email=payload.contact_email,
            platform_url=payload.platform_url,
            account=payload.account,
            password=payload.password,
            commission_rate=payload.commission_rate,
            sort_order=payload.sort_order or 0,
            description=payload.description,
            attachments=payload.attachments,
            contract_ids=[],
            status=1,
            remark=payload.remark,
            created_by=uid,
            created_by_name=u_name,
            create_time=datetime.now(),
        )
        new_id = await ChannelDAO.insert(db, channel)
        await db.commit()
        return new_id

    @staticmethod
    async def update_services(
        db: AsyncSession,
        channel_id: int,
        payload: ChannelUpdateModel,
        current_user: CurrentUserModel,
    ) -> None:
        c = await ChannelDAO.get_by_id(db, channel_id)
        if not c:
            raise ServiceException(message=f'渠道ID {channel_id} 不存在', data='404')

        fields = payload.model_dump(exclude_unset=True, exclude_none=False)
        fields.pop('id', None)
        if 'category' in fields:
            _validate_category(fields['category'])

        if not fields:
            return

        fields['update_by'] = _user_name(current_user) or ''
        await ChannelDAO.update_by_id(db, channel_id, fields)
        await db.commit()

    @staticmethod
    async def delete_services(
        db: AsyncSession,
        ids: list[int],
        current_user: CurrentUserModel,
    ) -> int:
        if not ids:
            return 0
        deleted = 0
        for cid in ids:
            c = await ChannelDAO.get_by_id(db, cid)
            if not c:
                continue
            # 关联合同拦截（contract_ids 非空）
            if c.contract_ids and len(c.contract_ids) > 0:
                raise ServiceException(
                    message=f'渠道 {c.channel_name} 关联了 {len(c.contract_ids)} 个合同，请先解除关联后再删除',
                    data='409',
                )
            deleted += await ChannelDAO.delete_by_ids(db, [cid])
        await db.commit()
        return deleted

    @staticmethod
    async def category_options_services(db: AsyncSession, current_user: CurrentUserModel) -> list[dict[str, str]]:
        """返回渠道分类下拉选项。"""
        return [
            ChannelCategoryOptionModel(value=e.value, label=e.label(e.value)).model_dump(by_alias=True)
            for e in ChannelCategoryEnum
        ]

    @staticmethod
    async def import_services(
        db: AsyncSession,
        payload: ChannelImportModel,
        current_user: CurrentUserModel,
    ) -> dict[str, Any]:
        """CSV 导入（D09）。返回 {success, skipped, errors: [{row, error}]}"""
        success = 0
        skipped = 0
        errors: list[dict[str, Any]] = []

        for idx, item in enumerate(payload.items, start=1):
            try:
                _validate_category(item.category)
                code = _normalize_code(item.channel_code) or f'QD-{idx:03d}'

                existed = await ChannelDAO.get_by_channel_code(db, code)
                if existed:
                    if payload.skip_duplicates:
                        skipped += 1
                        continue
                    raise ServiceException(message=f'编码 {code} 已存在', data='409')

                ch = BizChannel(
                    channel_code=code,
                    channel_name=item.channel_name,
                    category=item.category,
                    contact_name=item.contact_name,
                    contact_phone=item.contact_phone,
                    commission_rate=item.commission_rate,
                    contract_ids=[],
                    status=1,
                    sort_order=0,
                    remark=item.remark,
                    created_by=_user_id(current_user),
                    created_by_name=_user_name(current_user),
                    create_time=datetime.now(),
                )
                await ChannelDAO.insert(db, ch)
                success += 1
            except ServiceException as e:
                errors.append({'row': idx, 'channelCode': item.channel_code, 'error': e.message})
            except Exception as e:  # noqa: BLE001
                errors.append({'row': idx, 'channelCode': item.channel_code, 'error': str(e)})

        await db.commit()
        return {
            'success': success,
            'skipped': skipped,
            'errors': errors,
            'total': len(payload.items),
        }
