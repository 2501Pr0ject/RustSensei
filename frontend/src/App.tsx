import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: string[];
}

const API_URL = "";

export function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [useRag, setUseRag] = useState(false);
  const [dark, setDark] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) {
      return;
    }
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, use_rag: useRag }),
      });
      const data = (await res.json()) as {
        response: string;
        citations: string[];
        rag_used: boolean;
      };
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response, citations: data.citations },
      ]);
    } catch {
      setError("Impossible de joindre le backend RustSensei. Lancez `make api`.");
    } finally {
      setSending(false);
    }
  };

  const lastMessage = messages[messages.length - 1];
  const showThinking = sending && (!lastMessage || lastMessage.role === "user");

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div
      className={`flex min-h-screen flex-col bg-[#020603] font-mono text-green-400 dark:bg-[#030a06] ${
        dark ? "dark" : ""
      }`}
    >
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-2 p-2">
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-green-400/20 pb-2">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-green-400">RustSensei</h1>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setDark((d) => !d)}
              className="rounded-lg border border-green-400/40 px-3 py-2.5 text-sm font-medium text-green-300 hover:bg-green-400/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-400/60"
            >
              {dark ? "Clair" : "Sombre"}
            </button>
            <button
              type="button"
              onClick={() => setUseRag((r) => !r)}
              aria-pressed={useRag}
              className={`rounded-lg border px-3 py-2.5 text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-400/60 ${
                useRag
                  ? "border-green-400 bg-green-400 text-black"
                  : "border-green-400/40 text-green-300 hover:bg-green-400/10"
              }`}
            >
              RAG : {useRag ? "ON" : "OFF"}
            </button>
            <button
              type="button"
              onClick={clearChat}
              className="rounded-lg border border-green-400/40 px-3 py-2.5 text-sm font-medium text-green-300 hover:bg-green-400/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-400/60"
            >
              Effacer
            </button>
          </div>
        </header>

        <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1" aria-live="polite">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`rounded-2xl px-4 py-3 ${
                m.role === "user"
                  ? "self-end rounded-br-md border bg-green-400/10 text-green-300"
                  : "self-start rounded-bl-md border-green-400/30 bg-transparent text-green-400"
              }`}
            >
              {m.role === "assistant" ? (
                <div className="rust-response text-base leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap text-base">{m.content}</p>
              )}
              {m.citations && m.citations.length > 0 ? (
                <div className="mt-2 text-xs text-green-500/70">Sources : {m.citations.join(", ")}</div>
              ) : null}
            </div>
          ))}
          {showThinking ? (
            <div className="self-start rounded-2xl rounded-bl-sm border border-green-400/30 px-4 py-3 text-green-500">
              <span className="animate-pulse">RustSensei réfléchit...</span>
            </div>
          ) : null}
          <div ref={bottomRef} />
        </div>

        <form
          className="flex gap-2 pt-2"
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question sur Rust..."
            className="min-w-0 flex-1 rounded-xl border border-green-400/30 bg-transparent px-4 py-2.5 font-mono text-base text-green-300 placeholder-green-500/50 focus:outline-none focus:ring-2 focus:ring-green-400/50"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-xl bg-green-400 px-4 py-2.5 font-mono text-base font-medium text-black disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-400/60"
          >
            Envoyer
          </button>
        </form>
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
      </div>
    </div>
  );
}
