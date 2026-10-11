import { API_BASE } from "../config";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// The access token lives only in memory, never in localStorage.
let accessToken = null;
let onSessionExpired = () => {};
let refreshPromise = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler;
}

function detailToMessage(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((item) => item.msg).join(". ");
  }
  return `Request failed (${status})`;
}

async function send(path, { method, json, form, formData, withAuth }) {
  const headers = {};
  let body;

  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form) {
    body = new URLSearchParams(form);
  } else if (formData) {
    body = formData; // the browser sets the multipart boundary itself
  }
  if (withAuth && accessToken) headers.Authorization = `Bearer ${accessToken}`;

  try {
    return await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body,
      // Only the auth endpoints use the refresh cookie.
      credentials: path.startsWith("/auth/") ? "include" : "same-origin",
    });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check that the backend is running.");
  }
}

// One refresh at a time: simultaneous callers share the same request.
export function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const response = await send("/auth/refresh", { method: "POST", withAuth: false });
      if (!response.ok) {
        throw new ApiError(response.status, "Your session has expired. Please sign in again.");
      }
      const data = await response.json();
      accessToken = data.access_token;
      return accessToken;
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

// auth: true (default) sends the current access token and, on a 401, refreshes
// it once and retries. Use auth: false for login, register, refresh and logout.
export async function request(path, { method = "GET", json, form, formData, auth = true } = {}) {
  const options = { method, json, form, formData, withAuth: auth };
  let response = await send(path, options);

  if (response.status === 401 && auth) {
    try {
      await refreshSession();
    } catch (error) {
      if (error.status === 401) onSessionExpired();
      throw error;
    }
    response = await send(path, options);
    if (response.status === 401) onSessionExpired();
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON response: fall through to the generic message.
  }

  if (!response.ok) {
    throw new ApiError(response.status, detailToMessage(data?.detail, response.status));
  }
  return data;
}