import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams, useNavigate, useSearchParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  Download,
  Edit,
  FileText,
  Plus,
  QrCode,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import { MaintenanceTools } from "../components/RecordTools";
import EvidenceCenter from "../components/EvidenceCenter";
import ShareQR from "../components/ShareQR";
import { api, json } from "../api";
import { useStore } from "../store";
import {
  Drawer,
  EmptyState,
  LifecycleTimeline,
  LoadingSkeleton,
  StatusBadge,
} from "../components/ui";
import DocumentCard from "../components/DocumentCard";
import RecognitionPanel, { type ItemForm } from "../components/RecognitionPanel";
import type { Detail } from "../types";
import ProductImage from "../components/ProductImage";
import ConsumableImage from "../components/ConsumableImage";
import { resolveProductAsset } from "../assets/itemAssets";
export default function ItemDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("基本信息");
  const [image, setImage] = useState("");
  const [drawer, setDrawer] = useState("");
  const [form, setForm] = useState<ItemForm>({});
  const [includeManuals, setIncludeManuals] = useState(false);
  const [busy, setBusy] = useState(false);
  const pdfInput = useRef<HTMLInputElement>(null);
  const { refresh, notify } = useStore();
  const load = useCallback(async () => {
    try {
      const d = await api<Detail>(`/items/${id}`);
      setDetail(d);
      setImage(
        resolveProductAsset(
          d.item,
          d.images.find((i) => i.type === "product")?.filePath || d.item.coverImage,
        ).src,
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (detail && params.get("open") === "qr") {
      setDrawer("一物一码");
      const next = new URLSearchParams(params);
      next.delete("open");
      setParams(next, { replace: true });
    }
  }, [detail, params, setParams]);
  useEffect(() => {
    if (!detail?.documents.some((d) => d.textStatus === "ocr_processing")) return;
    const timer = setInterval(() => void load(), 2000);
    return () => clearInterval(timer);
  }, [detail, load]);
  const close = useCallback(() => setDrawer(""), []);
  const act = async (fn: () => Promise<unknown>, message: string) => {
    setBusy(true);
    setError("");
    try {
      await fn();
      await Promise.all([load(), refresh()]);
      notify(message);
      setDrawer("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  if (error && !detail)
    return (
      <main className="page">
        <EmptyState title={error} action={<Link to="/items">返回我的物品</Link>} />
      </main>
    );
  if (!detail)
    return (
      <main className="page">
        <LoadingSkeleton />
      </main>
    );
  const { item } = detail;
  const exportRawData = () => {
    const blob = new Blob([JSON.stringify(detail, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `物生-${item.name}.json`;
    a.click();
    URL.revokeObjectURL(url);
    notify("档案已导出为 JSON，附件仍保存在本机");
  };
  const exportArchive = async () => {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/items/${id}/export/pdf`);
      if (!response.ok) {
        const message = await response.json().catch(() => ({ detail: "档案 PDF 导出失败" }));
        throw new Error(typeof message.detail === "string" ? message.detail : "档案 PDF 导出失败");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      try {
        const a = document.createElement("a");
        a.href = url;
        a.download = `物生-${item.name}-物品档案.pdf`;
        a.click();
      } finally { URL.revokeObjectURL(url); }
      notify("物品档案 PDF 已导出");
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  };
  const openEdit = () => {
    setForm({
      ...Object.fromEntries(
        [
          "name",
          "brand",
          "model",
          "category",
          "purchasePrice",
          "purchaseDate",
          "purchaseChannel",
          "warrantyMonths",
          "returnWindowDays",
          "serialNumber",
          "description",
          "location",
        ].map((k) => [k, String(item[k as keyof typeof item] ?? "")]),
      ),
      status: ["淘汰", "转卖", "回收"].includes(item.status) ? item.status : "正常使用",
    });
    setDrawer("编辑信息");
  };
  const upload = async (file: File) => {
    if (busy) return;
    if (!file.name.toLowerCase().endsWith(".pdf") || file.type !== "application/pdf") {
      setError("请上传 .pdf 格式的 PDF 文件");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("PDF 不超过 50MB");
      return;
    }
    const body = new FormData();
    body.append("file", file);
    await act(
      () => api(`/items/${id}/documents/manual`, { method: "POST", body }),
      "说明书已保存在本机",
    );
  };
  return (
    <main className="page detail-page">
      <div className="breadcrumbs">
        <Link to="/items">我的物品</Link>
        <span>›</span>物品详情
        {item.isDemo && <span className="demo-label">合成 Demo</span>}
      </div>
      {error && !drawer && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <div className="detail-hero">
        <div className="gallery">
          <div className="thumbnails">
            {[item.coverImage, ...detail.images.map((i) => i.filePath)]
              .map((src) => resolveProductAsset(item, src).src)
              .filter((v, i, a) => v && a.indexOf(v) === i)
              .map((src) => (
                <button
                  key={src}
                  onClick={() => setImage(src)}
                  className={src === image ? "active" : ""}
                >
                  <ProductImage item={item} src={src} alt="切换物品图片" />
                </button>
              ))}
          </div>
          <div className="main-image">
            <AnimatePresence mode="wait">
              <motion.div
                key={image}
                className="main-image-crossfade"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18 }}
              >
                <ProductImage item={item} src={image} fit="contain" priority />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
        <section className="detail-info">
          <div className="detail-title">
            <h1>{item.name}</h1>
            <StatusBadge>{item.status}</StatusBadge>
          </div>
          <p>{item.description || "每一段陪伴，都值得被记住。"}</p>
          <dl className="detail-facts">
            {[
              ["品牌", item.brand],
              ["购买价格", `¥ ${item.purchasePrice.toLocaleString()}`],
              ["型号", item.model],
              ["保修截止", item.warrantyEndDate || "未记录"],
              ["购买日期", item.purchaseDate],
              [
                "剩余保修",
                item.warrantyDaysLeft === null
                  ? "未记录"
                  : item.warrantyDaysLeft >= 0
                    ? `${item.warrantyDaysLeft} 天`
                    : "已过保",
              ],
              ["购买渠道", item.purchaseChannel || "未记录"],
              ["序列号", item.serialNumber || "未记录"],
            ].map(([key, val]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{val}</dd>
              </div>
            ))}
          </dl>
        </section>
        <aside className="detail-actions panel">
          <button className="button primary" onClick={openEdit}>
            <Edit size={18} />
            编辑信息
          </button>
          <button className="button secondary" onClick={() => setDrawer("一物一码")}>
            <QrCode size={18} />
            生成二维码
          </button>
          <button className="button secondary" disabled={busy} onClick={() => void exportArchive()}>
            <Download size={18} />
            导出档案
          </button>
          <button className="button secondary" onClick={exportRawData}>
            导出原始数据 JSON
          </button>
          <a
            className="button secondary"
            href={`/api/items/${id}/evidence-pack?includeManuals=${includeManuals}`}
            download
          >
            售后证据包
          </a>
          <label>
            <input
              type="checkbox"
              checked={includeManuals}
              onChange={(e) => setIncludeManuals(e.target.checked)}
            />{" "}
            包含说明书
          </label>
          <small>
            记录在本机
            <br />
            始终由你掌握
          </small>
        </aside>
      </div>
      <LifecycleTimeline events={detail.events} status={item.status} />
      <section className="panel detail-tabs">
        <div className="text-tabs">
          {["基本信息", "凭证资料", "说明书", "维护记录", "维修记录", "耗材", "AI 建议"].map(
            (t) => (
              <button className={tab === t ? "active" : ""} key={t} onClick={() => setTab(t)}>
                {t}
              </button>
            ),
          )}
        </div>
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="tab-body"
          >
            {tab === "基本信息" && (
              <div className="detail-summary-grid">
                <section className="care-summary green">
                  <Wrench />
                  <h3>维护建议</h3>
                  <p>{detail.suggestions[0]}</p>
                  <button onClick={() => setTab("维护记录")}>查看维护记录 →</button>
                </section>
                <section className="care-summary orange">
                  <ShieldCheck />
                  <h3>保修提醒</h3>
                  <p>
                    {item.warrantyDaysLeft !== null && item.warrantyDaysLeft >= 0
                      ? `仍在保修期内，还有 ${item.warrantyDaysLeft} 天。请保留购买凭证。`
                      : "当前已过保或未记录保修期限。"}
                  </p>
                  <Link to="/reminders">查看提醒 →</Link>
                </section>
                <section className="care-summary blue">
                  <FileText />
                  <h3>产品说明书</h3>
                  <p>{detail.documents.length} 份本地资料。支持 PDF 存档和文本引用。</p>
                  <button onClick={() => setTab("说明书")}>查看说明书 →</button>
                </section>
                <section className="care-summary purple">
                  <Sparkles />
                  <h3>物品专属建议</h3>
                  <p>结合当前档案、维护与维修历史，有依据地回答。</p>
                  <Link to={`/assistant?item=${id}`}>询问助手 →</Link>
                </section>
              </div>
            )}
            {tab === "凭证资料" && (
              <EvidenceCenter
                itemId={id!}
                images={detail.images}
                reload={async () => {
                  await Promise.all([load(), refresh()]);
                }}
              />
            )}
            {tab === "说明书" && (
              <>
                <div className="section-toolbar">
                  <p>本地 PDF 资料；扫描件若无文本层会明确提示。</p>
                  <button
                    type="button"
                    className="button primary"
                    disabled={busy}
                    onClick={() => pdfInput.current?.click()}
                  >
                    <Plus size={18} />
                    {busy ? "上传中…" : detail.documents.length ? "继续上传 PDF" : "上传 PDF"}
                  </button>
                  <input
                    ref={pdfInput}
                    className="visually-hidden"
                    type="file"
                    accept=".pdf,application/pdf"
                    disabled={busy}
                    aria-label="上传说明书 PDF"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void upload(f);
                      e.target.value = "";
                    }}
                  />
                </div>
                {detail.documents.map((d) => (
                  <DocumentCard
                    key={d.id}
                    document={d}
                    onUpdate={load}
                    onDelete={() =>
                      act(
                        () => api(`/documents/${d.id}`, { method: "DELETE" }),
                        "说明书及本地文件已删除",
                      )
                    }
                  />
                ))}
                {!detail.documents.length && (
                  <EmptyState
                    title="本地 PDF 资料尚未添加"
                    description="上传 PDF 后，可直接查看并在 AI 助手中引用。"
                  />
                )}
              </>
            )}
            {tab === "维护记录" && (
              <>
                <div className="section-toolbar">
                  <p>周期由你确认，按日历日期计算。</p>
                  <button className="button primary" onClick={() => setDrawer("记录维护")}>
                    <Plus size={18} />
                    记录维护
                  </button>
                </div>
                {detail.maintenance.map((m) => (
                  <article className="record-row" key={m.id}>
                    <span className="icon-well green">
                      <Wrench />
                    </span>
                    <div>
                      <h3>{m.type}</h3>
                      <p>{m.description}</p>
                    </div>
                    <span>
                      {m.date}
                      <small>下次 {m.nextDueDate}</small>
                    </span>
                    <b>¥ {m.cost}</b>
                    <MaintenanceTools
                      record={m}
                      reload={async () => {
                        await load();
                        await refresh();
                      }}
                    />
                  </article>
                ))}
                {!detail.maintenance.length && <EmptyState />}
              </>
            )}
            {tab === "维修记录" && (
              <>
                <div className="section-toolbar">
                  <p>所有维修同步生命周期事件与年度支出。</p>
                  <Link className="button primary" to={`/repairs?item=${id}`}>
                    新增维修记录
                  </Link>
                </div>
                {detail.repairs.map((r) => (
                  <article className="record-row" key={r.id}>
                    <Wrench />
                    <div>
                      <h3>{r.issue}</h3>
                      <p>
                        {r.reportDate} · {r.serviceType}
                      </p>
                    </div>
                    <StatusBadge>{r.status}</StatusBadge>
                    <b>¥ {r.cost}</b>
                  </article>
                ))}
                {!detail.repairs.length && (
                  <EmptyState
                    title="没有找到维修记录"
                    description="目前没有记录过维修，不代表物品从未维修。"
                  />
                )}
              </>
            )}
            {tab === "耗材" && (
              <>
                {detail.consumables.map((c) => (
                  <article className="record-row" key={c.id}>
                    <ConsumableImage className="record-image" consumable={c} />
                    <div>
                      <h3>{c.name}</h3>
                      <p>
                        库存 {c.currentStock} {c.unit} · 预计 {c.estimatedDaysLeft ?? "未知"} 天
                      </p>
                    </div>
                    <Link className="button secondary" to="/consumables">
                      查看预测
                    </Link>
                  </article>
                ))}
                {!detail.consumables.length && (
                  <EmptyState
                    title="尚未关联耗材"
                    action={<Link to="/consumables">添加设备耗材关联</Link>}
                  />
                )}
              </>
            )}
            {tab === "AI 建议" && (
              <div className="suggestions">
                {detail.suggestions.map((s) => (
                  <p key={s}>
                    <Sparkles size={19} />
                    {s}
                  </p>
                ))}
                <Link className="button primary" to={`/assistant?item=${id}`}>
                  打开物品专属助手
                </Link>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </section>
      {drawer && (
        <Drawer title={drawer} onClose={close}>
          {drawer === "一物一码" && <ShareQR detail={detail} />}
          {drawer === "编辑信息" && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void act(
                  () =>
                    api(
                      `/items/${id}`,
                      json("PUT", {
                        ...form,
                        purchasePrice: Number(form.purchasePrice),
                        warrantyMonths: Number(form.warrantyMonths),
                        returnWindowDays: Number(form.returnWindowDays),
                      }),
                    ),
                  "信息与提醒已同步更新",
                );
              }}
            >
              <RecognitionPanel form={form} setForm={setForm} result={null} busy={busy} manual />
              <button className="button primary" disabled={busy}>
                保存修改
              </button>
              <button
                type="button"
                className="button secondary"
                disabled={busy}
                onClick={() => setDrawer("删除档案")}
              >
                删除档案
              </button>
            </form>
          )}
          {drawer === "删除档案" && (
            <div>
              <p>确认删除「{item.name}」及其关联记录？已上传图片和 PDF 文件也将一并删除。</p>
              <button
                className="button primary"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await api(`/items/${id}`, { method: "DELETE" });
                    await refresh();
                    notify("档案、关联记录和本地附件已删除");
                    navigate("/items");
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                确认删除档案
              </button>
              <button className="button secondary" onClick={openEdit}>
                返回编辑
              </button>
            </div>
          )}
          {drawer === "记录维护" && (
            <form
              className="drawer-form"
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                void act(
                  () =>
                    api(
                      `/items/${id}/maintenance`,
                      json("POST", {
                        type: f.get("type"),
                        date: f.get("date"),
                        intervalDays: Number(f.get("interval")),
                        description: f.get("description"),
                        cost: Number(f.get("cost") || 0),
                      }),
                    ),
                  "维护已记录，下次维护提醒已生成",
                );
              }}
            >
              <label>
                维护内容
                <input name="type" required defaultValue="清洁维护" maxLength={100} />
              </label>
              <label>
                维护日期
                <input
                  name="date"
                  type="date"
                  required
                  defaultValue={useStore.getState().data?.today}
                />
              </label>
              <label>
                下次周期（天）
                <input
                  name="interval"
                  type="number"
                  min="1"
                  max="3650"
                  defaultValue="90"
                  required
                />
              </label>
              <label>
                费用（元）
                <input name="cost" type="number" min="0" step="0.01" defaultValue="0" />
              </label>
              <label>
                说明
                <textarea name="description" maxLength={1000} />
              </label>
              <button className="button primary" disabled={busy}>
                保存维护记录
              </button>
            </form>
          )}
          {error && (
            <p role="alert" className="form-error">
              {error}
            </p>
          )}
        </Drawer>
      )}
    </main>
  );
}
