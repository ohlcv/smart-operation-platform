#!/usr/bin/env bash
# =============================================================================
# clean-cache.sh
#   清理 smart-operation-platform 仓库的所有 Python/Node 构建缓存与脏文件，
#   防止宿主机缓存污染 Docker 镜像（重点是 alembic 的 cpython-XX.pyc）。
#
# 用法：
#   ./clean-cache.sh            # 清理缓存（保留日志）
#   ./clean-cache.sh --logs     # 同时清理后端日志（容器会重新生成）
#   ./clean-cache.sh --dry-run  # 只显示要删的内容，不实际删除
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CLEAN_LOGS=0
DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --logs) CLEAN_LOGS=1 ;;
        --dry-run) DRY_RUN=1 ;;
        -h|--help)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *)
            echo "未知参数: $arg" >&2
            echo "用法: $0 [--logs] [--dry-run]" >&2
            exit 2
            ;;
    esac
done

# 颜色
if [[ -t 1 ]]; then
    C_RED='\033[31m'; C_YEL='\033[33m'; C_GRN='\033[32m'; C_DIM='\033[2m'; C_RST='\033[0m'
else
    C_RED=''; C_YEL=''; C_GRN=''; C_DIM=''; C_RST=''
fi

# 统计
TOTAL_FOUND=0
TOTAL_DELETED=0
TOTAL_BYTES=0

# -----------------------------------------------------------------------------
# 单条清理规则
#   用法: clean_pattern "<描述>" <路径...>
# -----------------------------------------------------------------------------
clean_pattern() {
    local desc="$1"; shift
    local targets=("$@")
    local found_count=0
    local deleted_count=0
    local pattern_args=()

    # 收集 find 参数（相对路径，排除 .git/.venv 等保护目录）
    for target in "${targets[@]}"; do
        pattern_args+=( -name "$target" )
    done

    local -a extra_args=()
    if [[ $DRY_RUN -eq 1 ]]; then
        # dry-run：只列文件
        local files
        files=$(find . \
            \( -path './.git' -o -path './.venv' -o -path './venv' -o -path './node_modules' \) -prune -o \
            \( "${pattern_args[@]}" \) -type f -print 2>/dev/null || true)
        if [[ -n "$files" ]]; then
            found_count=$(echo "$files" | wc -l | tr -d ' ')
            echo -e "${C_DIM}  [dry-run]${C_RST} $desc: 匹配 $found_count 个"
            while IFS= read -r f; do
                [[ -z "$f" ]] && continue
                echo "    $f"
            done <<< "$files"
            TOTAL_FOUND=$((TOTAL_FOUND + found_count))
        fi
        return
    fi

    # 实际删除（先 dry 出列表再删，避免 find -delete 静默失败）
    local files
    files=$(find . \
        \( -path './.git' -o -path './.venv' -o -path './venv' -o -path './node_modules' \) -prune -o \
        \( "${pattern_args[@]}" \) -type f -print 2>/dev/null || true)

    if [[ -z "$files" ]]; then
        echo -e "${C_DIM}  [skip]${C_RST} $desc: 无匹配"
        return
    fi

    while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        found_count=$((found_count + 1))
        if rm -f "$f" 2>/dev/null; then
            deleted_count=$((deleted_count + 1))
            TOTAL_BYTES=$((TOTAL_BYTES + $(stat -f%z "$f" 2>/dev/null || echo 0)))
        else
            echo -e "${C_RED}  [error]${C_RST} 删除失败: $f"
        fi
    done <<< "$files"

    echo -e "${C_GRN}  [ok]${C_RST} $desc: 删除 $deleted_count / 匹配 $found_count"
    TOTAL_FOUND=$((TOTAL_FOUND + found_count))
    TOTAL_DELETED=$((TOTAL_DELETED + deleted_count))
}

# -----------------------------------------------------------------------------
# 目录清理（递归删整棵树）
#   用法: clean_dir "<描述>" <目录名...>
# -----------------------------------------------------------------------------
clean_dir() {
    local desc="$1"; shift
    local targets=("$@")
    local -a dirs=()
    local found_count=0
    local deleted_count=0

    for target in "${targets[@]}"; do
        # 限深 6 层，保护意外命中
        while IFS= read -r d; do
            [[ -z "$d" ]] && continue
            dirs+=("$d")
        done < <(find . -maxdepth 6 \
            \( -path './.git' -o -path './.venv' -o -path './venv' -o -path './node_modules' \) -prune -o \
            -type d -name "$target" -print 2>/dev/null || true)
    done

    if [[ ${#dirs[@]} -eq 0 ]]; then
        echo -e "${C_DIM}  [skip]${C_RST} $desc: 无匹配"
        return
    fi

    found_count=${#dirs[@]}
    for d in "${dirs[@]}"; do
        # 统计字节数
        local size
        size=$(du -sk "$d" 2>/dev/null | awk '{print $1}')
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "    [dry-run] $d  ($size KB)"
        else
            if rm -rf "$d" 2>/dev/null; then
                deleted_count=$((deleted_count + 1))
                TOTAL_BYTES=$((TOTAL_BYTES + ${size:-0} * 1024))
            else
                echo -e "${C_RED}  [error]${C_RST} 删除失败: $d"
            fi
        fi
    done

    if [[ $DRY_RUN -eq 1 ]]; then
        echo -e "${C_DIM}  [dry-run]${C_RST} $desc: 匹配 $found_count 个目录"
    else
        echo -e "${C_GRN}  [ok]${C_RST} $desc: 删除 $deleted_count / 匹配 $found_count"
    fi
    TOTAL_FOUND=$((TOTAL_FOUND + found_count))
    TOTAL_DELETED=$((TOTAL_DELETED + deleted_count))
}

# -----------------------------------------------------------------------------
# 主流程
# -----------------------------------------------------------------------------
echo "================================================================"
echo "  smart-operation-platform 缓存清理"
if [[ $DRY_RUN -eq 1 ]]; then
    echo "  模式: DRY-RUN（不会实际删除）"
fi
if [[ $CLEAN_LOGS -eq 1 ]]; then
    echo "  选项: 同时清理后端日志"
fi
echo "  工作目录: $SCRIPT_DIR"
echo "================================================================"

echo ""
echo -e "${C_YEL}[1/6] Python __pycache__ 与 .pyc/.pyo${C_RST}"
clean_pattern "__pycache__ 目录" "__pycache__"
clean_pattern ".pyc 文件"    "*.pyc"
clean_pattern ".pyo 文件"    "*.pyo"

echo ""
echo -e "${C_YEL}[2/6] macOS / 测试覆盖率 / Linter 缓存${C_RST}"
clean_pattern ".DS_Store" ".DS_Store"
clean_pattern ".coverage" ".coverage"
clean_pattern ".coverage.*" ".coverage.*"
clean_pattern ".pytest_cache" ".pytest_cache"
clean_pattern ".mypy_cache" ".mypy_cache"
clean_pattern ".ruff_cache" ".ruff_cache"
clean_pattern ".hypothesis" ".hypothesis"

echo ""
echo -e "${C_YEL}[3/6] 前端构建缓存${C_RST}"
clean_dir "dist 目录"   "dist"
clean_dir "build 目录"  "build"
clean_pattern ".eslintcache" ".eslintcache"
clean_pattern ".stylelintcache" ".stylelintcache"
clean_pattern ".cache" ".cache"

echo ""
echo -e "${C_YEL}[4/6] Egg-info / pip 元数据${C_RST}"
clean_pattern "*.egg-info" "*.egg-info"
clean_pattern "*.egg" "*.egg"
clean_dir ".eggs 目录" ".eggs"

echo ""
echo -e "${C_YEL}[5/6] HTML 报告 / 临时文件${C_RST}"
clean_dir "htmlcov 目录" "htmlcov"
clean_pattern "*.log.tmp" "*.log.tmp"
clean_pattern "*.tmp" "*.tmp"
clean_pattern ".mypy.ini.tmp" ".mypy.ini.tmp"

echo ""
if [[ $CLEAN_LOGS -eq 1 ]]; then
    echo -e "${C_YEL}[6/6] 后端日志（--logs 已开启）${C_RST}"
    clean_pattern "backend.log" "backend.log"
    clean_dir "logs/2026" "2026"
else
    echo -e "${C_DIM}[6/6] 后端日志（默认跳过，加 --logs 清理）${C_RST}"
    echo -e "${C_DIM}       注：日志通常不含缓存污染，但包含历史堆栈，可能误判 alembic 失败${C_RST}"
fi

echo ""
echo "================================================================"
if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "  ${C_YEL}DRY-RUN 完成${C_RST}：匹配到 ${TOTAL_FOUND} 个条目，未删除任何文件"
    echo "  重跑: ./clean-cache.sh  (不带 --dry-run 实际执行)"
else
    if [[ $TOTAL_DELETED -gt 0 ]]; then
        human=$(numfmt --to=iec --suffix=B "$TOTAL_BYTES" 2>/dev/null || echo "${TOTAL_BYTES} bytes")
        echo -e "  ${C_GRN}完成${C_RST}：删除 ${TOTAL_DELETED} / ${TOTAL_FOUND} 个条目，释放 ${human}"
    else
        echo -e "  ${C_GRN}完成${C_RST}：没有需要清理的内容"
    fi
    echo ""
    echo "  下一步："
    echo "    ./start-dev.sh --docker --rebuild"
fi
echo "================================================================"