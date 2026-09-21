// Configure this value when the backend service is available.
export const API_BASE_URL = "";

async function request(path, options = {}) {
  // TODO: Connect requests to the backend endpoint and add auth handling.
  if (!API_BASE_URL) {
    throw new Error("API_BASE_URL has not been configured.");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

export const apiGet = (path, options) => request(path, options);
export const apiPost = (path, body, options = {}) => request(path, { method: "POST", body, ...options });
export const apiPut = (path, body, options = {}) => request(path, { method: "PUT", body, ...options });
export const apiDelete = (path, options) => request(path, { method: "DELETE", ...options });
