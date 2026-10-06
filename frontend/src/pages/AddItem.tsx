import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, Check, FileText, ScanLine } from "lucide-react";
import { PageHeader } from "../components/ui";
import ImageUploader, { type UploadImage } from "../components/ImageUploader";
import RecognitionPanel, { emptyForm, type ItemForm } from "../components/RecognitionPanel";
import { api, json } from "../api";
import type { Item, Recognition, DraftImage } from "../types";
import { useStore } from "../store";
export default function AddItem() {
  const [manual, setManual] = useState(false);
  const [images, setImages] = useState<UploadImage[]>([]);
  const [form, setForm] = useState<ItemForm>({ ...emptyForm });
  const [result, setResult] = useState<Recognition | null>(null);
  const [busy, setBusy] = useState(false);
  const [recognizing, setRecognizing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const draft = useRef<string | null>(null);
  const saved = useRef(false);
  const previews = useRef(new Set<string>());
  const fileLock = useRef(false);
  useEffect(
    () => () => {
      previews.current.forEach((url) => URL.revokeObjectURL(url));
      previews.current.clear();
      if (draft.current && !saved.current) {
        void fetch(`/api/drafts/${draft.current}`, { method: "DELETE", keepalive: true }).catch(
          () => console.warn("草稿即时清理未完成；未保存草稿会在 24 小时后清理"),
        );
      }
    },
    [],
  );
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { refresh, notify } = useStore();
  const addImages = async (files: File[], type: string) => {
    if (!files.length || fileLock.current) return;
    fileLock.current = true;
    setUploading(true);
    setError("");
    setResult(null);
    const additions: UploadImage[] = files.map((file) => {
      const preview = URL.createObjectURL(file);
      previews.current.add(preview);
      return { file, preview, type, state: "uploading" };
    });
    setImages((current) => [...current, ...additions]);
    try {
      if (!draft.current)
        draft.current = (await api<{ id: string }>("/drafts", json("POST", {}))).id;
      const body = new FormData();
      files.forEach((file) => body.append("files", file));
      body.append("type", type);
      const uploaded = await api<DraftImage[]>(`/drafts/${draft.current}/images`, {
        method: "POST",
        body,
      });
      setImages((current) =>
        current.map((image) => {
          const index = additions.findIndex((a) => a.preview === image.preview);
          return index < 0 ? image : { ...image, id: uploaded[index].id, state: "success" };
        }),
      );
    } catch (e) {
      additions.forEach((image) => {
        URL.revokeObjectURL(image.preview);
        previews.current.delete(image.preview);
      });
      setImages((current) =>
        current.filter((image) => !additions.some((a) => a.preview === image.preview)),
      );
      setError((e as Error).message);
    } finally {
      fileLock.current = false;
      setUploading(false);
    }
  };
  const removeImage = async (image: UploadImage) => {
    if (!image.id || fileLock.current) return;
    fileLock.current = true;
    setUploading(true);
    setError("");
    try {
      await api(`/drafts/${draft.current}/images/${image.id}`, { method: "DELETE" });
      setImages((current) => current.filter((i) => i.id !== image.id));
      setResult(null);
      URL.revokeObjectURL(image.preview);
      previews.current.delete(image.preview);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      fileLock.current = false;
      setUploading(false);
    }
  };
  const changeType = async (image: UploadImage, type: string) => {
    if (!image.id || fileLock.current) return;
    fileLock.current = true;
    setUploading(true);
    setError("");
    try {
      await api(`/drafts/${draft.current}/images/${image.id}`, json("PATCH", { type }));
      setImages((current) => current.map((i) => (i.id === image.id ? { ...i, type } : i)));
      setResult(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      fileLock.current = false;
      setUploading(false);
    }
  };
  const recognize = async () => {
    setRecognizing(true);
    setBusy(true);
    setError("");
    try {
      const r = await api<Recognition>(`/drafts/${draft.current}/recognize`, json("POST", {}));
      setResult(r);
      setForm((prev) => {
        const values = { ...prev };
        Object.values(r.fields).forEach((c) => {
          if (c.field in values) values[c.field] = c.value;
        });
        return values;
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      setRecognizing(false);
    }
  };
  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const item = await api<Item>(
        "/items",
        json("POST", {
          ...form,
          purchasePrice: Number(form.purchasePrice || 0),
          warrantyMonths: Number(form.warrantyMonths),
          returnWindowDays: Number(form.returnWindowDays),
          recognitionSessionId: result?.sessionId,
          draftSessionId: images.length ? draft.current : undefined,
        }),
      );
      saved.current = true;
      await refresh();
      notify("档案已建立，退换与保修提醒已同步");
      navigate(`/items/${item.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="page">
      <PageHeader
        title="添加物品"
        description="通过拍照识别或手动录入，快速建立你的物品档案，让每一件物品都有记录。"
      />
      <div className="entry-modes">
        <button
          className={!manual ? "selected" : ""}
          disabled={busy || uploading}
          onClick={() => setManual(false)}
        >
          <Camera size={28} />
          <div>
            <h3>拍照识别建档</h3>
            <p>多图本地 OCR，识别可读文字</p>
          </div>
        </button>
        <button
          className={manual ? "selected" : ""}
          disabled={busy || uploading}
          onClick={() => setManual(true)}
        >
          <FileText size={28} />
          <div>
            <h3>手动录入</h3>
            <p>适用于没有文字或无法识别的物品</p>
          </div>
        </button>
      </div>
      <div className="creation-steps">
        {["上传图片", "AI 识别", "确认信息", "保存建档"].map((s, i) => (
          <div key={s} className={i <= (result ? 2 : busy ? 1 : 0) ? "active" : ""}>
            <span>{i + 1}</span>
            <div>
              <b>{s}</b>
              <small>
                {["物品与购买凭证", "融合可追溯候选", "允许逐项修改", "形成数字档案"][i]}
              </small>
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={save}>
        <div className={`add-grid ${manual ? "manual" : ""}`}>
          {!manual && (
            <div>
              <ImageUploader
                images={images}
                onAdd={(files, type) => void addImages(files, type)}
                onRemove={(image) => void removeImage(image)}
                onTypeChange={(image, type) => void changeType(image, type)}
                busy={busy || uploading}
                uploading={uploading}
              />
              <button
                className="button primary recognize-button"
                type="button"
                disabled={!images.length || busy || uploading}
                onClick={recognize}
              >
                <ScanLine size={18} />
                {busy ? "正在处理…" : result ? "重新识别" : "开始识别"}
              </button>
              <p className="data-footnote">
                来源置信度是 OCR 与规则评分，并非经评测的整体准确率。默认保修 12 月、退换 7
                天，请依据凭证确认。
              </p>
            </div>
          )}
          <div>
            <RecognitionPanel
              form={form}
              setForm={setForm}
              result={result}
              busy={recognizing}
              manual={manual}
            />
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <div className="form-actions">
              <button
                type="button"
                className="button secondary"
                disabled={busy || uploading}
                onClick={() => setManual(!manual)}
              >
                {manual ? "转为拍照识别" : "转为手动补充"}
              </button>
              <button
                className="button primary"
                disabled={busy || uploading || (!manual && !images.length)}
              >
                <Check size={18} />
                {busy && !recognizing ? "保存中…" : "确认并保存"}
              </button>
            </div>
          </div>
        </div>
      </form>
    </main>
  );
}
