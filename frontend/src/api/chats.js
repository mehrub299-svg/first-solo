import { request } from "./client";

export function listChats() {
  return request("/chats");
}

export function listMessages(chatId) {
  return request(`/chats/${chatId}/messages`);
}

export function deleteChat(chatId) {
  return request(`/chats/${chatId}`, { method: "DELETE" });
}