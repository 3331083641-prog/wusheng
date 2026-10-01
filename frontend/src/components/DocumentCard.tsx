import { BookOpen, Download, FileText } from "lucide-react";
import type { Document } from "../types";
export default function DocumentCard({ document }: { document: Document }) {
  return (
    <article className="document-card">
      <span className="icon-well blue">
        <FileText />
      </span>
      <div>
        <b>{document.filename}</b>
        <p>
          上传于 {document.uploadedAt.slice(0, 10)} ·{" "}
          {document.extractedText ? "已解析可引用文字" : "已存档 · 暂无可读文本"}
        </p>
      </div>
      <a
        className="icon-button"
        href={document.filePath}
        target="_blank"
        rel="noreferrer"
        aria-label={`查看 ${document.filename}`}
      >
        <BookOpen size={19} />
      </a>
      <a
        className="icon-button"
        href={document.filePath}
        download
        aria-label={`下载 ${document.filename}`}
      >
        <Download size={18} />
      </a>
    </article>
  );
}
