import { useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Bell, Box, Calendar, Check, ShieldCheck, ShoppingBag, Wrench } from "lucide-react";
import { api, json } from "../api";
import { useStore } from "../store";
import { EmptyState, PageHeader, StatCard, StatusBadge } from "../components/ui";
import type { Reminder } from "../types";
const kinds = [
  ["全部", Bell, "green"],
  ["保修到期", ShieldCheck, "orange"],
  ["退换截止", ShoppingBag, "orange"],
  ["维护任务", Wrench, "blue"],
  ["耗材补给", Box, "purple"],
  ["其他", Calendar, "green"],
] as const;
export function ReminderRow({
  reminder,
  onAction,
}: {
  reminder: Reminder;
  onAction: (id: string, action: string) => void;
}) {
  const item = useStore((s) => s.data?.items.find((i) => i.id === reminder.itemId));
  return (
    <motion.article
      layout
      className="reminder-row"
      exit={{ opacity: 0, scale: 0.97, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.22 }}
    >
      <img src={item?.coverImage} alt="" />
      <div className="reminder-item">
        <b>{item?.name || "物品"}</b>
        <small>
          {item?.brand} · {item?.model}
        </small>
      </div>
      <div className="reminder-event">
        <StatusBadge
          tone={
            reminder.type === "耗材补给"
              ? "purple"
              : reminder.type === "维护任务"
                ? "blue"
                : "orange"
          }
        >
          {reminder.type}
        </StatusBadge>
        <small>{reminder.title}</small>
      </div>
      <div className="reminder-date">
        <Calendar size={18} />
        <span>
          {reminder.dueDate}
          <small className={reminder.daysLeft <= 2 ? "urgent-text" : ""}>
            {reminder.daysLeft < 0
              ? `已逾期 ${-reminder.daysLeft} 天`
              : `还剩 ${reminder.daysLeft} 天`}
          </small>
        </span>
      </div>
      <StatusBadge
        tone={reminder.daysLeft <= 2 ? "red" : reminder.daysLeft <= 7 ? "orange" : "blue"}
      >
        {reminder.priority}
      </StatusBadge>
      <div className="row-actions">
        <Link className="button outline" to={`/items/${reminder.itemId}`}>
          查看
        </Link>
        <button className="button secondary" onClick={() => onAction(reminder.id, "snooze")}>
          延后 7 天
        </button>
        <button className="button soft" onClick={() => onAction(reminder.id, "complete")}>
          <Check size={15} />
          已处理
        </button>
      </div>
    </motion.article>
  );
}
export default function Reminders() {
  const { data, refresh, notify } = useStore();
  const [filter, setFilter] = useState("全部");
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState("");
  const [sort, setSort] = useState("date");
  const reminders = data!.reminders.filter(
    (r) =>
      r.status === (completed ? "completed" : "pending") &&
      (filter === "全部" || r.type === filter),
  );
  const action = async (id: string, action: string) => {
    try {
      await api(`/reminders/${id}`, json("PATCH", { action, days: 7 }));
      await refresh();
      notify(action === "complete" ? "提醒已处理" : "已延后 7 天");
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const groups = [
    ["今天", reminders.filter((r) => r.daysLeft <= 0)],
    ["本周", reminders.filter((r) => r.daysLeft > 0 && r.daysLeft <= 7)],
    ["本月", reminders.filter((r) => r.daysLeft > 7 && r.daysLeft <= 30)],
    ["以后", reminders.filter((r) => r.daysLeft > 30)],
  ] as const;
  return (
    <main className="page">
      <PageHeader title="提醒中心" description="及时掌握物品的重要节点，让生活更轻松、更安心。" />
      <div className="stats-grid six">
        {kinds.map(([label, Icon, tone]) => (
          <StatCard
            label={label === "全部" ? "全部提醒" : label}
            value={
              data!.reminders.filter(
                (r) => r.status === "pending" && (label === "全部" || r.type === label),
              ).length
            }
            icon={Icon}
            tone={tone}
            key={label}
            onClick={() => setFilter(label)}
          />
        ))}
      </div>
      <div className="toolbar">
        <div className="filter-tabs">
          {kinds.map(([k]) => (
            <button className={k === filter ? "active" : ""} key={k} onClick={() => setFilter(k)}>
              {k}
            </button>
          ))}
        </div>
        <div className="view-tools">
          <label className="checkbox">
            <input
              type="checkbox"
              checked={completed}
              onChange={(e) => setCompleted(e.target.checked)}
            />
            已处理记录
          </label>
          <select aria-label="提醒排序" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="date">按到期时间</option>
            <option value="item">按物品名称</option>
          </select>
        </div>
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {groups
        .filter(([, rows]) => rows.length)
        .map(([title, rows]) => (
          <section className="reminder-group" key={title}>
            <h3>
              <span />
              {title}
              <small>{rows.length}</small>
            </h3>
            <AnimatePresence>
              {[...rows]
                .sort((a, b) =>
                  sort === "date"
                    ? a.dueDate.localeCompare(b.dueDate)
                    : a.itemId.localeCompare(b.itemId),
                )
                .map((r) => (
                  <ReminderRow reminder={r} key={r.id} onAction={(id, a) => void action(id, a)} />
                ))}
            </AnimatePresence>
          </section>
        ))}
      {!reminders.length && (
        <EmptyState
          title="暂时没有这类提醒"
          description="日期和维护记录会自动生成提醒，你也可以查看已处理记录。"
        />
      )}
      <p className="data-footnote">
        按本机日期 {data!.today} 实时计算。此版本提供站内提醒，未运行时不会发送系统通知。
      </p>
    </main>
  );
}
