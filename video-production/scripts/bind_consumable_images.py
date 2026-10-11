"""Pre-bind two owner-provided consumable images in the isolated film database.

This helper does not create consumables or stock records. The film QA must state
that images are pre-bound; all creation, association and stock actions are real
UI operations. It never targets the project's production data directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

import httpx

PRODUCTION = Path(__file__).resolve().parents[2]
FILM = PRODUCTION / "video-production"
ISOLATED = (FILM / "runtime/data").resolve()


def run(item_id: str, cleaner_id: str, heads_id: str, base_url: str) -> dict:
    parsed = urlsplit(base_url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.port != 8006:
        raise SystemExit("Only the explicitly isolated localhost:8006 service is permitted")
    database = ISOLATED / "wusheng.db"
    if database.resolve() == (PRODUCTION / "data/wusheng.db").resolve() or not database.is_file():
        raise SystemExit("Isolated recording database not found")
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    ids = [(cleaner_id, "cleaner.png"), (heads_id, "heads.png")]
    for ident, _ in ids:
        record = db.execute("SELECT * FROM consumables WHERE id=?", (ident,)).fetchone()
        if record is None or record["itemId"] != item_id:
            raise SystemExit(f"Consumable {ident} must already be created by UI for the recording item")
    backup = FILM / "runtime/before-consumable-image-binding.db"
    if not backup.exists():
        with sqlite3.connect(backup) as target:
            db.backup(target)
    results = []
    with httpx.Client(base_url=base_url, timeout=30, trust_env=False) as client:
        health = client.get("/health")
        health.raise_for_status()
        for ident, filename in ids:
            source = FILM / "assets" / filename
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            existing = db.execute(
                "SELECT id,assetMetadata FROM item_images WHERE itemId=? AND sha256=? AND type='other'",
                (item_id, digest),
            ).fetchone()
            if existing:
                image_id = existing["id"]
                file_path = f"/api/images/{image_id}"
            else:
                with source.open("rb") as image:
                    response = client.post(
                        f"/items/{item_id}/images",
                        files={"files": (filename, image, "image/png")},
                        data={"type": "other"},
                    )
                response.raise_for_status()
                image = response.json()[0]
                image_id, file_path = image["id"], image["filePath"]
            response = client.get(file_path)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != digest:
                raise RuntimeError("Uploaded image differs from original bytes")
            metadata = {
                "competitionDemo": True,
                "source": "用户指定的比赛演示素材",
                "originFilename": filename,
                "consumableId": ident,
                "bindingMethod": "耗材图片预置绑定；耗材新增、关联和库存操作为真实 UI 操作",
                "sha256": digest,
            }
            results.append({"consumableId": ident, "imageId": image_id, "filePath": file_path,
                            "sha256": digest, "metadata": metadata})
    with db:
        for result in results:
            db.execute("UPDATE consumables SET coverImage=? WHERE id=? AND itemId=?",
                       (result["filePath"], result["consumableId"], item_id))
            db.execute("UPDATE item_images SET assetMetadata=? WHERE id=? AND itemId=?",
                       (json.dumps(result["metadata"], ensure_ascii=False), result["imageId"], item_id))
    if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("SQLite integrity check failed")
    db.close()
    report = {"database": str(database), "itemId": item_id, "results": results,
              "disclosure": "耗材图片预置绑定；新增/关联/库存为 UI 真实操作"}
    (FILM / "reports/consumable-image-binding.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--cleaner-id", required=True)
    parser.add_argument("--heads-id", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8006")
    args = parser.parse_args()
    print(json.dumps(run(args.item_id, args.cleaner_id, args.heads_id, args.base_url), ensure_ascii=False))
