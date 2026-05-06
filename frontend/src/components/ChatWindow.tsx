import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { MessageBubble } from "./MessageBubble";
import { SourceDrawer } from "./SourceDrawer";
import { useWebSocket } from "../hooks/useWebSocket";
import type { ChatMessage, SourceDocument } from "../types";

const HISTORY_KEY = "support-chat-history";
const SESSION_KEY = "support-chat-session";

function newId() {
  return crypto.randomUUID();
}

function loadHistory(): ChatMessage[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]") as ChatMessage[];
  } catch {
    return [];
  }
}

function getSessionId() {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) {
    return existing;
  }
  const sessionId = newId();
  localStorage.setItem(SESSION_KEY, sessionId);
  return sessionId;
}

export function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>(loadHistory);
  const [draft, setDraft] = useState("");
  const [activeSourceMessage, setActiveSourceMessage] = useState<ChatMessage | null>(null);
  const assistantIdRef = useRef<string | null>(null);
  const sessionId = useMemo(getSessionId, []);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
  }, [messages]);

  const appendAssistantToken = useCallback((token: string) => {
    setMessages((current) =>
      current.map((message) =>
        message.id === assistantIdRef.current
          ? { ...message, content: message.content + token, pending: true }
          : message,
      ),
    );
  }, []);

  const attachSources = useCallback((sources: SourceDocument[]) => {
    setMessages((current) =>
      current.map((message) =>
        message.id === assistantIdRef.current ? { ...message, sources } : message,
      ),
    );
  }, []);

  const finishAssistant = useCallback(() => {
    setMessages((current) =>
      current.map((message) =>
        message.id === assistantIdRef.current ? { ...message, pending: false } : message,
      ),
    );
    assistantIdRef.current = null;
  }, []);

  const showError = useCallback((message: string) => {
    setMessages((current) => [
      ...current,
      { id: newId(), role: "assistant", content: message, pending: false },
    ]);
  }, []);

  const socketOptions = useMemo(
    () => ({
      onToken: appendAssistantToken,
      onSources: attachSources,
      onDone: finishAssistant,
      onError: showError,
    }),
    [appendAssistantToken, attachSources, finishAssistant, showError],
  );

  const { connected, sendQuery } = useWebSocket(socketOptions);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const message = draft.trim();
    if (!message) {
      return;
    }

    const assistantId = newId();
    assistantIdRef.current = assistantId;
    setMessages((current) => [
      ...current,
      { id: newId(), role: "user", content: message },
      { id: assistantId, role: "assistant", content: "", pending: true },
    ]);
    setDraft("");

    if (!sendQuery(sessionId, message)) {
      finishAssistant();
    }
  };

  return (
    <main className="chat-shell">
      <section className="chat-panel">
        <header className="chat-header">
          <div>
            <p className="eyebrow">AI Support</p>
            <h1>Customer Support Chatbot</h1>
          </div>
          <span className={`status ${connected ? "status-online" : "status-offline"}`}>
            {connected ? "Live" : "Reconnecting"}
          </span>
        </header>

        <div className="message-list">
          {messages.length === 0 ? (
            <div className="empty-state">
              Ask about product specs, returns, billing, order status, or troubleshooting.
            </div>
          ) : null}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} onShowSources={setActiveSourceMessage} />
          ))}
        </div>

        <form className="composer" onSubmit={submit}>
          <input
            aria-label="Support message"
            placeholder="How can we help?"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <button type="submit">Send</button>
        </form>
      </section>
      <SourceDrawer message={activeSourceMessage} onClose={() => setActiveSourceMessage(null)} />
    </main>
  );
}
