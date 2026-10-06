import { useEffect, useState, type ReactNode } from "react";
import {
  Bell,
  Box,
  ChartNoAxesCombined,
  Home,
  Leaf,
  Package,
  PlusSquare,
  Search,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import { NavLink, Link, useLocation } from "react-router-dom";
import { Logo } from "./ui";
import ProductImage from "./ProductImage";
import { useStore } from "../store";
const navigation = [
  ["/", "首页", Home],
  ["/items", "我的物品", Package],
  ["/items/new", "添加物品", PlusSquare],
  ["/reminders", "提醒中心", Bell],
  ["/consumables", "耗材管理", Box],
  ["/repairs", "维修记录", Wrench],
  ["/assistant", "AI 助手", Sparkles],
  ["/statistics", "数据统计", ChartNoAxesCombined],
] as const;
export function Sidebar() {
  const location = useLocation();
  return (
    <aside className="sidebar">
      <Logo />
      <nav aria-label="主导航">
        {navigation.map(([to, label, Icon]) => (
          <NavLink
            key={to}
            to={to}
            aria-label={label}
            title={label}
            end={to === "/" || to === "/items"}
            className={({ isActive }) =>
              `nav-item ${(isActive && !(to === "/items" && location.pathname === "/items/new")) || (to === "/items" && location.pathname.startsWith("/items/") && location.pathname !== "/items/new") ? "active" : ""}`
            }
          >
            <Icon size={21} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-note">
        <p>
          让每一件物品
          <br />
          都被好好对待
        </p>
        <span>陪伴，比拥有更长久。</span>
        <Link to="/items" aria-label="查看我的物品">
          <Chevron />
        </Link>
      </div>
      <div className="local-note">
        <span /> 本地优先 · 免费开放
      </div>
    </aside>
  );
}
function Chevron() {
  return <span className="chevron-text">→</span>;
}
export function UtilityBar() {
  const data = useStore((s) => s.data);
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const location = useLocation();
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(query.trim()), 300);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    setQuery("");
    setDebounced("");
  }, [location.pathname]);
  const results =
    data?.items
      .filter((i) =>
        [i.name, i.brand, i.model, i.serialNumber]
          .join(" ")
          .toLowerCase()
          .includes(debounced.toLowerCase()),
      )
      .slice(0, 6) || [];
  return (
    <div className="utility-bar">
      <span className="utility-caption">
        <Leaf size={15} /> 照顾物品，也照顾生活
      </span>
      <div className="global-search">
        <Search size={18} />
        <input
          aria-label="全局搜索"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索物品名称、品牌、型号或序列号…"
        />
        {debounced && (
          <div className="search-results">
            {results.length ? (
              results.map((i) => (
                <Link key={i.id} to={`/items/${i.id}`}>
                  <ProductImage item={i} alt="" priority />
                  <div>
                    <b>{i.name}</b>
                    <small>
                      {i.brand} · {i.model}
                    </small>
                  </div>
                </Link>
              ))
            ) : (
              <p>没有找到相关物品</p>
            )}
          </div>
        )}
      </div>
      <Link className="notification" to="/reminders" aria-label="查看通知">
        <Bell size={22} />
        {!!data?.reminders.filter((r) => r.status === "pending" && r.daysLeft <= 7).length && (
          <span />
        )}
      </Link>
      <span className="local-status">
        <ShieldCheck size={15} /> 数据保存在本地
      </span>
    </div>
  );
}
export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="workspace">
        <UtilityBar />
        {children}
      </div>
    </div>
  );
}
