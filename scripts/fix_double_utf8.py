#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_double_utf8.py
==================

一键修复因「MySQL latin1 连接 + utf8mb4 字段」导致的双重 UTF-8 编码数据。

应用场景
--------
MySQL 容器启动时未指定字符集（或 `character_set_client=latin1`），
导致应用以 utf-8 字节发送的字符串被 server 误以为是 latin1 字节，
落库时被二次 utf-8 编码。

例如原始字符串 `系统管理` 的 UTF-8 字节是 `E7 B3 BB E7 BB 9F E7 AE A1 E7 90 86`，
经过错误链路后会变成 `C3 A7 C2 B3 C2 BB C3 A7 C2 BB C5 B8 ...`，
应用回读时显示为乱码 `ç³»ç»Ÿç®¡ç†`。

本脚本通过反向转码修复已被污染的数据。

链路与反转
--------
- 原始 S → utf-8 字节 B1
- server 按 latin1 (cp1252) 解读为字符序列 C
- 写入 utf8mb4 字段时重新 utf-8 编码为 B2

反转：
1. B2 → utf-8 decode → str s（含 cp1252 已定义的 Unicode 字符 + C1 控制字符）
2. 把 s 反查回原始 cp1252 字节
3. 把这些字节当 utf-8 解码 → 原始 S

用法
----
::

    # 仅预览（不写库）
    python3 scripts/fix_double_utf8.py --dry-run

    # 真正修复（连接参数走环境变量 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME）
    python3 scripts/fix_double_utf8.py

    # 自定义连接
    python3 scripts/fix_double_utf8.py --host 127.0.0.1 --port 13306 \
        --user root --password root --database ruoyi-fastapi

环境变量
--------
- DB_HOST      默认 127.0.0.1
- DB_PORT      默认 13306
- DB_USER      默认 root
- DB_PASSWORD  默认 root
- DB_NAME      默认 ruoyi-fastapi

依赖
----
- pymysql (``pip install pymysql``)

详细背景
--------
见 ``docs/04-开发/DEBUG/double-utf8-encoding-2026-07-11.md``
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable

import pymysql
from pymysql.cursors import Cursor

# Windows-1252 中 0x80-0x9F 的 Unicode 映射。
# MySQL 的 latin1 字符集实际上就是 cp1252，所以 server 在存储这些
# 高位字节时会自动按这个表映射到对应的 Unicode 字符（如 0x8B → U+2039 "‹"）。
CP1252_HIGH: dict[int, int] = {
    0x80: 0x20AC, 0x82: 0x201A, 0x83: 0x0192, 0x84: 0x201E, 0x85: 0x2026,
    0x86: 0x2020, 0x87: 0x2021, 0x88: 0x02C6, 0x89: 0x2030, 0x8A: 0x0160,
    0x8B: 0x2039, 0x8C: 0x0152, 0x8E: 0x017D, 0x91: 0x2018, 0x92: 0x2019,
    0x93: 0x201C, 0x94: 0x201D, 0x95: 0x2022, 0x96: 0x2013, 0x97: 0x2014,
    0x98: 0x02DC, 0x99: 0x2122, 0x9A: 0x0161, 0x9B: 0x203A, 0x9C: 0x0153,
    0x9E: 0x017E, 0x9F: 0x0178,
}
# 反向 Unicode codepoint → cp1252 字节
UNI_TO_CP1252: dict[int, int] = {cp: byte for byte, cp in CP1252_HIGH.items()}

# 需要修复的核心业务表 + 文本字段。生产环境如需扩展，补充到此即可。
DEFAULT_TABLES: dict[str, list[str]] = {
    "sys_menu":      ["menu_name", "route_name", "component", "path", "query", "icon", "perms", "remark"],
    "sys_dept":      ["dept_name"],
    "sys_role":      ["role_name", "role_key"],
    "sys_dict_type": ["dict_name"],
    "sys_dict_data": ["dict_label", "css_class", "list_class"],
    "sys_user":      ["nick_name"],
}


def reverse_double_utf8(s: str) -> str | None:
    """
    将双重 utf-8 编码的字符串反转回原始字符串。

    策略：把 s 当作 cp1252 字符序列反查回字节，再 utf-8 解码。
    - cp < 0x80：直接当 ASCII 字节
    - 0x80 <= cp < 0x100：直接当 cp1252 高位字节
    - cp >= 0x100：是 cp1252 高位的 Unicode 映射（如 U+2039），反查字节

    出现任何无法识别的字符会返回 None（不应被修复）。
    """
    if not s:
        return s
    # 已含中文，无需反转
    if any("\u4e00" <= ch <= "\u9fff" for ch in s):
        return s
    bytes_cp1252 = bytearray()
    for ch in s:
        cp = ord(ch)
        if cp < 0x100:
            bytes_cp1252.append(cp)
        elif cp in UNI_TO_CP1252:
            bytes_cp1252.append(UNI_TO_CP1252[cp])
        else:
            # 未知字符（含中文 emoji 等），可能是其他类型污染，跳过
            return None
    try:
        return bytes(bytes_cp1252).decode("utf-8")
    except UnicodeDecodeError:
        return None


def _looks_chinese(s: str) -> bool:
    return bool(s) and any("\u4e00" <= ch <= "\u9fff" for ch in s)


def _fetch_primary_key(cur: Cursor, table: str) -> str | None:
    cur.execute(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_KEY='PRI' LIMIT 1",
        (table,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def fix_table(
    cur: Cursor,
    table: str,
    columns: Iterable[str],
    dry_run: bool,
) -> tuple[int, int, tuple | None]:
    """修复单张表，返回 (总行数, 修复行数, 示例元组)。"""
    pk = _fetch_primary_key(cur, table)
    if not pk:
        print(f"  !! {table} 没主键，跳过")
        return 0, 0, None

    cols = list(columns)
    placeholders_select = ", ".join(["`%s`" % c for c in cols])
    cur.execute(f"SELECT `{pk}`, {placeholders_select} FROM `{table}`")
    rows = cur.fetchall()

    fixed = 0
    sample: tuple | None = None
    for row in rows:
        pid = row[0]
        new_vals: list = []
        changed = False
        for i, col in enumerate(cols):
            v = row[i + 1]
            if v is None:
                new_vals.append(None)
                continue
            candidate = reverse_double_utf8(v)
            if candidate is not None and candidate != v and _looks_chinese(candidate):
                changed = True
                new_vals.append(candidate)
                if sample is None:
                    sample = (col, v, candidate)
            else:
                new_vals.append(v)
        if changed:
            if not dry_run:
                set_clause = ", ".join(f"`{c}`=%s" for c in cols)
                cur.execute(
                    f"UPDATE `{table}` SET {set_clause} WHERE `{pk}`=%s",
                    new_vals + [pid],
                )
            fixed += 1
    return len(rows), fixed, sample


def main() -> int:
    parser = argparse.ArgumentParser(
        description="修复 MySQL「双重 utf-8 编码」污染数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="详细背景见 docs/04-开发/DEBUG/double-utf8-encoding-2026-07-11.md",
    )
    parser.add_argument("--host", default=os.environ.get("DB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DB_PORT", "13306")))
    parser.add_argument("--user", default=os.environ.get("DB_USER", "root"))
    parser.add_argument("--password", default=os.environ.get("DB_PASSWORD", "root"))
    parser.add_argument(
        "--database", default=os.environ.get("DB_NAME", "ruoyi-fastapi")
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅扫描不写入（强烈推荐先 dry-run 验证结果再正式跑）",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        default=None,
        help="指定要修复的表名子集，默认修复 DEFAULT_TABLES 中所有表",
    )
    args = parser.parse_args()

    print(f"连接 {args.user}@{args.host}:{args.port}/{args.database}（charset=utf8mb4）")
    print(f"模式: {'DRY-RUN（不写库）' if args.dry_run else '正式修复'}")
    print()

    try:
        conn = pymysql.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            charset="utf8mb4",
            autocommit=False,
        )
    except pymysql.MySQLError as e:
        print(f"连接失败: {e}", file=sys.stderr)
        return 1

    targets = args.tables or list(DEFAULT_TABLES.keys())
    total_rows = 0
    total_fixed = 0
    try:
        with conn.cursor() as cur:
            for tbl in targets:
                cols = DEFAULT_TABLES.get(tbl)
                if cols is None:
                    print(f"  !! {tbl} 不在 DEFAULT_TABLES 中，跳过")
                    continue
                rows, fixed, sample = fix_table(cur, tbl, cols, dry_run=args.dry_run)
                conn.commit()
                total_rows += rows
                total_fixed += fixed
                msg = f"{tbl}: 总行数={rows}, {'将修复' if args.dry_run else '修复'}行数={fixed}"
                if sample:
                    col, before, after = sample
                    msg += f"\n     示例 {col}:\n       修复前: {before!r}\n       修复后: {after!r}"
                print(msg)
    finally:
        conn.close()

    print()
    print(
        f"{'[预览]' if args.dry_run else '[已修复]'}总计扫描 {total_rows} 行，"
        f"{'将修复' if args.dry_run else '已修复'} {total_fixed} 行"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
