const localApiBase = `${window.location.protocol}//${window.location.hostname}:8001`;

export const API_BASE = (import.meta.env.VITE_API_BASE || localApiBase).replace(
  /\/+$/,
  "",
);

/** Call the configured API with the HttpOnly session cookie attached. */
export function apiFetch(path, options = {}) {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
  });
}
