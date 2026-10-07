import { useRef, useState } from "react";
import { Camera, FileText, Package, Receipt, X } from "lucide-react";
export interface UploadImage {
  file: File;
  preview: string;
  type: string;
  id?: string;
  state: "uploading" | "success";
}
export default function ImageUploader({
  images,
  onAdd,
  onRemove,
  onTypeChange,
  busy,
  uploading,
}: {
  images: UploadImage[];
  onAdd: (files: File[], type: string) => void;
  onRemove: (image: UploadImage) => void;
  onTypeChange: (image: UploadImage, type: string) => void;
  uploading: boolean;
  busy: boolean;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const kind = useRef("product");
  const dragDepth = useRef(0);
  const choose = (type = "product") => {
    if (busy) return;
    kind.current = type;
    ref.current?.removeAttribute("capture");
    ref.current?.click();
  };
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState("");
  const add = (files: File[]) => {
    setError("");
    if (images.length + files.length > 10) {
      setError("一次最多上传 10 张图片");
      return;
    }
    if (
      files.some(
        (f) =>
          !["image/jpeg", "image/png", "image/webp"].includes(f.type) || f.size > 10 * 1024 * 1024,
      )
    ) {
      setError("仅支持 JPG、PNG、WebP，每张不超过 10MB");
      return;
    }
    onAdd(files, kind.current);
  };
  return (
    <section className="panel upload-panel">
      <header>
        <h3>1. 上传物品照片</h3>
        <small>图片留在本机，不上传外部模型</small>
      </header>
      <div
        className={`dropzone ${drag ? "dragging" : ""} ${busy ? "scanning" : ""}`}
        role="button"
        tabIndex={busy ? -1 : 0}
        aria-label="点击上传图片或拖拽到此处"
        aria-disabled={busy}
        onClick={() => choose()}
        onKeyDown={(e) => {
          if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            choose();
          }
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          dragDepth.current++;
          if (!busy) setDrag(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!busy) setDrag(true);
        }}
        onDragLeave={() => {
          dragDepth.current--;
          if (dragDepth.current <= 0) setDrag(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          dragDepth.current = 0;
          kind.current = "product";
          if (!busy) add(Array.from(e.dataTransfer.files));
        }}
      >
        <div className="scan-line" />
        <span className="camera-circle">
          <Camera size={38} />
        </span>
        <h3>点击上传图片或拖拽到此处</h3>
        <p>支持多图 JPG、PNG、WebP，单张不超过 10MB</p>
        <button
          type="button"
          className="button primary"
          disabled={busy}
          onClick={(e) => {
            e.stopPropagation();
            choose();
          }}
        >
          选择图片
        </button>
        <button
          type="button"
          className="button secondary"
          disabled={busy}
          onClick={(e) => {
            e.stopPropagation();
            kind.current = "product";
            if (ref.current) {
              ref.current.setAttribute("capture", "environment");
              ref.current.click();
            }
          }}
        >
          拍照添加
        </button>
        <input
          ref={ref}
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          disabled={busy}
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => {
            add(Array.from(e.target.files || []));
            e.target.value = "";
            e.target.removeAttribute("capture");
          }}
          aria-label="上传物品图片"
        />
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <div className="upload-types">
        {[
          { icon: Camera, label: "物品本体照片", type: "product" },
          { icon: Receipt, label: "小票 / 发票", type: "receipt" },
          { icon: Package, label: "包装盒 / 铭牌", type: "label" },
          { icon: FileText, label: "说明书照片", type: "manual_image" },
        ].map(({ icon: Icon, label, type }) => (
          <button type="button" key={type} disabled={busy} onClick={() => choose(type)}>
            <Icon size={23} />
            <b>{label}</b>
          </button>
        ))}
      </div>
      {uploading && (
        <p role="status" className="data-footnote">
          上传中… 图片正保存到本机草稿
        </p>
      )}
      <div className="uploaded-images">
        {images.map((image, i) => (
          <div key={image.preview}>
            <img src={image.preview} alt={`上传图片 ${i + 1}`} />
            <button
              type="button"
              aria-label={`移除图片 ${i + 1}`}
              className="remove-image"
              disabled={busy}
              onClick={() => onRemove(image)}
            >
              <X size={15} />
            </button>
            <small className="upload-file-name" title={image.file.name}>
              {image.file.name}
            </small>
            <small>
              {(image.file.size / 1024 / 1024).toFixed(2)} MB ·{" "}
              {image.state === "uploading" ? "上传中…" : "本地已保存"}
            </small>
            <select
              aria-label={`图片 ${i + 1} 类型`}
              value={image.type}
              disabled={busy}
              onChange={(e) => onTypeChange(image, e.target.value)}
            >
              <option value="product">物品照片</option>
              <option value="receipt">小票 / 发票</option>
              <option value="label">包装 / 铭牌</option>
              <option value="manual_image">说明书</option>
            </select>
          </div>
        ))}
      </div>
    </section>
  );
}
