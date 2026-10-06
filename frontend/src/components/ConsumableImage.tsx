import { resolveConsumableAsset, type ConsumablePhoto } from "../assets/consumableAssets";
import ProductImage from "./ProductImage";

export default function ConsumableImage({
  consumable,
  className = "",
  priority = false,
}: {
  consumable: ConsumablePhoto;
  className?: string;
  priority?: boolean;
}) {
  return (
    <ProductImage
      asset={resolveConsumableAsset(consumable)}
      alt={consumable.name}
      className={`consumable-image ${className}`}
      fit="contain"
      objectPosition="50% 50%"
      priority={priority}
    />
  );
}
