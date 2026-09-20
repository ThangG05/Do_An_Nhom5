export interface AuthUser {
  id: string;
  email: string;
  username: string;
  full_name: string;
  avatar_url: string | null;
  is_new_user: boolean;
  system_role: 'USER' | 'SUPER_ADMIN';
  admin_group_slugs: string[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: AuthUser;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function readApiError(response: Response, fallback: string): Promise<Error> {
  const payload = (await response.json().catch(() => null)) as
    | { detail?: string | Array<{ msg?: string }> }
    | null;
  const detail = payload?.detail;
  if (typeof detail === 'string') return new Error(detail);
  if (Array.isArray(detail) && detail[0]?.msg) return new Error(detail[0].msg);
  return new Error(fallback);
}

export async function authenticateWithGoogle(
  credential: string,
): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE_URL}/auth/google`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  });

  if (!response.ok) {
    throw await readApiError(response, 'Không thể đăng nhập bằng Google.');
  }

  return response.json() as Promise<AuthTokens>;
}

export async function requestRegistrationCode(email: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/register/request-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    throw await readApiError(response, 'Không thể gửi mã xác thực.');
  }
}

export async function verifyRegistrationCode(
  email: string,
  code: string,
): Promise<{ registration_token: string; expires_in: number }> {
  const response = await fetch(`${API_BASE_URL}/auth/register/verify-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  });
  if (!response.ok) {
    throw await readApiError(response, 'Mã xác thực không hợp lệ.');
  }
  return response.json() as Promise<{
    registration_token: string;
    expires_in: number;
  }>;
}

export async function completeRegistration(
  registrationToken: string,
  password: string,
): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE_URL}/auth/register/complete`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ registration_token: registrationToken, password }),
  });
  if (!response.ok) {
    throw await readApiError(response, 'Không thể hoàn tất đăng ký.');
  }
  return response.json() as Promise<AuthTokens>;
}

export async function loginWithPassword(
  email: string,
  password: string,
): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw await readApiError(response, 'Email hoặc mật khẩu không đúng.');
  }
  return response.json() as Promise<AuthTokens>;
}

export function saveAuthSession(tokens: AuthTokens): void {
  window.sessionStorage.setItem('hvnh-hub-access-token', tokens.access_token);
  window.sessionStorage.removeItem('hvnh-hub-refresh-token');
  window.sessionStorage.setItem('hvnh-hub-user', JSON.stringify(tokens.user));
}

export function getAuthUser(): AuthUser | null {
  const rawUser = window.sessionStorage.getItem('hvnh-hub-user');
  if (!rawUser) return null;

  try {
    return JSON.parse(rawUser) as AuthUser;
  } catch {
    return null;
  }
}

export function updateStoredAvatar(avatarUrl: string): void {
  const user = getAuthUser();
  if (user) window.sessionStorage.setItem('hvnh-hub-user', JSON.stringify({ ...user, avatar_url: avatarUrl }));
}

export function updateStoredFullName(fullName: string): void {
  const user = getAuthUser();
  if (user) window.sessionStorage.setItem('hvnh-hub-user', JSON.stringify({ ...user, full_name: fullName }));
}

export function clearAuthSession(): void {
  window.sessionStorage.removeItem('hvnh-hub-access-token');
  window.sessionStorage.removeItem('hvnh-hub-refresh-token');
  window.sessionStorage.removeItem('hvnh-hub-user');
}

/** Revoke an earlier cookie session before authenticating as another user. */
export async function clearPreviousAuthSession(): Promise<void> {
  clearAuthSession();
  const csrf = document.cookie
    .split('; ')
    .find((item) => item.startsWith('hvnh_csrf='))
    ?.split('=')[1];
  if (!csrf) return;
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': decodeURIComponent(csrf),
    },
    body: JSON.stringify({ refresh_token: 'cookie' }),
  }).catch(() => undefined);
}

export function getAccessToken(): string | null {
  return window.sessionStorage.getItem('hvnh-hub-access-token');
}

let refreshPromise: Promise<AuthTokens> | null = null;

export async function refreshAuthSession(): Promise<AuthTokens> {
  if (refreshPromise) return refreshPromise;
  const csrf = document.cookie.split('; ').find((item) => item.startsWith('hvnh_csrf='))?.split('=')[1] || '';

  refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': decodeURIComponent(csrf) },
    body: JSON.stringify({ refresh_token: 'cookie' }),
  })
    .then(async (response) => {
      if (!response.ok) {
        clearAuthSession();
        throw await readApiError(response, 'Phiên đăng nhập đã hết hạn.');
      }
      const tokens = (await response.json()) as AuthTokens;
      saveAuthSession(tokens);
      return tokens;
    })
    .finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}

export async function getCurrentUser(accessToken?: string): Promise<AuthUser> {
  const token = accessToken || window.sessionStorage.getItem('hvnh-hub-access-token');
  if (!token) throw new Error('Bạn chưa đăng nhập.');
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw await readApiError(response, 'Phiên đăng nhập không hợp lệ.');
  return response.json() as Promise<AuthUser>;
}

export async function restoreAuthSession(): Promise<AuthUser> {
  try {
    const user = await getCurrentUser();
    window.sessionStorage.setItem('hvnh-hub-user', JSON.stringify(user));
    return user;
  } catch {
    const tokens = await refreshAuthSession();
    return tokens.user;
  }
}

export async function authenticatedFetch(
  input: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = window.sessionStorage.getItem('hvnh-hub-access-token');
  const headers = new Headers(options.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let response = await fetch(input, { ...options, headers });
  if (response.status !== 401) return response;

  // Public pages render the navbar too. Do not manufacture a refresh request
  // when the browser has neither an access session nor a refresh-cookie marker.
  const hasRefreshCookie = document.cookie
    .split('; ')
    .some((item) => item.startsWith('hvnh_csrf='));
  if (!token && !hasRefreshCookie) return response;

  const refreshed = await refreshAuthSession();
  headers.set('Authorization', `Bearer ${refreshed.access_token}`);
  response = await fetch(input, { ...options, headers });
  return response;
}

export async function logoutSession(): Promise<void> {
  const csrf = document.cookie.split('; ').find((item) => item.startsWith('hvnh_csrf='))?.split('=')[1] || '';
  if (csrf) {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': decodeURIComponent(csrf) },
      body: JSON.stringify({ refresh_token: 'cookie' }),
    }).catch(() => undefined);
  }
  clearAuthSession();
}
