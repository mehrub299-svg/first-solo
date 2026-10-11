import { request } from "./client";

export function listDocuments() {
  return request("/documents");
}

export function createDocument(title, text) {
  return request("/documents", { method: "POST", json: { title, text } });
}

export function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/documents/upload", { method: "POST", formData });
}

export function deleteDocument(id) {
  return request(`/documents/${id}`, { method: "DELETE" });
}