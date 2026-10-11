import { request } from "./client";

export function register(email, password) {
  return request("/auth/register", {
    method: "POST",
    json: { email, password },
    auth: false,
  });
}

export function login(email, password) {
  // The backend expects OAuth2 form data: the email goes in the "username" field.
  return request("/auth/login", {
    method: "POST",
    form: { username: email, password },
    auth: false,
  });
}

export function logout() {
  return request("/auth/logout", { method: "POST", auth: false });
}

export function getMe() {
  return request("/auth/me");
}