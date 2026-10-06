import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BookOpen, Box, Calendar, ShieldCheck, Sparkles, Wrench } from "lucide-react";
import { PageHeader, StatusBadge } from "../components/ui";
import AIChat from "../components/AIChat";
import { useStore } from "../store";
import ProductImage from "../components/ProductImage";
export default function Assistant() {
  const data = useStore((s) => s.data)!;
  const [params, setParams] = useSearchParams();
  const selected = params.get("item") || "headphones";
  const item = data.items.find((i) => i.id === selected) || data.items[0];
  const [question, setQuestion] = useState("");
  if (!item)
    return (
      <main className="page">
        <PageHeader title="AI 助手" description="先添加一件物品，即可使用档案问答。" />
        <Link to="/items/new">添加物品</Link>
      </main>
    );
  return (
    <main className="page">
      <PageHeader
        title="AI 助手"
        description="基于当前物品的专属档案，解答使用、维护、保修、耗材与维修问题。"
      />
      <div className="assistant-questions">
        {[
          ["这台设备还在保修吗？", ShieldCheck],
          ["多久需要清洁一次？", Wrench],
          ["查看说明书", BookOpen],
          ["什么时候需要换耗材？", Box],
          ["之前维修过什么？", Sparkles],
        ].map(([q, Icon]) => {
          const I = Icon as typeof Box;
          return (
            <button key={String(q)} onClick={() => setQuestion(String(q))}>
              <I size={19} />
              {String(q)}
            </button>
          );
        })}
      </div>
      <div className="assistant-layout">
        <AIChat itemId={item.id} suggested={question} />
        <aside className="panel current-item">
          <header>
            <h3>当前物品</h3>
            <StatusBadge>本地档案</StatusBadge>
          </header>
          <select
            aria-label="选择当前物品"
            value={item.id}
            onChange={(e) => {
              setParams({ item: e.target.value });
              setQuestion("");
            }}
          >
            {data.items.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </select>
          <Link className="context-item" to={`/items/${item.id}`}>
            <ProductImage item={item} priority />
            <h3>{item.name}</h3>
            <p>{item.model}</p>
          </Link>
          <dl className="drawer-facts">
            {[
              ["购买时间", item.purchaseDate],
              ["保修到期", item.warrantyEndDate || "未记录"],
              ["购买渠道", item.purchaseChannel],
              ["产品序列号", item.serialNumber],
              ["分类", item.category],
              ["存放位置", item.location],
            ].map(([key, val]) => (
              <div key={key}>
                <dt>
                  <Calendar size={14} />
                  {key}
                </dt>
                <dd>{val || "未记录"}</dd>
              </div>
            ))}
          </dl>
          <h3>快捷操作</h3>
          <Link className="context-action" to={`/items/${item.id}`}>
            <BookOpen size={20} />
            查看说明书与档案 →
          </Link>
          <Link className="context-action" to="/reminders">
            <ShieldCheck size={20} />
            查看保修与维护提醒 →
          </Link>
          <Link className="context-action" to="/consumables">
            <Box size={20} />
            查看设备关联耗材 →
          </Link>
          <p className="data-footnote">
            未配置生成模型时，使用可验证的规则回答。图片不会被自动发送到在线服务。
          </p>
        </aside>
      </div>
    </main>
  );
}
