import { useState } from "react";
import { BookOpen, Download, FileText, Trash2 } from "lucide-react";
import type { Document } from "../types";
import { Drawer } from "./ui";
import { api } from "../api";
export default function DocumentCard({
  document,
  onDelete,
  onUpdate,
}: {
  document: Document;
  onDelete: () => Promise<void>;
  onUpdate?: () => Promise<void>;
}) {
  const [confirm, setConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [ocrBusy, setOCRBusy] = useState(false);
  const [ocrError, setOCRError] = useState("");
  const name = document.originalFilename || document.filename;
  const remove = async () => {
    setDeleting(true);
    try {
      await onDelete();
      setConfirm(false);
    } finally {
      setDeleting(false);
    }
  };
  return (
    <>
      <article className="document-card">
        <span className="icon-well blue">
          <FileText />
        </span>
        <div>
          <b>{name}</b>
          {document.assetMetadata && <p>{document.assetMetadata.scope} {document.assetMetadata.language} {document.assetMetadata.modelReview}</p>}
          {document.assetMetadata?.sourceUrl && <a href={document.assetMetadata.sourceUrl} target="_blank" rel="noreferrer">厂商来源</a>}
          <p>
            {document.pageCount ?? "未知"} 页 · {(document.fileSize / 1024 / 1024).toFixed(2)} MB ·{" "}
            {document.uploadedAt.slice(0, 10)} 上传
          </p>
          <p>
            {document.assetMetadata?.excludedFromAI
              ? "型号待复核，不用于 AI 引用"
              : document.textStatus === "ocr_processing"
              ? "正在本地识别…"
              : document.extractedText
                ? "已提取文字，可供 AI 引用"
                : "扫描型 PDF / 暂无可提取文字"}
          </p>
          {document.ocrError && <p>{document.ocrError}</p>}
          {!document.extractedText && (
            <button
              className="button secondary"
              disabled={ocrBusy || document.textStatus === "ocr_processing"}
              onClick={async () => {
                setOCRBusy(true);
                setOCRError("");
                try {
                  await api(`/documents/${document.id}/ocr`, { method: "POST" });
                  await onUpdate?.();
                } catch (e) {
                  setOCRError((e as Error).message);
                } finally {
                  setOCRBusy(false);
                }
              }}
            >
              {ocrBusy ? "识别请求中…" : "本地识别文本"}
            </button>
          )}
          {ocrError && <p role="alert">{ocrError}</p>}
        </div>
        <a
          className="icon-button"
          href={document.filePath}
          target="_blank"
          rel="noreferrer"
          aria-label={`查看 ${name}`}
          title="查看"
        >
          <BookOpen size={19} />
        </a>
        <a
          className="icon-button"
          href={`${document.filePath}?download=true`}
          download={name}
          aria-label={`下载 ${name}`}
          title="下载"
        >
          <Download size={18} />
        </a>
        <button
          type="button"
          className="icon-button"
          title="删除"
          aria-label={`删除 ${name}`}
          disabled={deleting}
          onClick={() => setConfirm(true)}
        >
          <Trash2 size={18} />
        </button>
      </article>
      {confirm && (
        <Drawer
          title="删除说明书"
          onClose={() => {
            if (!deleting) setConfirm(false);
          }}
        >
          <p>确定删除《{name}》？本地 PDF 文件及数据库记录将一并删除。</p>
          <button
            type="button"
            className="button primary"
            disabled={deleting}
            onClick={() => void remove()}
          >
            {deleting ? "删除中…" : "确认删除"}
          </button>
        </Drawer>
      )}
    </>
  );
}
