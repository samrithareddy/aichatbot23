import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../types";

type MessageBubbleProps = {
  message: ChatMessage;
  onShowSources: (message: ChatMessage) => void;
};

export function MessageBubble({ message, onShowSources }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <article className={`message ${isUser ? "message-user" : "message-assistant"}`}>
      <div className="message-meta">{isUser ? "You" : "Support AI"}</div>
      <div className="message-content">
        {isUser ? message.content : <ReactMarkdown>{message.content || "..."}</ReactMarkdown>}
      </div>
      {!isUser && message.pending ? <span className="typing">Streaming response...</span> : null}
      {!isUser && message.sources?.length ? (
        <button className="link-button" type="button" onClick={() => onShowSources(message)}>
          View {message.sources.length} source{message.sources.length === 1 ? "" : "s"}
        </button>
      ) : null}
    </article>
  );
}
