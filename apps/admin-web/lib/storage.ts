export const STORAGE_KEYS = {
  token: "sf_token",
  user: "sf_user"
};

export function saveToken(token: string) {
  localStorage.setItem(STORAGE_KEYS.token, token);
}

export function loadToken(): string | null {
  return localStorage.getItem(STORAGE_KEYS.token);
}

export function clearToken() {
  localStorage.removeItem(STORAGE_KEYS.token);
}

export function saveUser(user: unknown) {
  localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user));
}

export function loadUser<T>(): T | null {
  const raw = localStorage.getItem(STORAGE_KEYS.user);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function clearUser() {
  localStorage.removeItem(STORAGE_KEYS.user);
}
