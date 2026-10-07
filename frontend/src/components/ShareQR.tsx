import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { api } from "../api";
type Network = {
  mode: string;
  reachable: boolean;
  recommendedBaseUrl: string;
  lanAddresses: string[];
};
export default function ShareQR({ itemId }: { itemId: string }) {
  const [network, setNetwork] = useState<Network>();
  const [address, setAddress] = useState("");
  const [url, setUrl] = useState("");
  const [qr, setQR] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const create = async (regenerate = false) => {
    setBusy(true);
    setError("");
    try {
      const link = await api<{ url: string }>(
        `/items/${itemId}/share?regenerate=${regenerate}&address=${encodeURIComponent(address)}`,
        {
          method: "POST",
        },
      );
      setUrl(link.url);
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
            改变后需要重新下载二维码。如手机无法访问，请允许 Python/物生通过当前私人网络防火墙。
          </small>
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
