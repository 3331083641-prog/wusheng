import { useEffect, useRef, useState } from "react";
import { Leaf, Send, Sparkles } from "lucide-react";
import { api, json } from "../api";
interface Answer {
  answer: string;
  sources: { type: string; title: string; quote?: string }[];
  mode: string;
}
export default function AIChat({ itemId, suggested }: { itemId: string; suggested: string }) {
  const [messages, setMessages] = useState<
    { role: string; text: string; sources?: Answer["sources"] }[]
  >([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("本地档案规则");
  useEffect(() => {
    api<{ mode: string }>("/health")
      .then((h) => setMode(h.mode))
      .catch(() => setMode("本地档案规则"));
  }, []);
  const bottom = useRef<HTMLDivElement>(null);
  const active = useRef(itemId);
  useEffect(() => {
    active.current = itemId;
    setMessages([]);
    setError("");
    setInput("");
  }, [itemId]);
  useEffect(() => {
    if (suggested) setInput(suggested);
  }, [suggested]);
  useEffect(() => {
    bottom.current?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
      block: "nearest",
    });
  }, [messages, busy]);
  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || busy) return;
    const question = input.trim(),
      selected = itemId;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    setError("");
    try {
      const answer = await api<Answer>("/generate", json("POST", { itemId: selected, question }));
      setMode(answer.mode);
      if (active.current === selected)
        setMessages((m) => [
          ...m,
          { role: "assistant", text: answer.answer, sources: answer.sources },
        ]);
    } catch (e) {
      if (active.current === selected) setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="chat panel">
      <div className="chat-mode">
        <span className="live-dot" />
        {mode} · 本地档案优先
      </div>
      <div className="chat-messages" aria-live="polite">
        {!messages.length && (
          <div className="chat-welcome">
            <span className="icon-well green">
              <Leaf size={31} />
            </span>
            <h2>
              先了解这件物品，
              <br />
              再回答你的问题。
            </h2>
            <p>保修、维护、维修与耗材信息来自当前档案。说明书有可读文本时，会给出引用。</p>
            <small>没有找到依据时，会明确告诉你。</small>
          </div>
        )}
        {messages.map((m, i) => (
          <div className={`chat-message ${m.role}`} key={`${itemId}-${i}`}>
            <span className="chat-role">{m.role === "assistant" ? <Leaf size={19} /> : "你"}</span>
            <div>
              <p>{m.text}</p>
              {m.sources?.length ? (
                <div className="answer-sources">
                  {m.sources.map((s, n) => (
                    <details key={n}>
                      <summary>
                        {s.type} · {s.title}
                      </summary>
                      {s.quote && <blockquote>{s.quote}</blockquote>}
                    </details>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ))}
        {busy && (
          <div className="typing">
            <Sparkles size={19} />
            <span />
            <span />
            <span />
            正在查询当前物品记录
          </div>
        )}
        <div ref={bottom} />
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <form className="chat-input" onSubmit={send}>
        <input
          aria-label="向当前物品助手提问"
          placeholder="关于这件物品，你想知道什么？"
          value={input}
          maxLength={1000}
          onChange={(e) => setInput(e.target.value)}
        />
        <button aria-label="发送问题" className="send-button" disabled={busy || !input.trim()}>
          <Send size={20} />
        </button>
      </form>
    </section>
  );
}
