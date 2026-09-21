import { apiGet, apiPost } from "./api.js";

// Backend teammate: configure these after agreeing the authentication/session contract.
// Keep paths empty until the contract is provided; no endpoint is assumed by the frontend.
export const AUTH_ENDPOINTS = {
  login: "",
  register: "",
  logout: "",
  currentUser: "",
};

function requireEndpoint(name) {
  const endpoint = AUTH_ENDPOINTS[name];
  if (!endpoint) throw new Error(`AUTH_ENDPOINTS.${name} has not been configured.`);
  return endpoint;
}

export async function login(credentials) {
  // TODO: Connect this payload to the agreed backend login contract.
  return apiPost(requireEndpoint("login"), JSON.stringify(credentials), { headers: { "Content-Type": "application/json" } });
}

export async function register(account) {
  // TODO: Connect this payload to the agreed backend registration contract.
  return apiPost(requireEndpoint("register"), JSON.stringify(account), { headers: { "Content-Type": "application/json" } });
}

export async function logout() {
  // TODO: Connect to the agreed backend logout contract.
  return apiPost(requireEndpoint("logout"));
}

export async function getCurrentUser() {
  // Expected session response may be { user: {...} } or the user object directly.
  // Update this adapter only if the agreed backend response uses a different envelope.
  const response = await apiGet(requireEndpoint("currentUser"));
  const user = response?.user ?? response?.currentUser ?? response;
  // Supports a nested statistics object or statistics returned directly on the user.
  const statistics = user?.statistics ?? user?.stats ?? response?.statistics ?? response?.stats ?? user ?? {};

  return {
    firstName: user?.firstName ?? user?.first_name ?? "",
    lastName: user?.lastName ?? user?.last_name ?? "",
    name: user?.name ?? "",
    email: user?.email ?? "",
    phone: user?.phone ?? user?.phoneNumber ?? user?.phone_number ?? "",
    avatarUrl: user?.avatarUrl ?? user?.avatar_url ?? user?.avatar ?? "",
    statistics,
  };
}
