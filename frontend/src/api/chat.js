import { request } from "./client";

export function askQuestion({ question, topK = 4, documentIds = [], chatId = null }) {
  const json = { question, top_k: topK };
  if (documentIds.length > 0) json.document_ids = documentIds;
  if (chatId !== null) json.chat_id = chatId;
  return request("/chat/ask", { method: "POST", json });
}