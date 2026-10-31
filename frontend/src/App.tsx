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
      className={`flex min-h-screen flex-col bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 ${
        dark ? "dark" : ""
      }`}
    >
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-2 p-2">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-xl font-bold tracking-tight sm:text-2xl">RustSensei</h1>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setDark((d) => !d)}
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              {dark ? "Clair" : "Sombre"}
            </button>
            <button
              type="button"
              onClick={() => setUseRag((r) => !r)}
              className={`rounded-lg border px-3 py-1.5 text-sm font-medium ${
                useRag
                  ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                  : "border-zinc-300 text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              }`}
            >
              RAG : {useRag ? "ON" : "OFF"}
            </button>
            <button
              type="button"
              onClick={clearChat}
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Effacer
            </button>
          </div>
        </header>

        <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`rounded-2xl px-4 py-3 ${
                m.role === "user"
                  ? "self-end rounded-br-md bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "self-start rounded-bl-md bg-zinc-100 dark:bg-zinc-800"
              }`}
            >
              {m.role === "assistant" ? (
                <div className="rust-response text-sm leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap text-sm">{m.content}</p>
              )}
              {m.citations && m.citations.length > 0 ? (
                <div className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                  Sources : {m.citations.join(", ")}
                </div>
              ) : null}
            </div>
          ))}
          {showThinking ? (
            <div className="self-start rounded-2xl rounded-bl-md bg-zinc-100 px-4 py-3 text-sm text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
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
            className="min-w-0 flex-1 rounded-xl border border-zinc-300 bg-white px-4 py-2.5 text-sm text-zinc-900 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-xl bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900"
          >
            Envoyer
          </button>
        </form>
        {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}
      </div>
    </div>
  );
}
