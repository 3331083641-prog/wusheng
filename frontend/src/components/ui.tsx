import { useEffect, useRef, useState, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Check, ChevronRight, Package, X, type LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import type { Item, Event } from "../types";
import ProductImage from "./ProductImage";

export function Logo() {
  return (
    <Link className="logo" to="/" aria-label="物生首页">
      <span className="logo-symbol">
        <img
          src="/assets/branding/wusheng-eco-ring-logo.png"
          alt=""
          width={36}
          height={36}
        />
      </span>
      <b>物生</b>
    </Link>
  );
}
export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </header>
  );
}
export function CountUp({ value }: { value: number }) {
  const [n, setN] = useState(value);
  const ref = useRef<HTMLSpanElement>(null);
  const reduce = useReducedMotion();
  useEffect(() => {
    if (reduce) {
      setN(value);
      return;
    }
    let start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min((now - start) / 650, 1);
      setN(Math.round(value * (1 - (1 - t) ** 3)));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    const ob = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        start = performance.now();
        frame = requestAnimationFrame(tick);
        ob.disconnect();
      }
    });
    if (ref.current) ob.observe(ref.current);
    return () => {
      ob.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value, reduce]);
  return <span ref={ref}>{n.toLocaleString()}</span>;
}
export function StatCard({
  label,
  value,
  icon: Icon = Package,
  tone = "green",
  suffix = "",
  note,
  onClick,
}: {
  label: string;
  value: number;
  icon?: LucideIcon;
  tone?: string;
  suffix?: string;
  note?: string;
  onClick?: () => void;
}) {
  const inner = (
    <>
      <span className={`icon-well ${tone}`}>
        <Icon size={27} />
      </span>
      <div>
        <span className="stat-label">{label}</span>
        <strong>
          <CountUp value={value} />
          <small>{suffix}</small>
        </strong>
        {note && <p>{note}</p>}
      </div>
      {onClick && <ChevronRight className="stat-arrow" size={18} />}
    </>
  );
  return onClick ? (
    <button className="stat-card" onClick={onClick}>
      {inner}
    </button>
  ) : (
    <div className="stat-card">{inner}</div>
  );
}
export function StatusBadge({ children, tone }: { children: ReactNode; tone?: string }) {
  const text = typeof children === "string" ? children : "";
  return (
    <span
      className={`badge ${tone || (text.includes("维修") || text.includes("维护") || text.includes("耗尽") ? "orange" : text.includes("补") ? "purple" : "green")}`}
    >
      {children}
    </span>
  );
}
export function ItemCard({
  item,
  list = false,
  priority = false,
}: {
  item: Item;
  list?: boolean;
  priority?: boolean;
}) {
  return (
    <motion.article
      layout
      className={`item-card ${list ? "list" : ""}`}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.18 }}
    >
      <Link to={`/items/${item.id}`}>
        <div className="item-picture">
          {item.coverImage ? (
            <ProductImage item={item} priority={priority} />
          ) : (
            <div className="photo-empty">
              <Package size={36} />
              <span>尚未添加照片</span>
            </div>
          )}
          <StatusBadge>
            {item.status === "正常使用" &&
            item.warrantyDaysLeft !== null &&
            item.warrantyDaysLeft >= 0
              ? "保修中"
              : item.status}
          </StatusBadge>
        </div>
        <div className="item-copy">
          <h3>{item.name}</h3>
          <p>
            {item.brand}
            <span className="divider">|</span>
            {item.model}
          </p>
          <footer>
            <span>
              <Check size={17} />
              {item.nextMaintenance ? (
                `下次维护 ${item.nextMaintenance}`
              ) : item.warrantyDaysLeft !== null && item.warrantyDaysLeft >= 0 ? (
                <>
                  还剩 <b>{item.warrantyDaysLeft}</b> 天保修
                </>
              ) : (
                "已过保 · 继续好好使用"
              )}
            </span>
            <ChevronRight size={16} />
          </footer>
        </div>
      </Link>
    </motion.article>
  );
}
export function EmptyState({
  title = "这里还没有记录",
  description = "添加第一条记录，让物品档案更完整。",
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <Package size={34} />
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
export function LoadingSkeleton() {
  return (
    <div className="skeleton-grid">
      {[1, 2, 3, 4, 5, 6].map((n) => (
        <div className="skeleton" key={n} />
      ))}
    </div>
  );
}
export function Drawer({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const nodes = Array.from(
          document.querySelectorAll<HTMLElement>(
            ".drawer button,.drawer input,.drawer select,.drawer a[href],.drawer textarea",
          ),
        ).filter((el) => !el.hasAttribute("disabled"));
        if (!nodes.length) return;
        const first = nodes[0],
          last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", handler);
    document.querySelector<HTMLElement>(".drawer button")?.focus();
    return () => {
      window.removeEventListener("keydown", handler);
      document.body.style.overflow = original;
      previous?.focus();
    };
  }, [onClose]);
  return (
    <AnimatePresence>
      <motion.div
        className="overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <motion.aside
          className="drawer"
          role="dialog"
          aria-modal="true"
          aria-label={title}
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ duration: 0.25, ease: "easeOut" }}
        >
          <header>
            <h2>{title}</h2>
            <button className="icon-button" aria-label="关闭" onClick={onClose}>
              <X />
            </button>
          </header>
          {children}
        </motion.aside>
      </motion.div>
    </AnimatePresence>
  );
}
export function ConfirmDialog({
  title,
  description,
  onConfirm,
  onClose,
}: {
  title: string;
  description: string;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <Drawer title={title} onClose={onClose}>
      <p>{description}</p>
      <button className="button primary" onClick={onConfirm}>
        确认
      </button>
    </Drawer>
  );
}
export function Toast({ message }: { message: string }) {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          role="status"
          className="toast"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
        >
          <Check size={18} />
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
export function ChartCard({
  title,
  children,
  note,
}: {
  title: string;
  children: ReactNode;
  note?: string;
}) {
  return (
    <section className="panel chart-card">
      <header>
        <h3>{title}</h3>
        {note && <small>{note}</small>}
      </header>
      {children}
    </section>
  );
}
export function LifecycleTimeline({ events, status }: { events: Event[]; status: string }) {
  const nodes = [
    ["purchase", "购买"],
    ["return", "退换"],
    ["use", "使用"],
    ["maintenance", "维护"],
    ["warranty", "保修"],
    ["repair", "维修"],
    ["retired", "淘汰"],
  ];
  return (
    <section className="panel lifecycle">
      <header>
        <h3>生命周期</h3>
        <span>记录物品从拥有到陪伴的全过程</span>
      </header>
      <div className="lifecycle-line">
        {nodes.map(([type, label]) => {
          const matching = events
            .filter((e) => e.type === type)
            .sort((a, b) => b.date.localeCompare(a.date));
          const event = matching[0];
          return (
            <div
              className={`life-node ${event ? "occurred" : ""} ${(status === "维修中" ? type === "repair" : type === "use") ? "current" : ""}`}
              key={type}
            >
              <span>{event ? <Check size={18} /> : <Package size={17} />}</span>
              <b>{label}</b>
              <small>
                {event
                  ? `${event.date}${matching.length > 1 ? ` · ${matching.length}次` : ""}`
                  : "暂无事件"}
              </small>
            </div>
          );
        })}
      </div>
    </section>
  );
}
export function GoLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link className="go-link" to={to}>
      {children}
      <ArrowRight size={17} />
    </Link>
  );
}
