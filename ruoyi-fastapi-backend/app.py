import os
import sys

# Force UTF-8 locale BEFORE any other imports (macOS may default to ASCII/Latin-1)
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Reconfigure stdout/stderr immediately
import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import uvicorn

from config.env import AppConfig
from server import create_app

if __name__ != '__main__':
    app = create_app()

if __name__ == '__main__':
    uvicorn.run(
        app='server:create_app',
        host=AppConfig.app_host,
        port=AppConfig.app_port,
        root_path=AppConfig.app_root_path,
        reload=AppConfig.app_reload,
        workers=AppConfig.app_workers,
        factory=True,
    )
