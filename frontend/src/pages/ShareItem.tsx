import { useEffect, useState } from "react";
import { api } from "../api";
type Shared = {
  item: Record<string, string>;
  events: { date: string; title: string }[];
  consumables: { name: string; status: string }[];
  manuals: { name: string }[];
};
export default function ShareItem() {
  const token = location.pathname.split("/").pop();
  const [data, setData] = useState<Shared | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Shared>(`/share-data/${token}`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [token]);
  return (
    <main className="share-page">
      <header>
        <img src="/assets/branding/wusheng-eco-ring-logo.png" alt="物生" width="36" /> 物生 Wusheng{" "}
        <small>只读物品档案</small>
      </header>
      {error ? (
        <p role="alert">{error}</p>
      ) : !data ? (
        <p>正在读取档案…</p>
      ) : (
        <>
          <img className="share-cover" src={data.item.coverImage} alt={data.item.name} />
          <h1>{data.item.name}</h1>
          <dl className="detail-facts">
            {Object.entries({
              品牌: data.item.brand,
              型号: data.item.model,
              购买日期: data.item.purchaseDate,
              保修截止: data.item.warrantyEndDate,
              当前状态: data.item.status,
              下一次维护: data.item.nextMaintenance,
              序列号: data.item.serialNumber,
            }).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value || "未记录"}</dd>
              </div>
            ))}
          </dl>
          <h2>耗材状态</h2>
          {data.consumables.map((c) => (
            <p key={c.name}>
              {c.name} · {c.status}
            </p>
          ))}
          <h2>生命周期</h2>
          {data.events.map((e, i) => (
            <p key={i}>
              {e.date} · {e.title}
            </p>
          ))}
          <h2>说明书</h2>
          {data.manuals.map((m, i) => (
            <p key={i}>{m.name}</p>
          ))}
          <p className="muted">本页面只可查看；服务关闭或分享撤销后不可访问。</p>
        </>
      )}
    </main>
  );
}
