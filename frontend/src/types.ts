export type SourceDocument = {
  source: string;
  title?: string;
  snippet: string;
  score?: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  pending?: boolean;
};

export type WebSocketEvent =
  | { type: "token"; data: string }
  | { type: "sources"; data: SourceDocument[] }
  | { type: "done"; metadata: Record<string, unknown> }
  | { type: "error"; message: string };
