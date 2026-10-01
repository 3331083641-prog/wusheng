import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, Check, FileText, ScanLine } from "lucide-react";
import { PageHeader } from "../components/ui";
import ImageUploader, { type UploadImage } from "../components/ImageUploader";
import RecognitionPanel, { emptyForm, type ItemForm } from "../components/RecognitionPanel";
import { api, json } from "../api";
import type { Item, Recognition } from "../types";
import { useStore } from "../store";
export default function AddItem() {
  const [manual, setManual] = useState(false);
  const [images, setImages] = useState<UploadImage[]>([]);
  const [form, setForm] = useState<ItemForm>({ ...emptyForm });
  const [result, setResult] = useState<Recognition | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { refresh, notify } = useStore();
  const recognize = async () => {
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      images.forEach((i) => {
        body.append("files", i.file);
        body.append("types", i.type);
      });
      const r = await api<Recognition>("/recognize", { method: "POST", body });
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
          images: result?.images || [],
        }),
      );
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
        <button className={!manual ? "selected" : ""} onClick={() => setManual(false)}>
          <Camera size={28} />
          <div>
            <h3>拍照识别建档</h3>
            <p>多图本地 OCR，识别可读文字</p>
          </div>
        </button>
        <button className={manual ? "selected" : ""} onClick={() => setManual(true)}>
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
              <ImageUploader images={images} onChange={setImages} busy={busy} />
              <button
                className="button primary recognize-button"
                type="button"
                disabled={!images.length || busy}
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
              busy={busy}
              manual={manual}
            />
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <div className="form-actions">
              <button type="button" className="button secondary" onClick={() => setManual(!manual)}>
                {manual ? "转为拍照识别" : "转为手动补充"}
              </button>
              <button className="button primary" disabled={busy || (!manual && !result)}>
                <Check size={18} />
                确认并保存
              </button>
            </div>
          </div>
        </div>
      </form>
    </main>
  );
}
