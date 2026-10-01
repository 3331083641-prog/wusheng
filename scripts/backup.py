"""Non-destructive local backup: consistent SQLite snapshot + uploaded files."""
from datetime import datetime
from pathlib import Path
import sqlite3
import shutil

root=Path(__file__).resolve().parents[1]
target=root/'backups'/datetime.now().strftime('%Y%m%d-%H%M%S')
target.mkdir(parents=True,exist_ok=False)
source=root/'data/wusheng.db'
if source.exists():
    with sqlite3.connect(source) as current,sqlite3.connect(target/'wusheng.db') as destination:
        current.backup(destination)
shutil.copytree(root/'data/uploads',target/'uploads',dirs_exist_ok=True)
print('Backup saved:',target)
