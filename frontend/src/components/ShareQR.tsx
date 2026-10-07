import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { api } from "../api";
import type { Detail } from "../types";
type Network = {
  mode: string;
  reachable: boolean;
  recommendedBaseUrl: string;
  lanAddresses: string[];
};
const optionLabels = {
  showPurchaseDate: "购买日期",
  showWarranty: "保修状态",
  showLifecycle: "生命周期（事件类别与日期）",
  showConsumables: "耗材状态",
  showManualNames: "说明书文件名（请确认文件名无隐私）",
};
export default function ShareQR({ detail }: { detail: Detail }) {
  const itemId = detail.item.id;
  const [network, setNetwork] = useState<Network>();
  const [address, setAddress] = useState("");
  const [url, setUrl] = useState("");
  const [qr, setQR] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [lifetime, setLifetime] = useState("7d");
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [options, setOptions] = useState({
    showPurchaseDate: false,
    showWarranty: true,
    showLifecycle: true,
    showConsumables: true,
    showManualNames: false,
  });
  const create = async (regenerate = true) => {
    setBusy(true);
    setError("");
    try {
      const link = await api<{ url: string; expiresAt: string | null }>(
        `/items/${itemId}/share?regenerate=${regenerate}&address=${encodeURIComponent(address)}`,
        {
          method: "POST",
          body: JSON.stringify({ lifetime, options }),
        },
      );
      setUrl(link.url);
      setExpiresAt(link.expiresAt);
      setQR(await QRCode.toDataURL(link.url, { width: 360, margin: 2 }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    api<Network>("/network/share-info")
      .then(setNetwork)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <div className="qr-view">
      <p>{network?.mode === "lan" ? "局域网模式" : "本机模式"}</p>
      <>
        <label>
          分享有效期
          <select
            aria-label="分享有效期"
            value={lifetime}
            disabled={busy || !!qr}
            onChange={(e) => setLifetime(e.target.value)}
          >
            <option value="24h">24 小时</option>
            <option value="7d">7 天（默认）</option>
            <option value="30d">30 天</option>
            <option value="forever">长期有效</option>
          </select>
        </label>
        <fieldset disabled={busy || !!qr}>
          <legend>分享内容预览</legend>
          <p>显示物品名称、品牌、型号、维护状态及本体图片。</p>
          <p>
            {detail.item.name} · {detail.item.brand || "未记录品牌"} ·{" "}
            {detail.item.model || "未记录型号"}
          </p>
          {Object.entries(optionLabels).map(([key, label]) => (
            <label key={key} style={{ display: "block" }}>
              <input
                type="checkbox"
                checked={options[key as keyof typeof options]}
                onChange={(e) => setOptions({ ...options, [key]: e.target.checked })}
              />{" "}
              {label}
            </label>
          ))}
          <small>
            隐藏序列号、价格、渠道、票据、发票、维修备注和说明书全文。生命周期只分享事件类别与日期。
          </small>
          {options.showWarranty && <p>保修截止：{detail.item.warrantyEndDate || "未记录"}</p>}
          <p>下一次维护：{detail.item.nextMaintenance || "未记录"}</p>
          {options.showPurchaseDate && <p>购买日期：{detail.item.purchaseDate}</p>}
          {options.showConsumables && (
            <p>
              耗材：
              {detail.consumables.map((c) => `${c.name}（${c.status}）`).join("、") || "暂无"}
            </p>
          )}
          {options.showManualNames && (
            <p>
              说明书文件名：
              {detail.documents.map((d) => d.originalFilename || d.filename).join("、") || "暂无"}
            </p>
          )}
        </fieldset>
      </>
      {network && !network.reachable ? (
        <>
          <p>当前应用仅允许本机访问，手机扫码无法打开。</p>
          <p>
            请运行 <code>scripts/start_lan.ps1</code> 后，使用本机地址打开管理界面。
          </p>
        </>
      ) : (
        <>
          {network && network.lanAddresses.length > 1 && (
            <label>
              分享网络地址
              <select
                aria-label="分享网络地址"
                value={address || network.lanAddresses[0]}
                onChange={(e) => {
                  setAddress(e.target.value);
                  setQR("");
                  setUrl("");
                }}
              >
                {network.lanAddresses.map((ip) => (
                  <option key={ip}>{ip}</option>
                ))}
              </select>
            </label>
          )}
          {!qr && (
            <button
              className="button primary"
              disabled={!network || busy}
              onClick={() => void create()}
            >
              生成只读二维码
            </button>
          )}
          {qr && (
            <>
              <img src={qr} alt="物品档案二维码" />
              <p>
                {expiresAt
                  ? `到期时间：${new Date(expiresAt).toLocaleString()}`
                  : "长期有效，请主动撤销"}
              </p>
              <small>
                修改分享范围或有效期：撤销后重新设置并生成。重新生成会立即作废旧二维码。
              </small>
              <p>
                <a href={url} target="_blank" rel="noreferrer">
                  {url}
                </a>
              </p>
              <a className="button primary" href={qr} download={`物生-${itemId}.png`}>
                下载 PNG
              </a>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => void create(true)}
              >
                重新生成访问令牌
              </button>
              <button
                className="button secondary"
                onClick={() =>
                  navigator.clipboard
                    .writeText(url)
                    .catch(() => setError("无法自动复制，请选中地址复制"))
                }
              >
                复制访问地址
              </button>
              <button
                className="button secondary"
                disabled={busy}
                onClick={async () => {
                  try {
                    await api(`/items/${itemId}/share`, { method: "DELETE" });
                    setQR("");
                    setUrl("");
                    setError("二维码已撤销");
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                撤销二维码
              </button>
            </>
          )}
          <small>
            仅可查看。同一 Wi-Fi、主机服务开启时可访问；IP
            改变后需要重新下载二维码。如手机无法访问，请检查 Windows
            私人网络、防火墙与访客网络隔离。本应用不会修改防火墙。
          </small>
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
