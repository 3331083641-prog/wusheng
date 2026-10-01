import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Box, Grid2X2, List, Plus, ShieldCheck, Wrench } from "lucide-react";
import { EmptyState, ItemCard, PageHeader, StatCard } from "../components/ui";
import { useStore } from "../store";
export default function Items() {
  const data = useStore((s) => s.data)!;
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [category, setCategory] = useState(params.get("category") || "全部");
  const [list, setList] = useState(false);
  const [sort, setSort] = useState("new");
  const [state, setState] = useState("全部");
  let items = data.items.filter(
    (i) =>
      (category === "全部" || i.category === category) &&
      (state === "全部" ||
        (state === "保修中"
          ? i.warrantyDaysLeft !== null && i.warrantyDaysLeft >= 0
          : state === "待维护"
            ? i.nextMaintenance && i.nextMaintenance <= data.today
            : true)),
  );
  items = [...items].sort((a, b) =>
    sort === "name"
      ? a.name.localeCompare(b.name, "zh-CN")
      : sort === "price"
        ? b.purchasePrice - a.purchasePrice
        : b.createdAt.localeCompare(a.createdAt),
  );
  return (
    <main className="page">
      <PageHeader
        title="我的物品"
        description="记录家中的每一件物品，掌握它们的状态，让生活更有秩序。"
        action={
          <Link className="button primary" to="/items/new">
            <Plus size={18} />
            添加物品
          </Link>
        }
      />
      <div className="stats-grid four">
        <StatCard label="全部物品" value={data.stats.itemCount} onClick={() => setState("全部")} />
        <StatCard
          label="保修中"
          value={data.stats.warrantyCount}
          icon={ShieldCheck}
          onClick={() => setState("保修中")}
        />
        <StatCard
          label="待维护"
          value={data.stats.maintenanceDue}
          icon={Wrench}
          tone="orange"
          onClick={() => setState("待维护")}
        />
        <StatCard
          label="耗材补给"
          value={data.stats.consumableLow}
          icon={Box}
          tone="purple"
          onClick={() => {
            navigate("/consumables");
          }}
        />
      </div>
      <div className="toolbar">
        <div className="filter-tabs">
          {["全部", "家电", "数码", "家居", "耗材", "其他"].map((c) => (
            <button
              key={c}
              className={category === c ? "active" : ""}
              onClick={() => setCategory(c)}
            >
              {category === c && (
                <motion.span className="tab-highlight" layoutId="category-highlight" />
              )}
              <span>{c}</span>
            </button>
          ))}
        </div>
        <div className="view-tools">
          <button
            aria-label="网格视图"
            className={`icon-button ${!list ? "selected" : ""}`}
            onClick={() => setList(false)}
          >
            <Grid2X2 size={19} />
          </button>
          <button
            aria-label="列表视图"
            className={`icon-button ${list ? "selected" : ""}`}
            onClick={() => setList(true)}
          >
            <List size={19} />
          </button>
          <select aria-label="排序" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="new">最新添加</option>
            <option value="name">按名称</option>
            <option value="price">按价格</option>
          </select>
        </div>
      </div>
      {state !== "全部" && (
        <button className="filter-clear" onClick={() => setState("全部")}>
          当前筛选：{state} · 清除
        </button>
      )}
      <motion.div layout className={`items-grid ${list ? "list-view" : ""}`}>
        <AnimatePresence>
          {items.map((item) => (
            <ItemCard key={item.id} item={item} list={list} />
          ))}
        </AnimatePresence>
      </motion.div>
      {!items.length && (
        <EmptyState title="没有符合条件的物品" description="试试其他分类，或记录一件新物品。" />
      )}
      <p className="data-footnote">
        共 {items.length} 件 · {data.items.filter((i) => i.isDemo).length} 件合成 Demo 档案 ·
        所有统计共用本地数据库
      </p>
    </main>
  );
}
