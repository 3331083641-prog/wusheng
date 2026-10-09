import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, FileText, Package, ShieldCheck, Wrench } from "lucide-react";
import { api } from "../api";
import "./share-item.css";

export type Shared = {
  item: { name: string; brand: string; model: string; category: string; status: string; coverImage: string; nextMaintenance?: string | null;
    purchaseDate?: string; purchasePrice?: number; purchaseChannel?: string; location?: string;
    warrantyEndDate?: string | null; warrantyDaysLeft?: number | null; warrantyMonths?: number };
  images: { src: string }[];
  lifecycle: { type: string; label: string; date: string | null; state: string; events: { title: string; date: string }[] }[];
  maintenance: { date: string; type: string; nextDueDate: string; needsMaintenance: boolean; cost?: number; description?: string }[];
  repairs: { reportDate: string; status: string; completionDate: string | null; cost?: number; issue?: string; description?: string }[];
  reminders: { type: string; dueDate: string }[];
  consumables: { name: string; relatedItemName: string; status: string; currentStock?: number; unit?: string;
    estimatedDaysLeft: number | null; suggestedPurchaseDate: string | null; dataQuality: string; qualityExplanation: string }[];
  manuals: { name: string; readable: boolean; pageCount?: number | null; fileSize?: number; uploadedAt?: string; viewUrl?: string; downloadUrl?: string | null }[];
  options: { showWarranty: boolean; showLifecycle: boolean; showConsumables: boolean; showMaintenance: boolean; showRepairs: boolean;
    showManualNames: boolean; showManualFiles: boolean };
};
const value = (v: unknown) => v === null || v === undefined || v === "" ? "未记录" : String(v);
const size = (bytes = 0) => bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
const money = (amount: number) => `¥${amount.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
function Facts({ fields }: { fields: [string, unknown][] }) {
  return <dl className="share-facts">{fields.map(([label, content]) => <div key={label}><dt>{label}</dt><dd>{value(content)}</dd></div>)}</dl>;
}
function Photo({ src, name }: { src: string; name: string }) {
  const [state, setState] = useState("loading");
  const [attempt, setAttempt] = useState(0);
  return <div className="share-photo" data-image-state={state}>
    {state !== "error" && <img key={attempt} src={src} alt={name} onLoad={() => setState("loaded")} onError={() => setState("error")} />}
    {state === "loading" && <span className="share-image-skeleton" aria-label="正在加载物品照片" />}
    {state === "error" && <div className="share-image-error" role="alert"><Package size={28} aria-hidden="true" /><p>照片暂时无法读取</p><small>请确认电脑保持运行，或刷新档案。</small><button onClick={() => { setState("loading"); setAttempt(a => a + 1); }}>重新加载照片</button></div>}
  </div>;
}
function Cover({ data }: { data: Shared }) {
  const [index, setIndex] = useState(0);
  const touchStart = useRef<number | null>(null);
  const images = data.images || (data.item.coverImage !== "/assets/no-photo.svg" ? [{ src: data.item.coverImage }] : []);
  const current = Math.min(index, Math.max(0, images.length - 1));
  const change = (step: number) => setIndex((current + step + images.length) % images.length);
  const days = data.item.warrantyDaysLeft;
  const warranty = !data.item.warrantyEndDate || days === null || days === undefined ? "保修未记录" : days < 0 ? "已过保" : days <= 30 ? "保修即将到期" : "保修中";
  return <section className="share-cover-card" aria-label="物品封面">
    <div className="share-gallery" onTouchStart={e => { touchStart.current = e.touches[0].clientX; }} onTouchEnd={e => {
      if (images.length > 1 && touchStart.current !== null) { const delta = e.changedTouches[0].clientX - touchStart.current; if (Math.abs(delta) > 40) change(delta < 0 ? 1 : -1); }
      touchStart.current = null;
    }}>
      {images.length ? <Photo key={images[current].src} src={images[current].src} name={data.item.name} /> : <div className="share-no-photo"><Package size={32} aria-hidden="true" /><p>尚未添加照片</p></div>}
      {images.length > 1 && <div className="share-gallery-controls"><button aria-label="上一张本体照片" onClick={() => change(-1)}><ChevronLeft size={18} /></button><span aria-live="polite">{current + 1} / {images.length}</span><button aria-label="下一张本体照片" onClick={() => change(1)}><ChevronRight size={18} /></button></div>}
    </div>
    <div className="share-identity"><h1>{data.item.name}</h1><p>{value(data.item.brand)} · {value(data.item.model)}</p><div className="share-chips"><span className="share-chip">{value(data.item.status)}</span>{data.options.showWarranty && <span className={`share-chip ${days !== null && days !== undefined && days < 0 ? "share-chip-warning" : ""}`}>{warranty}</span>}</div></div>
  </section>;
}
export default function ShareItem() {
  const token = location.pathname.split("/").pop();
  const [data, setData] = useState<Shared | null>(null);
  const [error, setError] = useState("");
  const controller = useRef<AbortController | null>(null);
  const load = useCallback(async (reset = true) => {
    controller.current?.abort();
    const request = new AbortController(); controller.current = request;
    if (reset) setData(null); setError("");
    try {
      const result = await api<Shared>(`/share-data/${encodeURIComponent(token || "")}`, { cache: "no-store", signal: request.signal });
      if (!request.signal.aborted) { setData(result); document.title = `物生 · ${result.item.name} · 只读档案`; }
    } catch (e) { if (!request.signal.aborted) { setData(null); setError((e as Error).message); document.title = "物生 · 只读物品档案"; } }
  }, [token]);
  useEffect(() => {
    const previousTitle = document.title; document.title = "物生 · 只读物品档案";
    void load();
    const refresh = () => { if (!document.hidden) void load(); };
    const visibility = () => { if (document.hidden) { controller.current?.abort(); setData(null); } else refresh(); };
    window.addEventListener("focus", refresh); window.addEventListener("pageshow", refresh); document.addEventListener("visibilitychange", visibility);
    const interval = window.setInterval(() => { if (!document.hidden) void load(false); }, 30000);
    return () => { controller.current?.abort(); window.clearInterval(interval); window.removeEventListener("focus", refresh); window.removeEventListener("pageshow", refresh); document.removeEventListener("visibilitychange", visibility); document.title = previousTitle; };
  }, [load]);
  const fields: [string, unknown][] = data ? [["物品名称", data.item.name], ["品牌", data.item.brand], ["型号", data.item.model], ["分类", data.item.category], ["当前状态", data.item.status]] : [];
  if (data) {
    for (const [key, label] of [["purchaseDate", "购买日期"], ["purchaseChannel", "购买渠道"], ["purchasePrice", "购买价格"], ["location", "存放位置"]] as const) {
      if (key in data.item) fields.push([label, key === "purchasePrice" ? money(data.item.purchasePrice!) : data.item[key]]);
    }
    if (data.options.showWarranty) fields.push(["保修期限", data.item.warrantyMonths ? `${data.item.warrantyMonths} 个月` : "未记录"], ["保修截止", data.item.warrantyEndDate]);
  }
  return <main className="share-page">
    <header className="share-brand"><div><img src="/assets/branding/wusheng-eco-ring-logo.png" alt="物生 Logo" width="32" height="32" /><span>物生</span></div><small>只读物品档案</small></header>
    {error ? <section className="share-state" role="alert"><h1>档案暂不可用</h1><p>{error}</p><button onClick={() => void load()}>重新读取档案</button></section> : !data ? <div className="share-loading" role="status" aria-label="正在读取档案"><div /><p>正在读取档案…</p></div> : <>
      <Cover data={data} />
      <section className="share-section"><h2>基本信息</h2><Facts fields={fields} /></section>
      <section className="share-section share-care"><h2><ShieldCheck size={19} aria-hidden="true" />保修与提醒</h2><Facts fields={[
        ...(data.options.showWarranty ? [["保修状态", !data.item.warrantyEndDate ? "未记录" : (data.item.warrantyDaysLeft ?? 0) < 0 ? "已过保" : "保修中"], ["截止日期", data.item.warrantyEndDate], ["剩余保修", data.item.warrantyDaysLeft === null || data.item.warrantyDaysLeft === undefined ? "未记录" : data.item.warrantyDaysLeft < 0 ? "已过保" : `${data.item.warrantyDaysLeft} 天`]] as [string, unknown][] : []), ["下次维护", data.item.nextMaintenance]]} />
        {data.reminders.map((r, i) => <p className="share-reminder" key={i}>{r.type} · {r.dueDate}</p>)}
      </section>
      {data.options.showLifecycle && <section className="share-section"><h2>生命周期</h2><ol className="share-timeline">{data.lifecycle.map(stage => <li className={`share-stage-${stage.state}`} key={stage.type}><span className="share-stage-dot" aria-hidden="true" /><div><strong>{stage.label}</strong>{stage.state === "current" && <span className="share-current">进行中</span>}{stage.events.length ? stage.events.map((e, i) => <p key={i}><time>{e.date}</time> · {e.title}</p>) : <p>{stage.state === "current" ? "当前阶段 · 未公开事件日期" : "暂无记录"}</p>}</div></li>)}</ol></section>}
      {(data.options.showMaintenance || data.options.showRepairs) && <section className="share-section"><h2><Wrench size={19} aria-hidden="true" />维护与维修</h2>
        {data.options.showMaintenance && <><h3>维护记录</h3>{!data.maintenance.length && <p className="share-empty">暂无维护记录</p>}{data.maintenance.map((r, i) => <article className="share-record" key={i}><div><strong>{r.type}</strong><span className={`share-chip ${r.needsMaintenance ? "share-chip-warning" : ""}`}>{r.needsMaintenance ? "需要维护" : "维护已记录"}</span></div><p>维护日期 {r.date}</p><p>下次维护 {r.nextDueDate}</p>{r.cost !== undefined && <p>费用 {money(r.cost)}</p>}{r.description && <p>{r.description}</p>}</article>)}</>}
        {data.options.showRepairs && <><h3>维修记录</h3>{!data.repairs.length && <p className="share-empty">暂无维修记录</p>}{data.repairs.map((r, i) => <article className="share-record" key={i}><div><strong>{r.status}</strong><span>报修 {r.reportDate}</span></div>{r.completionDate && <p>完成日期 {r.completionDate}</p>}{r.issue && <p>{r.issue}</p>}{r.cost !== undefined && <p>费用 {money(r.cost)}</p>}{r.description && <p>{r.description}</p>}</article>)}</>}
      </section>}
      {data.options.showConsumables && <section className="share-section"><h2>耗材状态</h2>{!data.consumables.length && <p className="share-empty">暂无关联耗材</p>}{data.consumables.map((c, i) => <article className="share-consumable" key={i}><div><strong>{c.name}</strong><span className={`share-chip ${["建议补货", "即将耗尽"].includes(c.status) ? "share-chip-warning" : ""}`}>{c.status}</span></div><small>关联物品：{c.relatedItemName}</small><Facts fields={[
        ...(c.currentStock !== undefined ? [["当前库存", `${c.currentStock} ${c.unit}`]] as [string, unknown][] : []), ["预计可用", c.estimatedDaysLeft === null ? "数据不足" : `${c.estimatedDaysLeft} 天`], ["建议补货", c.suggestedPurchaseDate]]} /><p className="share-prediction">{({ high: "较充分", medium: "一般", low: "有限" } as Record<string, string>)[c.dataQuality] || "未记录"}数据 · {c.qualityExplanation}</p></article>)}</section>}
      {(data.options.showManualNames || data.options.showManualFiles) && <section className="share-section"><h2>产品说明书</h2>{!data.manuals.length && <p className="share-empty">暂无已共享说明书</p>}{data.manuals.map((m, i) => <article className="share-manual" key={m.viewUrl || i}><div className="share-manual-name"><FileText size={22} aria-hidden="true" /><strong>{m.name}</strong></div>{m.readable ? <><p>PDF{m.pageCount ? ` · ${m.pageCount} 页` : ""} · {size(m.fileSize)}</p><small>{m.uploadedAt?.slice(0, 10)} 上传</small><div className="share-manual-actions"><a href={m.viewUrl} target="_blank" rel="noreferrer">在线查看</a>{m.downloadUrl && <a href={m.downloadUrl} download={m.name}>下载 PDF</a>}</div></> : <p className="share-empty">仅共享文件名，未授权读取文件</p>}</article>)}{data.manuals.some(m => m.readable) && <p className="share-pdf-help">若当前浏览器不支持直接阅读（如部分微信内置浏览器），请使用系统浏览器打开{data.manuals.some(m => m.downloadUrl) ? "或下载 PDF 后用系统阅读器查看" : ""}。</p>}</section>}
    </>}
    <footer className="share-footer"><strong>物生 · 只读档案</strong><p>手机和电脑需处于可互通的同一局域网，电脑保持物生运行。分享过期或撤销后，档案与说明书均不可访问。</p></footer>
  </main>;
}
