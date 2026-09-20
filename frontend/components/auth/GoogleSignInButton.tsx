'use client';

import Script from 'next/script';
import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

import { authenticateWithGoogle, clearPreviousAuthSession, saveAuthSession } from '@/lib/auth';

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
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  function renderGoogleButton() {
    if (!clientId || !window.google || !buttonRef.current) return;

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
          router.replace(tokens.user.system_role === 'SUPER_ADMIN' ? '/admin' : '/home');
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

  if (!clientId) {
    return (
      <p className="google-auth-message" role="status">
        Đăng nhập Google chưa được cấu hình.
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
