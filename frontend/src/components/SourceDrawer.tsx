import type { ChatMessage } from "../types";

type SourceDrawerProps = {
  message: ChatMessage | null;
  onClose: () => void;
};

export function SourceDrawer({ message, onClose }: SourceDrawerProps) {
  return (
    <aside className={`source-drawer ${message ? "source-drawer-open" : ""}`} aria-live="polite">
      <div className="drawer-header">
        <h2>Retrieved sources</h2>
        <button type="button" onClick={onClose} aria-label="Close sources">
          x
        </button>
      </div>
      {message?.sources?.map((source) => (
        <section className="source-card" key={`${source.source}-${source.snippet}`}>
          <h3>{source.title ?? source.source}</h3>
          <p>{source.snippet}</p>
          <small>
            {source.source}
            {typeof source.score === "number" ? ` - score ${source.score.toFixed(3)}` : ""}
          </small>
        </section>
      ))}
    </aside>
  );
}
