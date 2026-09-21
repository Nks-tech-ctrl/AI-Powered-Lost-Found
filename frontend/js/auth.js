import { apiPost } from "./api.js";

export async function login(credentials) {
  // TODO: Connect to the backend authentication endpoint.
  return apiPost("/auth/login", JSON.stringify(credentials), { headers: { "Content-Type": "application/json" } });
}

export async function register(account) {
  // TODO: Connect to the backend registration endpoint.
  return apiPost("/auth/register", JSON.stringify(account), { headers: { "Content-Type": "application/json" } });
}

export async function logout() {
  // TODO: Connect to the backend logout endpoint.
}
