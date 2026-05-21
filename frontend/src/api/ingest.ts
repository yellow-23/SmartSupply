import api from "./axios.instance";

export interface IngestRecord {
  date: string;
  family: string;
  sales: number;
  onpromotion: number;
}

export interface IngestPreview {
  store_name: string;
  records_found: number;
  date_range_start: string | null;
  date_range_end: string | null;
  families_detected: string[];
  records: IngestRecord[];
  warnings: string[];
}

export interface IngestResponse {
  store_nbr: number;
  records_loaded: number;
  families: string[];
  date_range_start: string;
  date_range_end: string;
}

export async function previewIngest(file: File): Promise<IngestPreview> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/ingest/preview", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function confirmIngest(
  records: IngestRecord[],
  store_nbr: number,
  business_id: number
): Promise<IngestResponse> {
  const { data } = await api.post("/ingest/confirm", { records, store_nbr, business_id });
  return data;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  trigger_confirm: boolean;
}

export async function chatIngest(
  messages: ChatMessage[],
  previewSummary: string
): Promise<ChatResponse> {
  const { data } = await api.post("/ingest/chat", {
    messages,
    preview_summary: previewSummary,
  });
  return data;
}
