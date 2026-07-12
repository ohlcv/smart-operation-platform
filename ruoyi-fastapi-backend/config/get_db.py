from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal, async_engine
from utils.log_util import logger


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接。

    使用 async def 与 AsyncSessionLocal().async with 保持一致；
    FastAPI 的 Depends(get_db) 自动支持 async generator。
    """
    async with AsyncSessionLocal() as current_db:
        yield current_db


async def run_alembic_upgrade() -> None:
    """
    应用启动时执行 Alembic upgrade head（v4.0 新增）

    通过 alembic.ini + env.py + alembic/versions/*.py 自动检测并应用未执行的迁移。
    使用同步驱动（pymysql / psycopg2）调用，避免 async 驱动与 alembic 事务模型冲突。

    失败行为：抛出异常，让应用启动失败（fail-fast）。
    """
    import os
    import subprocess

    logger.info('🔄 执行 alembic upgrade head...')
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        ['alembic', '-c', os.path.join(backend_dir, 'alembic.ini'), 'upgrade', 'head'],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f'❌ alembic upgrade head 失败: {result.stderr}')
        raise RuntimeError(f'alembic upgrade head failed: {result.stderr}')
    logger.info(f'✅ alembic upgrade head 成功\n{result.stdout.strip()}')


async def close_async_engine() -> None:
    """
    应用关闭时释放数据库连接池

    :return:
    """
    await async_engine.dispose()
