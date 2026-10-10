import { useEffect, useRef, useState } from "react";
import { api, json } from "../api";
import type { ItemImage } from "../types";
export const attachmentTypes: Record<string, string> = {
  product: "物品照片",
  receipt: "购买小票",
  invoice: "电子/纸质发票",
  package: "包装盒",
  label: "产品铭牌",
  warranty_card: "保修卡",
  manual_image: "说明书照片",
  other: "其他资料",
};
type Evidence = {
  field: string;
  recognizedValue: string;
  currentValue: string;
  confidence: number;
  sourceImage: string | null;
  sourceType: string;
  rawText: string;
  manuallyEdited: boolean;
};
export default function EvidenceCenter({
  itemId,
  images,
  reload,
}: {
  itemId: string;
  images: ItemImage[];
  reload: () => Promise<void>;
}) {
  const [kind, setKind] = useState("product");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    api<Evidence[]>(`/items/${itemId}/provenance`)
      .then(setEvidence)
      .catch((e) => setError(e.message));
  }, [itemId, images]);
  const act = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await action();
      await reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section>
      <div className="section-toolbar">
        <p>本机保存的照片、凭证与资料</p>
        <select aria-label="添加资料类型" value={kind} onChange={(e) => setKind(e.target.value)}>
          {Object.entries(attachmentTypes).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
        <button className="button primary" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "处理中…" : "添加资料"}
        </button>
        <input
          ref={input}
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          aria-label="上传物品凭证"
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            e.target.value = "";
            if (!files.length) return;
            const body = new FormData();
            files.forEach((f) => body.append("files", f));
            body.append("type", kind);
            void act(() => api(`/items/${itemId}/images`, { method: "POST", body }));
          }}
        />
      </div>
      {error && <p role="alert">{error}</p>}
      {images.some((image) => image.type === "product") && <details>
        <summary>管理本体照片</summary>
        <div className="evidence-grid">{images.filter((image) => image.type === "product").map((image) => <article className="panel product-photo-management" key={image.id}>
          <a href={image.filePath} target="_blank" rel="noreferrer"><img src={image.filePath} alt={image.originalFilename || "物品照片"} width="160" height="120" style={{ objectFit: "contain", maxWidth: "100%" }} /></a>
          <p>{image.originalFilename || "物品照片"}</p>
          <select aria-label={`资料 ${image.id} 类型`} value={image.type} disabled={busy} onChange={(e) => void act(() => api(`/images/${image.id}`, json("PATCH", { type: e.target.value })))}>
            {Object.entries(attachmentTypes).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <button className="button secondary" disabled={busy} onClick={() => { if (window.confirm("删除这张照片及本地文件？")) void act(() => api(`/images/${image.id}`, { method:"DELETE" })); }}>删除资料</button>
        </article>)}</div>
      </details>}
      <div className="evidence-grid">
        {images.filter((image) => image.type !== "product").map((image) => (
          <article className="panel evidence-card" key={image.id}>
            <a href={image.filePath} target="_blank" rel="noreferrer">
              <img src={image.filePath} alt={image.originalFilename || "资料图片"} />
            </a>
            <p>{image.originalFilename || "资料图片"}</p>
            {image.assetMetadata?.isSynthetic && <>
              <p className="demo-label">合成演示资料 · 非真实购物凭证</p>
              <p>{image.assetMetadata.brand} · {image.assetMetadata.model}</p>
              <p>{image.assetMetadata.bindingSource === "owner-confirmed" ? "用户确认资料" : image.assetMetadata.modelVerified ? "图内型号一致" : "型号／规格待核实"} · {image.assetMetadata.reviewNote}</p>
            </>}
            <a className="button secondary" href={image.filePath} target="_blank" rel="noreferrer">查看大图</a>
            <select
              aria-label={`资料 ${image.id} 类型`}
              value={image.type}
              disabled={busy}
              onChange={(e) =>
                void act(() => api(`/images/${image.id}`, json("PATCH", { type: e.target.value })))
              }
            >
              {Object.entries(attachmentTypes).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => {
                if (window.confirm("删除这张资料及本地文件？"))
                  void act(() => api(`/images/${image.id}`, { method: "DELETE" }));
              }}
            >
              删除资料
            </button>
          </article>
        ))}
      </div>
      <h3>建档识别依据</h3>
      {!evidence.length && <p>当前没有 OCR 建档来源记录；手动填写的字段不会伪装为识别结果。</p>}
      {evidence.map((e, i) => (
        <article className="record-row evidence-row" key={i}>
          <div>
            <b>{e.field}</b>
            <p>
              OCR 候选：{e.recognizedValue} · 当前值：{String(e.currentValue ?? "")}
            </p>
            <p>
              {e.manuallyEdited ? "已人工修改" : "与 OCR 候选一致"} · 置信度{" "}
              {(e.confidence * 100).toFixed(1)}% · 来源：
              {attachmentTypes[e.sourceType] || e.sourceType}
            </p>
            <details>
              <summary>OCR 原文</summary>
              <pre>{e.rawText}</pre>
            </details>
            {e.sourceImage && (
              <a href={e.sourceImage} target="_blank" rel="noreferrer">
                来源图片
              </a>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}
