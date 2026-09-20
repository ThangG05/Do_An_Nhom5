'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { clearAuthSession, getAuthUser, restoreAuthSession } from '@/lib/auth';
import { fetchSystemStatus } from '@/lib/api';

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

    setIsReady(false);
    restoreAuthSession()
      .then(async () => {
        const user = getAuthUser();
        if (user?.system_role === 'SUPER_ADMIN' && !pathname.startsWith('/admin')) {
          router.replace('/admin');
          return;
        }
        const state = await fetchSystemStatus();
        if (state.enabled && user?.system_role !== 'SUPER_ADMIN') {
          router.replace('/maintenance');
          return;
        }
        setIsReady(true);
      })
      .catch(() => {
        clearAuthSession();
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      });
  }, [isPublic, pathname, router]);

  if (!isReady) {
    return <main className="home-loading" aria-label="Đang xác thực phiên đăng nhập" />;
  }
  return children;
}
