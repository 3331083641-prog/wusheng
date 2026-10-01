import { motion } from "framer-motion";
import { Check, Info } from "lucide-react";
import type { Recognition } from "../types";
export type ItemForm = Record<string, string>;
export const emptyForm: ItemForm = {
  name: "",
  brand: "",
  model: "",
  category: "数码",
  purchasePrice: "",
  purchaseDate: "",
  purchaseChannel: "",
  warrantyMonths: "12",
  returnWindowDays: "7",
  serialNumber: "",
  description: "",
  location: "",
};
const fields = [
  ["name", "商品名称", "text"],
  ["brand", "品牌", "text"],
  ["model", "型号", "text"],
  ["category", "类别", "select"],
  ["purchasePrice", "购买价格（元）", "number"],
  ["purchaseDate", "购买日期", "date"],
  ["purchaseChannel", "购买渠道", "text"],
  ["warrantyMonths", "保修期限（月）", "number"],
  ["returnWindowDays", "退换期限（天）", "number"],
  ["serialNumber", "序列号", "text"],
  ["location", "存放位置", "text"],
];
export default function RecognitionPanel({
  form,
  setForm,
  result,
  busy,
  manual = false,
}: {
  form: ItemForm;
  setForm: (form: ItemForm) => void;
  result: Recognition | null;
  busy: boolean;
  manual?: boolean;
}) {
  return (
    <section className="panel recognition-panel">
      <header>
        <h3>{manual ? "填写物品档案" : "2. 识别结果与人工确认"}</h3>
        {result && (
          <span className="local-pill">
            <Check size={14} />
            本地 OCR
          </span>
        )}
      </header>
      {!manual && !result && !busy && (
        <div className="recognition-intro">
          <Info size={24} />
          <p>上传照片与小票后点击「开始识别」。识别到的字段会出现在这里，可逐项修改。</p>
          <small>没有可读文字的物品照片可能无法识别。系统不会猜测品牌与型号。</small>
        </div>
      )}
      {busy && (
        <div className="recognition-loading">
          <div className="skeleton" />
          <div className="skeleton" />
          <p>本地 OCR 正在阅读图片并融合字段…</p>
        </div>
      )}
      {result?.warnings.map((w) => (
        <p className="notice" key={w}>
          {w}
        </p>
      ))}
      <div className="form-grid">
        {fields.map(([field, label, type], i) => {
          const evidence = result?.fields[field];
          return (
            <motion.label
              key={field}
              initial={result ? { opacity: 0, y: 6 } : false}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: result ? i * 0.035 : 0 }}
            >
              {label}
              {["name", "purchaseDate"].includes(field) && <span className="required"> *</span>}
              {type === "select" ? (
                <select
                  aria-label={label}
                  value={form[field]}
                  onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                >
                  {["家电", "数码", "家居", "耗材", "其他"].map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              ) : (
                <input
                  aria-label={label}
                  type={type}
                  value={form[field]}
                  required={["name", "purchaseDate"].includes(field)}
                  maxLength={type === "text" ? 250 : undefined}
                  min={type === "number" ? 0 : undefined}
                  step={field === "purchasePrice" ? "0.01" : type === "number" ? 1 : undefined}
                  max={
                    field === "warrantyMonths"
                      ? 120
                      : field === "returnWindowDays"
                        ? 365
                        : undefined
                  }
                  onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                />
              )}
              {evidence && (
                <span
                  className={`confidence ${evidence.confidence < 0.8 ? "low" : ""}`}
                  title={`来源：${evidence.sourceImage}`}
                >
                  <span style={{ width: `${evidence.confidence * 100}%` }} />
                  候选置信度 {Math.round(evidence.confidence * 100)}%
                  {evidence.confidence < 0.8 ? " · 请核对" : ""}
                </span>
              )}
            </motion.label>
          );
        })}
        {form.status !== undefined && (
          <label className="full-width">
            生命周期状态
            <select
              aria-label="生命周期状态"
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              {["正常使用", "淘汰", "转卖", "回收"].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
            <small>维护和维修状态由记录推算；淘汰、转卖或回收会停止新的自动提醒。</small>
          </label>
        )}
        <label className="full-width">
          备注
          <textarea
            value={form.description}
            maxLength={500}
            rows={3}
            placeholder="使用场景、特殊情况等…"
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </label>
      </div>
      {result && (
        <details className="ocr-evidence">
          <summary>查看原始识别文字与字段来源（{result.candidates.length} 条候选）</summary>
          {result.candidates.map((c, i) => (
            <p key={i}>
              <b>{c.field}</b>：{c.value} · {Math.round(c.confidence * 100)}%
              <small>{c.sourceImage}</small>
            </p>
          ))}
        </details>
      )}
    </section>
  );
}
