'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { clearAuthSession, getAccessToken, getAuthUser, restoreAuthSession, type AuthUser } from '@/lib/auth';
import { fetchSystemStatus } from '@/lib/api';

const STATUS_TTL_MS = 30_000;
let validatedToken: string | null = null;
let validationPromise: Promise<AuthUser> | null = null;
let statusCache: { enabled: boolean; checkedAt: number } | null = null;
let statusPromise: Promise<boolean> | null = null;

function validateSession(): Promise<AuthUser> {
  const token = getAccessToken();
  const user = getAuthUser();
  if (token && token === validatedToken && user) return Promise.resolve(user);
  if (!validationPromise) {
    validationPromise = restoreAuthSession()
      .then((restored) => {
        validatedToken = getAccessToken();
        return restored;
      })
      .finally(() => { validationPromise = null; });
  }
  return validationPromise;
}

function checkSystemStatus(): Promise<boolean> {
  if (statusCache && Date.now() - statusCache.checkedAt < STATUS_TTL_MS) {
    return Promise.resolve(statusCache.enabled);
  }
  if (!statusPromise) {
    statusPromise = fetchSystemStatus()
      .then((state) => {
        statusCache = { enabled: state.enabled, checkedAt: Date.now() };
        return state.enabled;
      })
      .finally(() => { statusPromise = null; });
  }
  return statusPromise;
}

const PUBLIC_ROUTES = new Set([
  '/',
  '/login',
  '/signup',
  '/verification',
  '/password',
  '/forgot-password',
  '/welcome',
  '/maintenance',
]);

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_ROUTES.has(pathname);
  const [isReady, setIsReady] = useState(isPublic);

  useEffect(() => {
    if (isPublic) {
      setIsReady(true);
      return;
    }

    let active = true;
    const token = getAccessToken();
    const cachedUser = getAuthUser();
    const alreadyValidated = Boolean(token && token === validatedToken && cachedUser);
    if (alreadyValidated) setIsReady(true);
    else setIsReady(false);

    // A client-side route change can render immediately once this tab has
    // validated the token. Recheck maintenance in the background when stale.
    void Promise.all([
      validateSession(),
      checkSystemStatus().catch(() => false),
    ]).then(([user, maintenanceEnabled]) => {
      if (!active) return;
      if (user.system_role === 'SUPER_ADMIN' && !pathname.startsWith('/admin')) {
        router.replace('/admin');
      } else if (maintenanceEnabled && user.system_role !== 'SUPER_ADMIN') {
        router.replace('/maintenance');
      } else {
        setIsReady(true);
      }
    }).catch(() => {
      if (active) {
        validatedToken = null;
        clearAuthSession();
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      }
    });
    return () => { active = false; };
  }, [isPublic, pathname, router]);

  if (!isReady) {
    return <main className="home-loading" aria-label="Đang xác thực phiên đăng nhập" />;
  }
  return children;
}
