"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; content: string };
type Me = {
  name: string;
  email: string;
  private: boolean;
  simulated: boolean;
  visibility: string;
};

const STORAGE_KEY = "mirror.chat.v1";

export default function MirrorPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("What feels most present right now?");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<"live" | "local" | null>(null);
  const [installReady, setInstallReady] = useState(false);
  const deferredPrompt = useRef<{ prompt: () => Promise<void> } | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Msg[];
        if (Array.isArray(parsed)) setMessages(parsed.slice(-40));
      }
    } catch {
      /* ignore */
    }

    void (async () => {
      try {
        const [meRes, promptRes] = await Promise.all([
          fetch("/api/me", { cache: "no-store" }),
          fetch("/api/prompts", { cache: "no-store" }),
        ]);
        if (!meRes.ok) {
          setAuthError("Private access only. Sign in with your Cursor account.");
          return;
        }
        const meJson = (await meRes.json()) as Me;
        setMe(meJson);
        if (promptRes.ok) {
          const p = (await promptRes.json()) as { prompt?: string };
          if (p.prompt) setPrompt(p.prompt);
        }
      } catch {
        setAuthError("Could not reach Mirror.");
      }
    })();

    if ("serviceWorker" in navigator) {
      void navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    }

    const onBip = (event: Event) => {
      event.preventDefault();
      deferredPrompt.current = event as unknown as { prompt: () => Promise<void> };
      setInstallReady(true);
    };
    window.addEventListener("beforeinstallprompt", onBip);
    return () => window.removeEventListener("beforeinstallprompt", onBip);
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-40)));
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  async function send(text: string) {
    const content = text.trim();
    if (!content || busy) return;
    const next = [...messages, { role: "user" as const, content }];
    setMessages(next);
    setDraft("");
    setBusy(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ messages: next }),
      });
      if (res.status === 401 || res.status === 403) {
        setAuthError("Private access denied.");
        return;
      }
      if (!res.ok) throw new Error("chat_failed");
      const data = (await res.json()) as { reply: string; mode: "live" | "local" };
      setMode(data.mode);
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: "Mirror could not answer just now. Try again in a moment.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void send(draft);
  }

  async function install() {
    if (!deferredPrompt.current) return;
    await deferredPrompt.current.prompt();
    deferredPrompt.current = null;
    setInstallReady(false);
  }

  return (
    <main className="app-shell">
      <header className="brand-bar">
        <div>
          <h1 className="brand">Mirror</h1>
          <p className="hero-line">A private AI companion that reflects you back.</p>
        </div>
        <div className="brand-meta">
          <div>{me?.name || "…"}</div>
          <div className="lock-pill">Private · you only</div>
        </div>
      </header>

      <section className="stage">
        <div className="prompt-strip">
          <p>{prompt}</p>
          <span>Today’s reflection</span>
        </div>

        <div className="thread" aria-live="polite">
          {authError ? (
            <div className="empty">
              <strong>Locked</strong>
              {authError}
            </div>
          ) : messages.length === 0 ? (
            <div className="empty">
              <strong>Begin with one true sentence</strong>
              Mirror keeps this space private — no public listing, no sign-up for others.
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={`${m.role}-${i}`} className={`bubble ${m.role}`}>
                <span className="who">{m.role === "user" ? "You" : "Mirror"}</span>
                {m.content}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </section>

      <form className="composer" onSubmit={onSubmit}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Write what is on your mind…"
          disabled={!!authError || busy}
          aria-label="Message to Mirror"
        />
        <div className="actions">
          <button
            type="button"
            onClick={() => void send(prompt)}
            disabled={!!authError || busy}
          >
            Use prompt
          </button>
          <button
            type="button"
            onClick={() => {
              setMessages([]);
              localStorage.removeItem(STORAGE_KEY);
            }}
            disabled={busy || messages.length === 0}
          >
            Clear
          </button>
          {installReady ? (
            <button type="button" onClick={() => void install()}>
              Install
            </button>
          ) : null}
          <button className="primary" type="submit" disabled={!!authError || busy || !draft.trim()}>
            {busy ? "Listening…" : "Reflect"}
          </button>
        </div>
        <p className={`status ${mode === "local" ? "" : ""}`}>
          {me?.simulated
            ? "Local preview uses a simulated viewer — live private access activates after you publish as Private."
            : mode === "local"
              ? "Using on-device reflection mode until OPENAI_API_KEY is set for your private app."
              : mode === "live"
                ? "Live AI reflection · private to your account"
                : "Conversations stay on this device. APIs require your Cursor sign-in."}
        </p>
        <p className="install-hint">
          On iPhone: Share → Add to Home Screen. On Android: browser menu → Install app / Add to Home screen.
        </p>
      </form>
    </main>
  );
}
