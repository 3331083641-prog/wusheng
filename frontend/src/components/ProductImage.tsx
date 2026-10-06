import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { Package } from "lucide-react";
import { resolveProductAsset, type ProductAsset, type ProductItem } from "../assets/itemAssets";

interface Props {
  asset?: ProductAsset;
  item?: ProductItem;
  src?: string;
  alt?: string;
  className?: string;
  priority?: boolean;
  fit?: "cover" | "contain";
  objectPosition?: string;
}

export default function ProductImage({ item, src, alt, asset: providedAsset, ...props }: Props) {
  const asset = providedAsset ?? resolveProductAsset(item, src);
  return (
    <ImageFrame
      key={asset.src}
      asset={asset}
      alt={alt ?? item?.name ?? "物品图片"}
      label={item?.name || alt || "物品图片"}
      {...props}
    />
  );
}

function ImageFrame({
  asset,
  alt,
  label,
  className = "",
  priority = false,
  fit = "cover",
  objectPosition,
}: Omit<Props, "item" | "src"> & { asset: ProductAsset; alt: string; label: string }) {
  const image = useRef<HTMLImageElement>(null);
  const decoding = useRef(false);
  const [state, setState] = useState<"loading" | "loaded" | "error">("loading");
  const failed = () => {
    setState("error");
    console.warn(`[Wusheng ProductImage] 图片加载失败：${label} (${asset.src})`);
  };
  const loaded = useCallback(async () => {
    const target = image.current;
    if (!target || !target.naturalWidth || decoding.current) return;
    decoding.current = true;
    // Wait for full-resolution decode before revealing the image. Rejected decode still
    // permits a valid native image; broken network images use the onError fallback.
    await target.decode().catch(() => undefined);
    if (image.current === target && target.naturalWidth) setState("loaded");
  }, []);
  useEffect(() => {
    if (image.current?.complete && image.current.naturalWidth) void loaded();
    // The keyed frame remounts when src changes, including cached images.
  }, [loaded]);
  const style = {
    "--product-fit": fit,
    "--product-position": objectPosition ?? asset.objectPosition,
  } as CSSProperties;
  return (
    <span className={`product-image ${className}`} data-image-state={state} style={style}>
      {state === "loading" && <span className="product-image-skeleton" aria-hidden="true" />}
      {state === "error" ? (
        <span className="product-image-fallback" role="img" aria-label={`${label}图片暂不可用`}>
          <Package size={28} aria-hidden="true" />
        </span>
      ) : (
        <img
          ref={image}
          src={asset.src}
          alt={alt}
          width={asset.width}
          height={asset.height}
          loading={priority ? "eager" : "lazy"}
          fetchPriority={priority ? "high" : "auto"}
          decoding="async"
          onLoad={() => void loaded()}
          onError={failed}
        />
      )}
    </span>
  );
}
