import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Check, ChevronLeft, ChevronRight, FileText, Package, QrCode, ShieldCheck, Wrench } from "lucide-react";
import { api } from "../api";
import { resolveProductAsset } from "../assets/itemAssets";
import type { Item } from "../types";
import ProductImage from "./ProductImage";
import "./home-showcase.css";

export const AUTO_INTERVAL = 6000;
const INTERACTION_PAUSE = 10000;
interface ShowcaseItem {
  item: Pick<Item, "id" | "name" | "brand" | "model" | "status" | "isDemo" | "coverImage" | "warrantyEndDate" | "warrantyDaysLeft" | "nextMaintenance">;
  chip: { label: string; tone: string };
  maintenanceType: string | null;
  consumable: { title: string; subtitle: string; tone: string };
  lifecycle: { type: string; label: string; date: string | null; state: string }[];
}
export default function HomeItemShowcase() {
  const [items, setItems] = useState<ShowcaseItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [visible, setVisible] = useState(document.visibilityState !== "hidden");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const reduce = useReducedMotion();
  const activeId = useRef("");
  const pending = useRef(false);
  const queuedRefresh = useRef(false);
  const pauseTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const load = useCallback(async () => {
    if (pending.current) { queuedRefresh.current = true; return; }
    pending.current = true;
    try {
      do {
        queuedRefresh.current = false;
        const result = await api<{ items: ShowcaseItem[] }>("/home/showcase");
        setItems(result.items);
        setCurrentIndex((index) => {
          const retained = result.items.findIndex((entry) => entry.item.id === activeId.current);
          return retained >= 0 ? retained : Math.min(index, Math.max(0, result.items.length - 1));
        });
      } while (queuedRefresh.current);
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      pending.current = false;
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
    const refresh = () => void load();
    const visibility = () => {
      const shown = document.visibilityState !== "hidden";
      setVisible(shown);
      if (shown) void load();
    };
    window.addEventListener("focus", refresh);
    window.addEventListener("wusheng:items-changed", refresh);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      window.removeEventListener("focus", refresh);
      window.removeEventListener("wusheng:items-changed", refresh);
      document.removeEventListener("visibilitychange", visibility);
      clearTimeout(pauseTimer.current);
    };
  }, [load]);
  useEffect(() => {
    if (items.length < 2 || isPaused || hovered || !visible || error) return;
    const timer = setInterval(() => setCurrentIndex((index) => (index + 1) % items.length), AUTO_INTERVAL);
    return () => clearInterval(timer);
  }, [items.length, isPaused, hovered, visible, error]);
  const currentItem = items[currentIndex];
  useEffect(() => { activeId.current = currentItem?.item.id || ""; }, [currentItem?.item.id]);
  useEffect(() => {
    if (items.length < 2) return;
    const next = items[(currentIndex + 1) % items.length];
    const preload = new window.Image();
    preload.src = resolveProductAsset(next.item).src;
  }, [items, currentIndex]);
  const pause = () => {
    setIsPaused(true);
    clearTimeout(pauseTimer.current);
    pauseTimer.current = setTimeout(() => setIsPaused(false), INTERACTION_PAUSE);
  };
  const select = (index: number) => { pause(); setCurrentIndex(index); };
  const thumbnailItems = items.length ? Array.from({ length: Math.min(3, items.length) }, (_, offset) => ({ entry: items[(currentIndex + offset) % items.length], index: (currentIndex + offset) % items.length })) : [];
  // A bounded dot window remains useful when a household has hundreds of items.
  const dotIndices = items.length ? Array.from({ length: Math.min(5, items.length) }, (_, offset) => (currentIndex + offset) % items.length) : [];
  if (loading) return <div className="home-showcase showcase-skeleton" aria-label="加载物品档案"><div /><div /><div /></div>;
  if (error) return <div className="home-showcase showcase-empty" role="alert"><Package size={32} /><h3>暂时无法加载物品档案</h3><p>{error}</p><button className="button secondary" onClick={() => void load()}>重新加载</button></div>;
  if (!currentItem) return <div className="home-showcase showcase-empty"><Package size={32} /><h3>还没有物品档案</h3><p>添加第一件物品，开始记录它的生命周期。</p><Link className="button primary" to="/items/new">添加物品</Link></div>;
  const { item, chip, lifecycle, consumable } = currentItem;
  const days = item.warrantyDaysLeft;
  const warranty = days === null ? "未记录" : days < 0 ? "已过保" : `${days} 天`;
  const warrantyNote = item.warrantyEndDate ? (days !== null && days < 0 ? `${item.warrantyEndDate} 到期` : `至 ${item.warrantyEndDate}`) : "暂无保修记录";
  return (
    <section className={`home-showcase${reduce ? " reduced" : ""}`} aria-label="物品档案轮播" aria-roledescription="carousel" data-paused={isPaused || hovered || !visible}
      onMouseEnter={() => { setHovered(true); pause(); }} onMouseLeave={() => { setHovered(false); pause(); }} onFocusCapture={pause}>
      <div className="showcase-layout">
        <div className="showcase-float">
          <article className="showcase-main">
            <header className="showcase-toolbar"><span><i className="live-dot" />物品档案展示 <small className="showcase-count">{currentIndex + 1} / {items.length}</small></span><div>
              <button aria-label="上一件物品" disabled={items.length < 2} onClick={() => select((currentIndex - 1 + items.length) % items.length)}><ChevronLeft size={17} /></button>
              <button aria-label="下一件物品" disabled={items.length < 2} onClick={() => select((currentIndex + 1) % items.length)}><ChevronRight size={17} /></button>
            </div></header>
            <AnimatePresence mode="wait" initial={false}>
              <motion.div className="showcase-content" key={item.id} initial={reduce ? false : { opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }} transition={{ duration: reduce ? 0 : 0.38 }}>
                <motion.div className="showcase-product" initial={reduce ? false : { opacity: 0, scale: 0.985 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: reduce ? 0 : 0.5 }}><ProductImage item={item} priority fit="contain" /></motion.div>
                <div className="showcase-identity"><h2>{item.name}</h2><span className={`showcase-chip tone-${chip.tone}`}>{chip.label}</span><p>{[item.brand, item.model].filter(Boolean).join(" · ") || "品牌 / 型号未记录"}</p>{item.isDemo && <small>合成 Demo 档案</small>}</div>
                <div className="showcase-metrics">
                  {[[ShieldCheck, "剩余保修", warranty, warrantyNote], [Wrench, "下次维护", item.nextMaintenance || "未记录", currentItem.maintenanceType || "暂无维护计划"], [Package, "耗材状态", consumable.title, consumable.subtitle]].map(([Icon, label, value, note], index) => {
                    const I = Icon as typeof ShieldCheck;
                    return <motion.div key={String(label)} initial={reduce ? false : { opacity: 0, y: 3 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: reduce ? 0 : index * 0.045 }}><I size={18} /><div><small>{String(label)}</small><strong>{String(value)}</strong><span>{String(note)}</span></div></motion.div>;
                  })}
                </div>
                <div className="showcase-lifecycle"><h3>生命周期</h3><ol>{lifecycle.map((node, index) => <motion.li className={node.state} key={node.type} initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: reduce ? 0 : index * 0.035 }}>
                  <span className="lifecycle-mark">{node.state === "completed" || node.state === "current" ? <Check size={13} /> : <span />}</span><b>{node.label}</b><small>{node.state === "current" ? "进行中" : node.date || "未发生"}</small>
                </motion.li>)}</ol></div>
                <div className="showcase-actions"><Link className="button primary" to={`/items/${item.id}`}><FileText size={16} />查看完整档案</Link><Link className="button secondary" to={`/items/${item.id}?open=qr`}><QrCode size={16} />一物一码</Link></div>
              </motion.div>
            </AnimatePresence>
          </article>
        </div>
        <div className="showcase-thumbnails">{thumbnailItems.map(({ entry, index }) => <button key={entry.item.id} aria-label={`展示物品：${entry.item.name}`} aria-pressed={index === currentIndex} title={entry.item.name} onClick={() => select(index)}><ProductImage item={entry.item} alt={entry.item.name} fit="contain" /></button>)}</div>
      </div>
      <div className="showcase-dots">{dotIndices.map((index) => <button key={items[index].item.id} aria-label={`切换至第 ${index + 1} 件物品`} aria-pressed={index === currentIndex} onClick={() => select(index)} />)}</div>
    </section>
  );
}
