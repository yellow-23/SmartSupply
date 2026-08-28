import api from "../../../shared/api/axios.instance";

export interface StockyMessage {
  role: "user" | "assistant";
  content: string;
}

export async function chatStocky(
  messages: StockyMessage[],
  businessId: number
): Promise<string> {
  const { data } = await api.post("/stocky/chat", {
    messages,
    business_id: businessId,
  });
  return data.reply;
}
