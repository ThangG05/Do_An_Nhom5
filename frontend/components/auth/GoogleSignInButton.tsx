'use client';

import Script from 'next/script';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

import { authenticateWithGoogle, clearPreviousAuthSession, saveAuthSession } from '@/lib/auth';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface CredentialResponse {
  credential?: string;
}

interface GoogleIdentityApi {
  accounts: {
    id: {
      initialize(options: {
        client_id: string;
        callback: (response: CredentialResponse) => void;
        hd?: string;
      }): void;
      renderButton(
        parent: HTMLElement,
        options: {
          type: 'standard';
          theme: 'outline';
          size: 'large';
          text: 'continue_with';
          shape: 'rectangular';
          locale: 'vi';
          width: number;
        },
      ): void;
    };
  };
}

declare global {
  interface Window {
    google?: GoogleIdentityApi;
  }
}

export default function GoogleSignInButton() {
  const buttonRef = useRef<HTMLDivElement>(null);
  const initializedRef = useRef(false);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [clientId, setClientId] = useState<string | null>(null);
  const [configLoaded, setConfigLoaded] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    fetch(`${API_BASE_URL}/system/public-config`, {
      cache: 'no-store',
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('Không tải được cấu hình đăng nhập.');
        return response.json() as Promise<{ google_client_id?: string | null }>;
      })
      .then((config) => {
        if (active) setClientId(config.google_client_id?.trim() || null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        if (active) setMessage('Không thể đọc cấu hình Google từ backend.');
      })
      .finally(() => {
        if (active) setConfigLoaded(true);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  function renderGoogleButton() {
    if (!clientId || !window.google || !buttonRef.current) return;
    if (initializedRef.current && buttonRef.current.childElementCount > 0) return;
    initializedRef.current = true;

    window.google.accounts.id.initialize({
      client_id: clientId,
      hd: 'hvnh.edu.vn',
      callback: async ({ credential }) => {
        if (!credential) {
          setMessage('Google không trả về thông tin đăng nhập.');
          return;
        }

        setIsLoading(true);
        setMessage('');
        try {
          await clearPreviousAuthSession();
          const tokens = await authenticateWithGoogle(credential);
          saveAuthSession(tokens);
          router.replace(tokens.user.system_role === 'SUPER_ADMIN' ? '/admin' : tokens.user.admin_group_slugs.length ? '/group-admin' : '/home');
        } catch (error) {
          setMessage(
            error instanceof Error
              ? error.message
              : 'Không thể đăng nhập bằng Google.',
          );
        } finally {
          setIsLoading(false);
        }
      },
    });

    buttonRef.current.replaceChildren();
    window.google.accounts.id.renderButton(buttonRef.current, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'continue_with',
      shape: 'rectangular',
      locale: 'vi',
      width: Math.min(buttonRef.current.clientWidth || 400, 400),
    });
  }

  if (!configLoaded) {
    return (
      <p className="google-auth-message" role="status">
        Đang tải đăng nhập Google…
      </p>
    );
  }

  if (!clientId) {
    return (
      <p className="google-auth-message google-auth-error" role="alert">
        Backend chưa cấu hình đăng nhập Google.
      </p>
    );
  }

  return (
    <div className="google-auth">
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onReady={renderGoogleButton}
        onError={() => setMessage('Không tải được dịch vụ đăng nhập Google.')}
      />
      <div
        ref={buttonRef}
        className={isLoading ? 'google-auth-button is-loading' : 'google-auth-button'}
        aria-label="Tiếp tục với Google"
      />
      {isLoading ? <p className="google-auth-message">Đang đăng nhập…</p> : null}
      {message ? (
        <p className="google-auth-message google-auth-error" role="alert">
          {message}
        </p>
      ) : null}
    </div>
  );
}
