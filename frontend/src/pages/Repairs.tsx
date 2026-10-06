import { useCallback, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Check, Clock, Plus, ShieldCheck, Sparkles, Wallet, Wrench } from "lucide-react";
import { api, json } from "../api";
import { useStore } from "../store";
import { Drawer, EmptyState, PageHeader, StatCard, StatusBadge } from "../components/ui";
import type { Repair } from "../types";
import ProductImage from "../components/ProductImage";
const statuses = ["待预约", "诊断中", "维修中", "已完成"];
export function RepairDrawer({ record, onClose }: { record: Repair; onClose: () => void }) {
  const { data, refresh, notify } = useStore();
  const item = data!.items.find((i) => i.id === record.itemId)!;
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <Drawer title={item.name} onClose={onClose}>
      <div className="repair-drawer-hero">
        <ProductImage item={item} alt="" priority />
        <div>
          <h3>{item.model}</h3>
          <StatusBadge>{record.status}</StatusBadge>
          <p>{record.issue}</p>
        </div>
      </div>
      <section className="drawer-section">
        <h3>维修进度</h3>
        <div className="repair-progress">
          {statuses.map((s, i) => (
            <div className={i <= statuses.indexOf(record.status) ? "active" : ""} key={s}>
              <span>{i < statuses.indexOf(record.status) ? <Check size={16} /> : i + 1}</span>
              <b>{s}</b>
              <small>
                {record.progress.find((p) => p.status === s)?.date.slice(0, 10) || "尚未进行"}
              </small>
            </div>
          ))}
        </div>
      </section>
      <dl className="drawer-facts">
        <div>
          <dt>报修日期</dt>
          <dd>{record.reportDate}</dd>
        </div>
        <div>
          <dt>维修方式</dt>
          <dd>{record.serviceType}</dd>
        </div>
        <div>
          <dt>维修费用</dt>
          <dd>¥ {record.cost}</dd>
        </div>
        <div>
          <dt>备注</dt>
          <dd>{record.description || "未记录"}</dd>
        </div>
      </dl>
      <section className="ai-advice">
        <h3>
          <Sparkles size={20} />
          可能原因与检查建议
        </h3>
        <p>
          先核对供电、安装环境与说明书中的检查步骤，并保存故障出现条件。当前资料不足以确定故障原因。
        </p>
        <small>涉及拆机、高压、燃气或危险电器，请停止自行处理并联系专业人员。</small>
      </section>
      <form
        className="drawer-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          const f = new FormData(e.currentTarget);
          try {
            await api(
              `/repairs/${record.id}`,
              json("PATCH", {
                status: f.get("status"),
                cost: Number(f.get("cost")),
                description: f.get("description"),
              }),
            );
            await refresh();
            notify("维修进度、生命周期与支出已同步");
            onClose();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          更新进度
          <select name="status" defaultValue={record.status}>
            {statuses.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          费用（元）
          <input
            name="cost"
            type="number"
            min="0"
            step="0.01"
            defaultValue={record.cost}
            required
          />
        </label>
        <label>
          维修说明
          <textarea name="description" defaultValue={record.description} maxLength={1000} />
        </label>
        <button className="button primary" disabled={busy}>
          保存维修进度
        </button>
        {error && (
          <p role="alert" className="form-error">
            {error}
          </p>
        )}
      </form>
      <p className="data-footnote">维修凭证可在物品详情的资料页上传 PDF。</p>
    </Drawer>
  );
}
export default function Repairs() {
  const { data, refresh, notify } = useStore();
  const [params] = useSearchParams();
  const [adding, setAdding] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter] = useState("全部状态");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const close = useCallback(() => {
    setAdding(false);
    setSelected(null);
    setError("");
  }, []);
  const repairs = data!.repairs.filter(
    (r) =>
      (filter === "全部状态" || filter === r.status) &&
      `${r.issue} ${data!.items.find((i) => i.id === r.itemId)?.name}`.includes(query),
  );
  const current = data!.repairs.find((r) => r.id === selected);
  return (
    <main className="page">
      <PageHeader
        title="维修记录"
        description="记录每一次修复，让每一件物品都能得到及时维护与照顾。"
        action={
          <button className="button primary" onClick={() => setAdding(true)}>
            <Plus size={18} />
            新增维修记录
          </button>
        }
      />
      <div className="stats-grid four">
        <StatCard
          label="维修中"
          value={data!.repairs.filter((r) => ["维修中", "诊断中"].includes(r.status)).length}
          icon={Wrench}
          tone="orange"
        />
        <StatCard
          label="已完成"
          value={data!.repairs.filter((r) => r.status === "已完成").length}
          icon={ShieldCheck}
        />
        <StatCard
          label="待预约"
          value={data!.repairs.filter((r) => r.status === "待预约").length}
          icon={Clock}
          tone="blue"
        />
        <StatCard
          label="本年维修支出"
          value={data!.stats.repairSpend}
          suffix="元"
          icon={Wallet}
          tone="purple"
        />
      </div>
      <div className="toolbar">
        <input
          aria-label="搜索维修记录"
          placeholder="搜索物品名称或问题描述…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          value={filter}
          aria-label="维修状态筛选"
          onChange={(e) => setFilter(e.target.value)}
        >
          <option>全部状态</option>
          {statuses.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </div>
      <div className="panel table-scroll">
        <table className="repair-table">
          <thead>
            <tr>
              {["物品", "问题描述", "报修日期", "处理状态", "维修方式", "费用", "备注", "操作"].map(
                (t) => (
                  <th key={t}>{t}</th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {repairs.map((r) => {
              const item = data!.items.find((i) => i.id === r.itemId)!;
              return (
                <tr key={r.id} onClick={() => setSelected(r.id)}>
                  <td>
                    <div className="table-item">
                      <ProductImage item={item} alt="" />
                      <section>
                        <b>{item.name}</b>
                        <small>
                          {item.brand} {item.model}
                        </small>
                      </section>
                    </div>
                  </td>
                  <td>{r.issue}</td>
                  <td>{r.reportDate}</td>
                  <td>
                    <StatusBadge
                      tone={
                        r.status === "已完成" ? "green" : r.status === "待预约" ? "blue" : "orange"
                      }
                    >
                      {r.status}
                    </StatusBadge>
                  </td>
                  <td>{r.serviceType}</td>
                  <td>¥ {r.cost}</td>
                  <td className="repair-note">{r.description || "—"}</td>
                  <td>
                    <button
                      className="icon-button"
                      aria-label={`查看${item.name}维修详情`}
                      onClick={() => setSelected(r.id)}
                    >
                      •••
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!repairs.length && <EmptyState />}
      </div>
      <p className="data-footnote">共 {repairs.length} 条记录 · 维修费用按实际录入统计</p>
      {current && <RepairDrawer record={current} onClose={close} />}
      {adding && (
        <Drawer title="新增维修记录" onClose={close}>
          <form
            className="drawer-form"
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              const f = new FormData(e.currentTarget);
              try {
                await api(
                  "/repairs",
                  json("POST", {
                    itemId: f.get("itemId"),
                    issue: f.get("issue"),
                    reportDate: f.get("reportDate"),
                    status: "待预约",
                    serviceType: f.get("serviceType"),
                    cost: Number(f.get("cost") || 0),
                    description: f.get("description"),
                  }),
                );
                await refresh();
                notify("维修记录已建立，生命周期已同步");
                close();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <label>
              物品
              <select name="itemId" defaultValue={params.get("item") || "washer"}>
                {data!.items.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              问题描述
              <input name="issue" required maxLength={250} />
            </label>
            <label>
              报修日期
              <input
                name="reportDate"
                type="date"
                required
                max={data!.today}
                defaultValue={data!.today}
              />
            </label>
            <label>
              维修方式
              <select name="serviceType">
                <option>官方售后</option>
                <option>线下维修店</option>
                <option>自行检查</option>
              </select>
            </label>
            <label>
              当前费用（元）
              <input name="cost" type="number" min="0" step="0.01" defaultValue="0" />
            </label>
            <label>
              备注
              <textarea name="description" maxLength={1000} />
            </label>
            <button className="button primary" disabled={busy}>
              创建报修记录
            </button>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
          </form>
        </Drawer>
      )}
    </main>
  );
}
