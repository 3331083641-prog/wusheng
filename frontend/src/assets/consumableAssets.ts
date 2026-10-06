import type { Consumable } from "../types";
import type { ProductAsset } from "./itemAssets";

const hd = (filename: string): ProductAsset => ({
  src: `/assets/consumables/${filename}`,
  width: 1448,
  height: 1086,
  objectPosition: "50% 50%",
});

/** User-supplied white-background PNG originals. Rendering never mutates business records. */
export const CONSUMABLE_ASSETS = {
  airPurifierFilter: hd("air-purifier-filter-cylinder.png"),
  laundryDetergent: hd("laundry-detergent-blue.png"),
  printerInk: hd("printer-ink-cartridges-cmy.png"),
  coffeeCapsules: hd("coffee-capsules-metallic.png"),
  toothbrushHeads: hd("toothbrush-heads-dual.png"),
  robotVacuumFilter: hd("robot-vacuum-filter-rect.png"),
} as const;

type AssetKey = keyof typeof CONSUMABLE_ASSETS;
export type ConsumablePhoto = Pick<Consumable, "id" | "itemId" | "name" | "coverImage">;

const bindings: { id: string; itemId: string; name: string; legacy: string; key: AssetKey }[] = [
  {
    id: "purifier-filter",
    itemId: "purifier",
    name: "空气净化器滤芯",
    legacy: "/assets/filter.jpg",
    key: "airPurifierFilter",
  },
  {
    id: "detergent",
    itemId: "washer",
    name: "洗衣液",
    legacy: "/assets/detergent.jpg",
    key: "laundryDetergent",
  },
  {
    id: "ink-cartridge",
    itemId: "printer",
    name: "打印机墨盒",
    legacy: "/assets/ink.jpg",
    key: "printerInk",
  },
  {
    id: "capsules",
    itemId: "coffee",
    name: "咖啡胶囊",
    legacy: "/assets/capsules.jpg",
    key: "coffeeCapsules",
  },
  {
    id: "brushhead",
    itemId: "toothbrush",
    name: "电动牙刷刷头",
    legacy: "/assets/brushhead.jpg",
    key: "toothbrushHeads",
  },
  {
    id: "robot-filter",
    itemId: "robot",
    name: "扫地机器人滤网",
    legacy: "/assets/filter.jpg",
    key: "robotVacuumFilter",
  },
];
const byId = new Map(bindings.map((binding) => [binding.id, binding]));
const byDeviceAndName = new Map(
  bindings.map((binding) => [`${binding.itemId}/${binding.name}`, binding]),
);
const bySource = new Map(Object.values(CONSUMABLE_ASSETS).map((asset) => [asset.src, asset]));

export function resolveConsumableAsset(consumable: ConsumablePhoto): ProductAsset {
  const src = consumable.coverImage;
  const current = bySource.get(src);
  if (current) return current;
  // ID/association is necessary: both filter shapes previously shared /assets/filter.jpg.
  const binding =
    byId.get(consumable.id) ?? byDeviceAndName.get(`${consumable.itemId}/${consumable.name}`);
  if (binding && (src === binding.legacy || !src || src === "/assets/no-photo.svg")) {
    return CONSUMABLE_ASSETS[binding.key];
  }
  // Preserve user-uploaded photos and unknown consumables instead of guessing by filename.
  return { src: src || "/assets/no-photo.svg", objectPosition: "50% 50%" };
}
