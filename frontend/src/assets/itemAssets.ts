import type { Item } from "../types";
import assetManifest from "./itemAssets.json";

export interface ProductAsset {
  src: string;
  width?: number;
  height?: number;
  objectPosition: string;
}

/** Original user-supplied PNGs. One source for cards, detail views and context panels. */
export const ITEM_ASSETS: Readonly<Record<string, ProductAsset>> = assetManifest;

const legacyAssets = new Map<string, ProductAsset>(
  Object.entries(ITEM_ASSETS).map(([id, asset]) => [`/assets/${id}.jpg`, asset]),
);
legacyAssets.set("/assets/headphones-detail.jpg", ITEM_ASSETS.headphones);
const currentAssets = new Map(Object.values(ITEM_ASSETS).map((asset) => [asset.src, asset]));

export type ProductItem = Pick<Item, "id" | "name" | "coverImage">;

/** Resolve presentation only: no database/seed updates and no replacement of uploaded photos. */
export function resolveProductAsset(item?: ProductItem, source?: string): ProductAsset {
  const src = source ?? item?.coverImage ?? "";
  if (item && (!src || src === "/assets/no-photo.svg") && ITEM_ASSETS[item.id]) {
    return ITEM_ASSETS[item.id];
  }
  const asset = legacyAssets.get(src) ?? currentAssets.get(src);
  if (asset) return asset;
  // Historical UI-only fixture uses "ink" as the printer ID. Ink consumables remain ink photos.
  if (item?.id === "ink" && src === "/assets/ink.jpg") return ITEM_ASSETS.printer;
  return { src: src || "/assets/no-photo.svg", objectPosition: "50% 50%" };
}
