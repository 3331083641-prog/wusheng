import type { ProviderHealth } from "../types";
export default function ProviderStatus({ health, error, retry }: { health?: ProviderHealth; error: boolean; retry: () => void }) {
  if (error) return <div className="provider-status"><span>暂时无法读取智能状态</span><button onClick={retry}>重新检测</button></div>;
  if (!health) return <div className="provider-status" role="status">正在检测本地智能状态…</div>;
  const fallback = health.activeProvider === "evidence" && !!health.fallbackReason;
  const localModel = health.activeProvider !== "evidence";
  return <div className={`provider-status ${fallback ? "provider-fallback" : ""}`} role="status">
    <div><b>{fallback ? "○ 本地模型未连接" : localModel ? `● 本地模型${health.model ? " · " + health.model : ""}` : "● 本地档案智能"}</b><small>{fallback ? "已自动切换至本地档案智能" : localModel ? `${health.activeProvider === "ollama" ? "Ollama" : "本机模型服务"} 已连接 · 数据不离开本机` : "无需大模型 · 数据不离开本机"}</small></div>
    {fallback && <details><summary>查看原因</summary><p>{health.fallbackReason}</p></details>}
  </div>;
}
