"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getAuthUser, type AuthUser } from "@/lib/auth";

const AuthUserContext = createContext<AuthUser | null>(null);

/** A single in-memory identity prevents every card from requesting /auth/me. */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const sync = () => setUser(getAuthUser());
    sync();
    window.addEventListener("hvnh-auth-changed", sync);
    return () => window.removeEventListener("hvnh-auth-changed", sync);
  }, []);

  return <AuthUserContext.Provider value={useMemo(() => user, [user])}>{children}</AuthUserContext.Provider>;
}

export function useAuthUser() {
  return useContext(AuthUserContext);
}
