import { useCallback, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Bell, Box, Calendar, Clock, Plus, ShoppingBag, Sparkles } from "lucide-react";
import { api, json } from "../api";
import { useStore } from "../store";
import { Drawer, EmptyState, PageHeader, StatCard, StatusBadge } from "../components/ui";
import type { Consumable } from "../types";
export function ConsumableCard({
  consumable,
  onClick,
}: {
  consumable: Consumable;
  onClick: () => void;
}) {
  const item = useStore((s) => s.data?.items.find((i) => i.id === consumable.itemId));
  return (
    <button className="consumable-card" onClick={onClick}>
      <img src={consumable.coverImage} alt={consumable.name} />
      <section>
        <header>
          <h3>{consumable.name}</h3>
          <StatusBadge>{consumable.status}</StatusBadge>
        </header>
        <p>
          <Box size={14} />
          关联设备 <span>{item?.name}</span>
        </p>
        <p>
          <Box size={14} />
          当前库存{" "}
          <b>
            {consumable.currentStock} {consumable.unit}
          </b>
        </p>
        <p>
          <Clock size={14} />
          预计可用{" "}
          <b
            className={
              consumable.estimatedDaysLeft !== null && consumable.estimatedDaysLeft <= 14
                ? "urgent-text"
                : ""
            }
          >
            {consumable.estimatedDaysLeft === null
              ? "数据不足"
              : `${consumable.estimatedDaysLeft} 天`}
          </b>
        </p>
        <p>
          <Calendar size={14} />
          建议购买 <b>{consumable.suggestedPurchaseDate || "暂不预测"}</b>
        </p>
      </section>
    </button>
  );
}
export default function Consumables() {
  const { data, refresh, notify } = useStore();
  const [filter, setFilter] = useState("全部");
  const [selected, setSelected] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sort, setSort] = useState("days");
  const [action, setAction] = useState("use");
  const close = useCallback(() => {
    setSelected(null);
    setAdding(false);
    setError("");
  }, []);
  const current = data!.consumables.find((c) => c.id === selected);
  const consumables = data!.consumables
    .filter(
      (c) =>
        (filter === "全部" || c.status === filter) &&
        `${c.name} ${data!.items.find((i) => i.id === c.itemId)?.name}`.includes(query),
    )
    .sort((a, b) =>
      sort === "name"
        ? a.name.localeCompare(b.name)
        : (a.estimatedDaysLeft ?? Infinity) - (b.estimatedDaysLeft ?? Infinity),
    );
  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    try {
      if (adding) {
        await api(
          "/consumables",
          json("POST", {
            itemId: form.get("itemId"),
            name: form.get("name"),
            unit: form.get("unit"),
            currentStock: Number(form.get("stock")),
            warningStock: Number(form.get("warning")),
            leadDays: 7,
          }),
        );
      } else {
        await api(
          `/consumables/${current!.id}/${action === "use" ? "consume" : "restock"}`,
          json("POST", {
            date: form.get("date"),
            quantity: Number(form.get("quantity")),
            cost: Number(form.get("cost") || 0),
          }),
        );
      }
      await refresh();
      notify(
        adding
          ? "耗材已关联设备"
          : action === "use"
            ? "消耗已记录，预测与库存已更新"
            : "补货与支出已记录",
      );
      if (adding) close();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="page">
      <PageHeader
        title="耗材管理"
        description="从真实使用记录预测余量，及时补给，让生活持续运转。"
        action={
          <button className="button primary" onClick={() => setAdding(true)}>
            <Plus size={18} />
            关联耗材
          </button>
        }
      />
      <div className="stats-grid four">
        <StatCard label="耗材总数" value={data!.consumables.length} icon={Box} />
        <StatCard
          label="即将耗尽"
          value={data!.consumables.filter((c) => c.status === "即将耗尽").length}
          icon={Bell}
          tone="orange"
        />
        <StatCard
          label="建议补货"
          value={data!.consumables.filter((c) => c.status === "建议补货").length}
          icon={ShoppingBag}
          tone="blue"
        />
        <StatCard
          label="本月消耗"
          value={data!.stats.monthlyConsumption}
          suffix="单位"
          icon={Clock}
          tone="purple"
          note="不同耗材单位合计，仅作记录数量参考"
        />
      </div>
      <div className="toolbar">
        <div className="filter-tabs">
          {["全部", "即将耗尽", "建议补货", "正常", "数据不足"].map((f) => (
            <button className={filter === f ? "active" : ""} key={f} onClick={() => setFilter(f)}>
              {f}
            </button>
          ))}
        </div>
        <div className="view-tools">
          <input
            aria-label="搜索耗材"
            placeholder="搜索耗材或关联设备…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select aria-label="耗材排序" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="days">按预计可用天数</option>
            <option value="name">按名称</option>
          </select>
        </div>
      </div>
      <div className="consumables-grid">
        {consumables.map((c) => (
          <ConsumableCard consumable={c} onClick={() => setSelected(c.id)} key={c.id} />
        ))}
      </div>
      {!consumables.length && <EmptyState />}
      <p className="data-footnote">
        预测基于历史消耗及观察区间；无历史或零消耗时不预测。当前库存单独记录，补货不会被计为消耗。
      </p>
      {(current || adding) && (
        <Drawer title={adding ? "关联设备耗材" : current!.name} onClose={close}>
          {current && (
            <>
              <div className="consumable-drawer-hero">
                <img src={current.coverImage} alt="" />
                <section>
                  <StatusBadge>{current.status}</StatusBadge>
                  <h3>{data!.items.find((i) => i.id === current.itemId)?.name}</h3>
                  <p>
                    当前库存{" "}
                    <b>
                      {current.currentStock} {current.unit}
                    </b>
                  </p>
                  <p>
                    预计可用 <b>{current.estimatedDaysLeft ?? "未知"} 天</b>
                  </p>
                  <p>建议购买 {current.suggestedPurchaseDate || "数据不足"}</p>
                </section>
              </div>
              <section className="drawer-section">
                <h3>历史消耗趋势</h3>
                <div className="drawer-chart">
                  <ResponsiveContainer width="100%" height={210}>
                    <AreaChart
                      data={current.records.map((r) => ({
                        date: r.date.slice(5),
                        quantity: r.quantityUsed,
                      }))}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Area
                        dataKey="quantity"
                        name={`消耗量（${current.unit}）`}
                        stroke="#16A361"
                        fill="#ECF8F1"
                        animationDuration={650}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </section>
              <section className="ai-advice">
                <h3>
                  <Sparkles size={21} />
                  补给建议 · 历史规则
                </h3>
                <p>
                  {current.dailyRate
                    ? `观察期日均消耗 ${current.dailyRate.toFixed(3)} ${current.unit}。预计 ${current.estimatedDaysLeft} 天后耗尽，建议 ${current.suggestedPurchaseDate} 前补给。`
                    : "尚无足够历史，记录真实消耗后再预测。"}
                </p>
                <small>{current.method}，不是厂家寿命保证；使用强度改变时请调整记录。</small>
              </section>
              <div className="text-tabs">
                <button
                  className={action === "use" ? "active" : ""}
                  onClick={() => setAction("use")}
                >
                  记录消耗
                </button>
                <button
                  className={action === "restock" ? "active" : ""}
                  onClick={() => setAction("restock")}
                >
                  补充库存
                </button>
              </div>
            </>
          )}
          <form className="drawer-form" onSubmit={submit}>
            {adding ? (
              <>
                <label>
                  关联设备
                  <select aria-label="关联设备" name="itemId" required>
                    {data!.items.map((i) => (
                      <option value={i.id} key={i.id}>
                        {i.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  耗材名称
                  <input name="name" required maxLength={150} />
                </label>
                <label>
                  单位
                  <input name="unit" defaultValue="个" required maxLength={20} />
                </label>
                <label>
                  当前库存
                  <input name="stock" type="number" min="0" step="0.01" required />
                </label>
                <label>
                  低库存阈值
                  <input
                    name="warning"
                    type="number"
                    min="0"
                    step="0.01"
                    defaultValue="1"
                    required
                  />
                </label>
              </>
            ) : (
              <>
                <label>
                  记录日期
                  <input
                    type="date"
                    name="date"
                    required
                    max={data!.today}
                    defaultValue={data!.today}
                  />
                </label>
                <label>
                  {action === "use" ? "消耗数量" : "补货数量"}
                  <input type="number" name="quantity" min="0.01" step="0.01" required />
                </label>
                {action === "restock" && (
                  <label>
                    补货费用（元）
                    <input
                      name="cost"
                      type="number"
                      min="0"
                      step="0.01"
                      defaultValue="0"
                      required
                    />
                  </label>
                )}
              </>
            )}
            <button className="button primary" disabled={busy}>
              {busy ? "保存中…" : "保存记录"}
            </button>
            {error && (
              <p role="alert" className="form-error">
                {error}
              </p>
            )}
          </form>
        </Drawer>
      )}
    </main>
  );
}
