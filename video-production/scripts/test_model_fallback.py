"""Real missing-model fallback acceptance on disposable, isolated port 8008."""
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

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "video-production"


def main() -> None:
    source = FILM / "runtime/qwen-data"
    target = FILM / "runtime/fallback-data"
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", 8008)) == 0:
            raise SystemExit("Port 8008 is occupied; no existing process was stopped")
    if target.exists() and any(target.iterdir()):
        raise SystemExit("Fallback data destination is not empty; no files were overwritten")
    shutil.copytree(source, target, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("wusheng.db", "wusheng.db-wal", "wusheng.db-shm"))
    with sqlite3.connect(f'file:{(source / "wusheng.db").as_posix()}?mode=ro', uri=True) as origin:
        with sqlite3.connect(target / "wusheng.db") as destination:
            origin.backup(destination)
    env = {**os.environ, "PYTHONUTF8": "1", "WUSHENG_DATA_DIR": str(target.resolve()),
           "WUSHENG_SHARE_MODE": "lan-ready", "WUSHENG_PORT": "8008", "WUSHENG_AI_PROVIDER": "ollama",
           "WUSHENG_OLLAMA_URL": "http://127.0.0.1:11434",
           "WUSHENG_OLLAMA_MODEL": "wusheng-not-installed-qa-model"}
    env.pop("WUSHENG_DB_URL", None)
    report = {"setup": "Real Ollama service with a deliberately non-installed model name",
              "port": 8008, "dataDirectory": str(target), "mocked": False}
    out = (FILM / "reports/fallback-server.stdout.log").open("w", encoding="utf-8")
    err = (FILM / "reports/fallback-server.stderr.log").open("w", encoding="utf-8")
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1",
                                "--port", "8008", "--no-proxy-headers", "--log-level", "warning"],
                               cwd=ROOT, env=env, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
    out.close()
    err.close()
    report["ownedProcessId"] = process.pid
    try:
        with httpx.Client(timeout=3, trust_env=False) as client:
            for _ in range(60):
                if process.poll() is not None:
                    raise RuntimeError("Fallback child exited during startup")
                try:
                    response = client.get("http://127.0.0.1:8008/health")
                    response.raise_for_status()
                    report["health"] = response.json()
                    break
                except httpx.HTTPError:
                    time.sleep(0.5)
            else:
                raise RuntimeError("Fallback health check did not complete")
            state = json.loads((FILM / "runtime/recording-state.json").read_text(encoding="utf-8"))
            started = time.monotonic()
            response = client.post("http://127.0.0.1:8008/generate",
                                   json={"itemId": state["itemId"], "question": "这件物品有哪些关联耗材？"}, timeout=15)
            response.raise_for_status()
            report["generate"] = response.json()
            report["seconds"] = round(time.monotonic() - started, 2)
            report["passed"] = all((report["health"]["activeProvider"] == "evidence",
                                    bool(report["health"]["fallbackReason"]),
                                    report["generate"]["activeProvider"] == "evidence",
                                    report["generate"]["modelInvoked"] is False,
                                    bool(report["generate"]["fallbackReason"]),
                                    "清洁液" in report["generate"]["answer"],
                                    "刀头" in report["generate"]["answer"]))
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        report["ownedProcessStopped"] = process.poll() is not None
        (FILM / "reports/model-unavailable-fallback.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
