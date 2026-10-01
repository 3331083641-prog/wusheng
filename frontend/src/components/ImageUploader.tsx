import { useRef, useState } from "react";
import { Camera, FileText, Package, Receipt, X } from "lucide-react";
export interface UploadImage {
  file: File;
  preview: string;
  type: string;
}
export default function ImageUploader({
  images,
  onChange,
  busy,
}: {
  images: UploadImage[];
  onChange: (images: UploadImage[]) => void;
  busy: boolean;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState("");
  const add = (files: File[]) => {
    setError("");
    if (images.length + files.length > 8) {
      setError("一次最多上传 8 张图片");
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
    onChange([
      ...images,
      ...files.map((file) => ({
        file,
        preview: URL.createObjectURL(file),
        type: "product",
      })),
    ]);
  };
  return (
    <section className="panel upload-panel">
      <header>
        <h3>1. 上传物品照片</h3>
        <small>图片留在本机，不上传外部模型</small>
      </header>
      <div
        className={`dropzone ${drag ? "dragging" : ""} ${busy ? "scanning" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
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
          onClick={() => ref.current?.click()}
        >
          选择图片
        </button>
        <input
          ref={ref}
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          onChange={(e) => {
            add(Array.from(e.target.files || []));
            e.target.value = "";
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
          [Camera, "物品本体照片"],
          [Receipt, "小票 / 发票"],
          [Package, "包装盒 / 铭牌"],
          [FileText, "说明书照片"],
        ].map(([Icon, label]) => {
          const I = Icon as typeof Camera;
          return (
            <div key={String(label)}>
              <I size={23} />
              <b>{String(label)}</b>
            </div>
          );
        })}
      </div>
      <div className="uploaded-images">
        {images.map((image, i) => (
          <div key={image.preview}>
            <img src={image.preview} alt={`上传图片 ${i + 1}`} />
            <button
              type="button"
              aria-label={`移除图片 ${i + 1}`}
              className="remove-image"
              disabled={busy}
              onClick={() => {
                URL.revokeObjectURL(image.preview);
                onChange(images.filter((_, n) => n !== i));
              }}
            >
              <X size={15} />
            </button>
            <select
              aria-label={`图片 ${i + 1} 类型`}
              value={image.type}
              disabled={busy}
              onChange={(e) =>
                onChange(images.map((v, n) => (n === i ? { ...v, type: e.target.value } : v)))
              }
            >
              <option value="product">物品照片</option>
              <option value="receipt">小票 / 发票</option>
              <option value="package">包装 / 铭牌</option>
              <option value="manual">说明书</option>
            </select>
          </div>
        ))}
      </div>
    </section>
  );
}
