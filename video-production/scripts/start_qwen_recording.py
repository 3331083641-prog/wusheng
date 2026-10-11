"""Snapshot the completed isolated recording archive and run Qwen on port 8007.

Run only after the UI recording database is ready. Production port 8000 and
production data are neither read for copying nor modified.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import time

import httpx

PROJECT = Path(__file__).resolve().parents[2]
FILM = PROJECT / "video-production"
SOURCE = (FILM / "runtime/data").resolve()
DESTINATION = (FILM / "runtime/qwen-data").resolve()
MODEL = "qwen3-vl:4b-instruct-q4_K_M"
PORT = 8007


def main() -> None:
    if SOURCE == (PROJECT / "data").resolve() or DESTINATION == SOURCE:
        raise SystemExit("Refusing a production or in-place snapshot")
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", PORT)) == 0:
            raise SystemExit("Port 8007 is already occupied; no existing process was stopped")
    if DESTINATION.exists() and any(DESTINATION.iterdir()):
        raise SystemExit("Qwen recording destination is not empty; no data was overwritten")
    source_db = SOURCE / "wusheng.db"
    if not source_db.is_file():
        raise SystemExit("UI recording database is missing")
    shutil.copytree(SOURCE, DESTINATION, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("wusheng.db", "wusheng.db-wal", "wusheng.db-shm"))
    with sqlite3.connect(f"file:{source_db.as_posix()}?mode=ro", uri=True) as source:
        with sqlite3.connect(DESTINATION / "wusheng.db") as target:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Snapshot integrity check failed")
    reports = FILM / "reports"
    stdout = (reports / "qwen-server.stdout.log").open("w", encoding="utf-8")
    stderr = (reports / "qwen-server.stderr.log").open("w", encoding="utf-8")
    env = {**os.environ, "PYTHONUTF8": "1", "WUSHENG_DATA_DIR": str(DESTINATION),
           "WUSHENG_SHARE_MODE": "lan-ready", "WUSHENG_PORT": str(PORT),
           "WUSHENG_AI_PROVIDER": "ollama", "WUSHENG_OLLAMA_MODEL": MODEL,
           "WUSHENG_OLLAMA_URL": "http://127.0.0.1:11434"}
    # A globally configured database URL must not override the isolated data dir.
    env.pop("WUSHENG_DB_URL", None)
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0",
                                "--port", str(PORT), "--no-proxy-headers", "--log-level", "warning"],
                               cwd=PROJECT, env=env, stdout=stdout, stderr=stderr,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    stdout.close()
    stderr.close()
    with httpx.Client(timeout=2, trust_env=False) as client:
        for _ in range(60):
            if process.poll() is not None:
                raise RuntimeError("Qwen recording backend exited; check its stderr log")
            try:
                response = client.get(f"http://127.0.0.1:{PORT}/health")
                response.raise_for_status()
                health = response.json()
                if health.get("activeProvider") == "ollama" and health.get("model") == MODEL:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        else:
            process.terminate()
            raise RuntimeError("Qwen backend health check failed; only the helper's child was stopped")
    state = {"pid": process.pid, "baseUrl": f"http://127.0.0.1:{PORT}",
             "sourceData": str(SOURCE), "snapshotData": str(DESTINATION), "health": health,
             "snapshotMethod": "SQLite online backup + unchanged local attachment copies"}
    (reports / "qwen-recording-service.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False))


if __name__ == "__main__":
    main()
