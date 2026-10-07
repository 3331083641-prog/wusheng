import { useState } from "react";
import { api, json } from "../api";
import type { Maintenance, Consumable, Repair } from "../types";
import { Drawer } from "./ui";
export function MaintenanceTools({
  record,
  reload,
}: {
  record: Maintenance;
  reload: () => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      await reload();
      setEditing(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <button className="button secondary" onClick={() => setEditing(true)}>
        编辑维护
      </button>
      <button
        className="button secondary"
        disabled={busy}
        onClick={() => {
          if (confirm("删除这条维护记录并重新计算提醒？"))
            void act(() => api(`/maintenance/${record.id}`, { method: "DELETE" }));
        }}
      >
        删除维护
      </button>
      {error && <p role="alert">{error}</p>}
      {editing && (
        <Drawer title="编辑维护记录" onClose={() => setEditing(false)}>
          <form
            className="drawer-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              void act(() =>
                api(
                  `/maintenance/${record.id}`,
                  json("PUT", {
                    type: f.get("type"),
                    date: f.get("date"),
                    intervalDays: Number(f.get("intervalDays")),
                    cost: Number(f.get("cost")),
                    description: f.get("description"),
                  }),
                ),
              );
            }}
          >
            {[
              ["type", "维护内容", "text", record.type],
              ["date", "维护日期", "date", record.date],
              ["intervalDays", "周期天数", "number", record.intervalDays],
              ["cost", "费用（元）", "number", record.cost],
              ["description", "说明", "text", record.description],
            ].map(([name, label, type, value]) => (
              <label key={name}>
                {label}
                <input
                  name={String(name)}
                  type={String(type)}
                  defaultValue={value}
                  required={name !== "description"}
                  min={name === "intervalDays" ? 1 : 0}
                  step={name === "cost" ? "0.01" : undefined}
                />
              </label>
            ))}
            <button className="button primary" disabled={busy}>
              保存维护修改
            </button>
          </form>
        </Drawer>
      )}
    </>
  );
}
export function ConsumableHistory({
  consumable,
  reload,
}: {
  consumable: Consumable;
  reload: () => Promise<void>;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const undo = async (path: string) => {
    if (!confirm("撤销这条记录，并同步库存、支出和预测？")) return;
    setBusy(true);
    try {
      await api(path, { method: "DELETE" });
      await reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="drawer-section">
      <h3>使用与补货历史</h3>
      {error && <p role="alert">{error}</p>}
      {consumable.records
        .filter((r) => r.quantityUsed > 0)
        .map((r) => (
          <p key={r.id}>
            {r.date} · 消耗 {r.quantityUsed} {consumable.unit}{" "}
            <button disabled={busy} onClick={() => void undo(`/consumption-records/${r.id}`)}>
              撤销消耗
            </button>
          </p>
        ))}
      {consumable.restocks.map((r) => (
        <p key={r.id}>
          {r.date} · 补货 {r.quantity} {consumable.unit} · ¥{r.cost}{" "}
          <button disabled={busy} onClick={() => void undo(`/restock-records/${r.id}`)}>
            撤销补货
          </button>
        </p>
      ))}
      <p>撤销后库存会为负的补货记录不能撤销。</p>
    </section>
  );
}
export function RepairCorrection({
  record,
  reload,
}: {
  record: Repair;
  reload: () => Promise<void>;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <details>
      <summary>纠正费用、说明或维修方式（不改变进度）</summary>
      <form
        className="drawer-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          const f = new FormData(e.currentTarget);
          try {
            await api(
              `/repairs/${record.id}/details`,
              json("PATCH", {
                cost: Number(f.get("cost")),
                description: f.get("description"),
                serviceType: f.get("serviceType"),
              }),
            );
            await reload();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          维修方式
          <select name="serviceType" defaultValue={record.serviceType}>
            {["官方售后", "线下维修店", "自行检查"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          纠正费用
          <input type="number" name="cost" min="0" step="0.01" defaultValue={record.cost} />
        </label>
        <label>
          纠正说明
          <textarea name="description" defaultValue={record.description} />
        </label>
        <button className="button secondary" disabled={busy}>
          保存记录纠正
        </button>
        {error && <p role="alert">{error}</p>}
      </form>
    </details>
  );
}
