import type { Item } from "../types";

export interface ProductAsset {
  src: string;
  width?: number;
  height?: number;
  objectPosition: string;
}

const hd = (filename: string, objectPosition = "50% 50%"): ProductAsset => ({
  src: `/assets/items/${filename}`,
  width: 1448,
  height: 1086,
  objectPosition,
});

/** Original user-supplied PNGs. One source for cards, detail views and context panels. */
export const ITEM_ASSETS: Readonly<Record<string, ProductAsset>> = {
  laptop: hd("macbook-air-m2.png"),
  headphones: hd("sony-wh1000xm6.png", "50% 32%"),
  washer: hd("haier-washer.png", "50% 36%"),
  ac: hd("midea-air-conditioner.png"),
  robot: hd("xiaomi-robot-vacuum.png", "50% 60%"),
  coffee: hd("delonghi-coffee-machine.png", "50% 38%"),
  toothbrush: hd("philips-electric-toothbrush.png", "50% 30%"),
  suitcase: hd("rimowa-suitcase.png", "50% 36%"),
  purifier: hd("xiaomi-air-purifier.png", "50% 55%"),
  printer: hd("hp-printer.png", "50% 60%"),
};

const legacyAssets = new Map<string, ProductAsset>(
  Object.entries(ITEM_ASSETS).map(([id, asset]) => [`/assets/${id}.jpg`, asset]),
);
legacyAssets.set("/assets/headphones-detail.jpg", ITEM_ASSETS.headphones);
const currentAssets = new Map(Object.values(ITEM_ASSETS).map((asset) => [asset.src, asset]));

export type ProductItem = Pick<Item, "id" | "name" | "coverImage">;

/** Resolve presentation only: no database/seed updates and no replacement of uploaded photos. */
export function resolveProductAsset(item?: ProductItem, source?: string): ProductAsset {
  const src = source ?? item?.coverImage ?? "";
  const asset = legacyAssets.get(src) ?? currentAssets.get(src);
  if (asset) return asset;
  if (item && (!src || src === "/assets/no-photo.svg") && ITEM_ASSETS[item.id]) {
    return ITEM_ASSETS[item.id];
  }
  // Historical UI-only fixture uses "ink" as the printer ID. Ink consumables remain ink photos.
  if (item?.id === "ink" && src === "/assets/ink.jpg") return ITEM_ASSETS.printer;
  return { src: src || "/assets/no-photo.svg", objectPosition: "50% 50%" };
}
