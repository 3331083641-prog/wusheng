import { useRef, useState } from "react";
import { api } from "../api";
export default function LocalData() {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <section className="panel local-data">
      <h2>本地数据</h2>
      <p>完整备份包含数据库、物品图片与 PDF；请自行妥善保存。恢复会先生成恢复前备份。</p>
      <a className="button secondary" href="/api/backup" download>
        下载完整备份
      </a>
      <button className="button secondary" disabled={busy} onClick={() => input.current?.click()}>
        {busy ? "恢复中…" : "恢复备份"}
      </button>
      <input
        ref={input}
        className="visually-hidden"
        aria-label="选择备份 ZIP"
        type="file"
        accept=".zip,application/zip"
        disabled={busy}
        onChange={async (e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          if (!file || !confirm("恢复将替换当前档案。系统会先保存恢复前备份。确认恢复？")) return;
          setBusy(true);
          setError("");
          try {
            const body = new FormData();
            body.append("file", file);
            body.append("confirmation", "恢复备份");
            await api("/backup/restore", { method: "POST", body });
            location.reload();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      />
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
