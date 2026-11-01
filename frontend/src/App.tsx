import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: string[];
  cached?: boolean;
}

const API_URL = "";

const HISTORY_STORAGE_KEY = "rustsensei_history";

const MAX_HISTORY_MESSAGES = 6;

// Ecrans tactiles : Entree insere un saut de ligne, l'envoi passe par le bouton.
const isCoarsePointer = (): boolean =>
  typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;

function loadPersistedHistory(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    const valid: ChatMessage[] = parsed
      .filter(
        (m) =>
          m &&
          (m.role === "user" || m.role === "assistant") &&
          typeof m.content === "string" &&
          m.content.trim().length > 0,
      )
      .map((m) => {
        const message: ChatMessage = { role: m.role, content: m.content };
        if (Array.isArray(m.citations)) {
          message.citations = m.citations.filter(
            (c: unknown): c is string => typeof c === "string",
          );
        }
        if (m.cached === true) {
          message.cached = true;
        }
        return message;
      });
    return valid.slice(-MAX_HISTORY_MESSAGES);
  } catch {
    return [];
  }
}

function splitCitation(citation: string): { label: string; url?: string } {
  const match = citation.match(/^\[([^\]]+)\]\((.+)\)$/);
  if (!match) {
    return { label: citation };
  }
  return { label: match[1], url: match[2] };
}

function readCitations(res: Response): string[] {
  const encoded = res.headers.get("X-Citations");
  if (!encoded) {
    return [];
  }
  try {
    const binary = atob(encoded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    const parsed = JSON.parse(new TextDecoder().decode(bytes));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function App() {
  const [messages, setMessages] = useState<ChatMessage[]>(loadPersistedHistory);
  const [input, setInput] = useState("");
  const [useRag, setUseRag] = useState(false);
  const [sending, setSending] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Hauteur auto de la zone de saisie (plafonnee par max-h, puis defilement).
  useEffect(() => {
    const el = inputRef.current;
    if (!el) {
      return;
    }
    el.style.height = "auto";
    if (input) {
      el.style.height = `${el.scrollHeight}px`;
    }
  }, [input]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending, streaming]);

  useEffect(() => {
    if (sending || streaming) {
      return;
    }
    const turns = messages
      .filter((m) => m.content.trim().length > 0)
      .slice(-MAX_HISTORY_MESSAGES);
    // Sources et badge cache sont conserves pour l'affichage apres rechargement
    // (seuls role et content sont envoyes au backend comme historique).
    try {
      localStorage.setItem(
        HISTORY_STORAGE_KEY,
        JSON.stringify(
          turns.map(({ role, content, citations, cached }) => ({
            role,
            content,
            ...(citations?.length ? { citations } : {}),
            ...(cached ? { cached } : {}),
          })),
        ),
      );
    } catch {
      // Stockage indisponible (navigation privee, quota) : historique non persiste.
    }
  }, [messages, sending, streaming]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) {
      return;
    }
    const history = messages
      .filter((m) => m.content.trim().length > 0)
      .slice(-6)
      .map((m) => ({ role: m.role, content: m.content }));
    setInput("");
    setError(null);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]);
    setSending(true);
    setStreaming(true);

    try {
      const res = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, use_rag: useRag, history }),
      });
      if (!res.ok) {
        let detail = "";
        try {
          const body = await res.json();
          if (typeof body?.detail === "string") {
            detail = ` : ${body.detail}`;
          }
        } catch {
          // corps non JSON : on garde le seul code HTTP
        }
        setError(`Le backend a répondu une erreur (${res.status})${detail}.`);
        return;
      }
      const citations = readCitations(res);
      const cached = res.headers.get("X-Cache") === "HIT";
      if (citations.length > 0 || cached) {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last?.role === "assistant") {
            next[next.length - 1] = { ...last, citations, cached };
          }
          return next;
        });
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let streamText = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        streamText += decoder.decode(value, { stream: true });
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last?.role === "assistant") {
            next[next.length - 1] = { ...last, content: streamText };
          }
          return next;
        });
      }
      streamText += decoder.decode();
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last?.role === "assistant") {
          next[next.length - 1] = { ...last, content: streamText };
        }
        return next;
      });
    } catch {
      setError("Impossible de joindre le backend RustSensei. Lancez `make api`.");
    } finally {
      // En cas d'erreur, retirer la bulle assistant restee vide.
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        return last?.role === "assistant" && last.content === "" ? prev.slice(0, -1) : prev;
      });
      setSending(false);
      setStreaming(false);
    }
  };

  const lastMessage = messages[messages.length - 1];
  const showThinking =
    sending && (!lastMessage || lastMessage.role === "user" || lastMessage.content === "");

  const clearChat = () => {
    setMessages([]);
    try {
      localStorage.removeItem(HISTORY_STORAGE_KEY);
    } catch {
      // Stockage indisponible : rien a effacer.
    }
    setError(null);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#020603] font-mono text-green-400">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-2 p-2">
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-green-400/20 pb-2">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-green-400">RustSensei</h1>
          <div className="flex flex-wrap items-center gap-2">
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
              className={`min-w-0 rounded-2xl px-4 py-3 ${
                m.role === "user"
                  ? "max-w-[85%] self-end rounded-br-md border bg-green-400/10 text-green-300"
                  : "w-full self-start rounded-bl-md border-green-400/30 bg-transparent text-green-400"
              }`}
            >
              {m.role === "assistant" ? (
                <div className="rust-response text-base leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                    {m.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap text-base [overflow-wrap:anywhere]">{m.content}</p>
              )}
              {m.role === "assistant" && m.cached ? (
                <div className="mb-1 text-xs text-green-500/70">
                  <span className="rounded-full border border-green-400/30 px-2 py-0.5">
                    réponse servie depuis le cache
                  </span>
                </div>
              ) : null}
              {m.citations && m.citations.length > 0 ? (
                <div className="mt-2 text-xs text-green-500/70">
                  Sources :{" "}
                  {m.citations.map((citation, index) => {
                    const { label, url } = splitCitation(citation);
                    return (
                      <span key={citation}>
                        {index > 0 ? ", " : ""}
                        {url ? (
                          <a
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="underline decoration-green-500/40 underline-offset-2 hover:text-green-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-400/60"
                          >
                            {label}
                          </a>
                        ) : (
                          label
                        )}
                      </span>
                    );
                  })}
                </div>
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
          className="flex items-end gap-2 pt-2"
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              // Entree envoie, Maj+Entree insere un retour a la ligne.
              if (
                e.key === "Enter" &&
                !e.shiftKey &&
                !e.nativeEvent.isComposing &&
                !isCoarsePointer()
              ) {
                e.preventDefault();
                void send();
              }
            }}
            placeholder="Votre question Rust…"
            className="max-h-[40vh] min-w-0 flex-1 resize-none overflow-y-auto rounded-xl border border-green-400/30 bg-transparent px-4 py-2.5 font-mono text-base text-green-300 placeholder-green-500/50 focus:outline-none focus:ring-2 focus:ring-green-400/50"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-xl bg-green-400 px-4 py-2.5 font-mono text-base font-medium text-black disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-400/60"
          >
            Envoyer
          </button>
        </form>
        <p className="hidden text-xs text-green-500/60 pointer-fine:block">
          Entrée pour envoyer · Maj+Entrée pour un saut de ligne (code multi-ligne)
        </p>
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
      </div>
    </div>
  );
}
