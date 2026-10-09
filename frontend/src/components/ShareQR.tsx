import { useCallback, useEffect, useState } from "react";
import QRCode from "qrcode";
import { api } from "../api";
import type { Detail } from "../types";
type Network = {
  mode: string;
  reachable: boolean;
  recommendedBaseUrl: string;
  lanAddresses: string[];
  port: number;
};
const optionLabels = {
  showPurchaseDate: "购买日期",
  showWarranty: "保修状态",
  showLifecycle: "生命周期（事件类别与日期）",
  showConsumables: "耗材状态",
  showManualNames: "说明书文件名（请确认文件名无隐私）",
  showPurchasePrice: "购买价格（敏感信息）",
  showPurchaseChannel: "购买渠道（敏感信息）",
  showLocation: "存放位置（敏感信息）",
  showMaintenance: "维护记录（日期、类别、下次日期）",
  showRepairs: "维修记录（日期与状态）",
  showRecordDetails: "维护/维修费用与详细备注（可能含私人信息）",
  showConsumableStock: "耗材当前库存",
  showManualFiles: "允许查看所选说明书 PDF",
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
    showPurchasePrice: false,
    showPurchaseChannel: false,
    showLocation: false,
    showMaintenance: false,
    showRepairs: false,
    showRecordDetails: false,
    showConsumableStock: false,
    showManualFiles: false,
    showManualDownloads: false,
    shareFutureManuals: false,
  });
  const [manualDocumentIds, setManualDocumentIds] = useState<string[]>([]);
  const documents = detail.documents.filter(d => d.type === "manual" && d.mimeType === "application/pdf");
  const create = async (regenerate = true) => {
    setBusy(true);
    setError("");
    try {
      const link = await api<{ url: string; expiresAt: string | null }>(
        `/items/${itemId}/share?regenerate=${regenerate}&address=${encodeURIComponent(address)}`,
        {
          method: "POST",
          body: JSON.stringify({ lifetime, options: { ...options, manualDocumentIds } }),
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
  const detectNetwork = useCallback(async () => {
    setBusy(true);
    setError("");
    try {
      const info = await api<Network>("/network/share-info");
      setNetwork(info);
      setQR("");
      setUrl("");
      setExpiresAt(null);
      setAddress((current) => info.lanAddresses.includes(current) ? current : info.lanAddresses[0] || "");
    } catch (e) {
      setNetwork(undefined);
      setQR("");
      setUrl("");
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, []);
  useEffect(() => { void detectNetwork(); }, [detectNetwork]);
  return (
    <div className="qr-view">
      <p className={network?.reachable ? "share-ready" : undefined} role="status">
        {network?.reachable ? "● 局域网分享已就绪" : network ? "局域网分享尚未就绪" : "正在检测分享网络…"}
      </p>
      {network?.reachable && <p>http://{address}:{network.port}</p>}
      <p className="muted" style={{ fontSize: 12 }}>手机和电脑需连接同一 Wi-Fi 或可互通局域网，电脑保持物生运行，扫码后可查看只读档案。</p>
      <button className="button secondary" disabled={busy} onClick={() => void detectNetwork()}>
        重新检测网络
      </button>
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
                onChange={(e) => setOptions({ ...options, [key]: e.target.checked, ...(key === "showManualFiles" && !e.target.checked ? { showManualDownloads: false, shareFutureManuals: false } : {}) })}
              />{" "}
              {label}
            </label>
          ))}
          <small>
            完整序列号、票据和发票始终隐藏；价格、渠道、位置、备注及 PDF 仅在明确勾选后共享。生命周期只分享事件类别与日期。
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
          {options.showPurchasePrice && <p>购买价格：¥{detail.item.purchasePrice}</p>}
          {options.showPurchaseChannel && <p>购买渠道：{detail.item.purchaseChannel || "未记录"}</p>}
          {options.showLocation && <p>存放位置：{detail.item.location || "未记录"}</p>}
          {options.showManualFiles && <div className="manual-share-selection">
            <p>开启后，持有有效二维码的设备可以查看所授权的说明书。请确保 PDF 不包含私人信息。</p>
            <small>允许在线阅读意味着文件内容可被接收者保存；下载开关仅控制下载入口。</small>
            <p>选择具体说明书（未选文件仍保持私有）：</p>
            {!documents.length && <small>当前没有说明书，可单独授权未来新增文件。</small>}
            {documents.map(d => <label key={d.id} style={{ display: "block", overflowWrap: "anywhere" }}><input type="checkbox" checked={manualDocumentIds.includes(d.id)} onChange={e => setManualDocumentIds(ids => e.target.checked ? [...ids, d.id] : ids.filter(id => id !== d.id))} /> {d.originalFilename || d.filename}</label>)}
            <label style={{ display: "block" }}><input type="checkbox" checked={options.showManualDownloads} onChange={e => setOptions({ ...options, showManualDownloads: e.target.checked })} />允许下载已授权说明书 PDF</label>
            <label style={{ display: "block" }}><input type="checkbox" checked={options.shareFutureManuals} onChange={e => setOptions({ ...options, shareFutureManuals: e.target.checked })} />持续授权：以后新增或替换上传的说明书也自动共享</label>
            <small>持续授权不会公开当前未勾选的文件；未开启时，新上传或替换文件必须重新选择并生成二维码。</small>
          </div>}
        </fieldset>
      </>
      {network && !network.reachable ? (
        <>
          <p>当前未检测到可用分享网络，请连接 Wi-Fi 后重新检测。</p>
          {network.mode === "local" && <p>开发预览仅供本机使用，请从应用的普通启动入口打开。</p>}
        </>
      ) : (
        <>
          {network && network.lanAddresses.length > 1 && (
            <label>
              分享网络地址
              <select
                aria-label="分享网络地址"
                disabled={busy}
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
              disabled={!network?.reachable || busy}
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
            仅可查看。同一可互通局域网、主机服务开启时可访问；IP
            改变后需要重新下载二维码。如手机无法访问，请确认 Windows 防火墙允许 Python
            在“私人网络”通信，并检查访客网络隔离。
          </small>
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
