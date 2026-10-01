"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  api,
  getStoredToken,
  setStoredTokens,
  clearStoredTokens,
  ApiError,
} from "@/lib/api";
import type { UserSession, UserSessionAdmin, LoginRequest } from "@greencore/shared-types";

interface AuthContextType {
  user: UserSession | null;
  token: string | null;
  isLoading: boolean;
  apiConnected: boolean | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  checkHealth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  const checkHealth = useCallback(async () => {
    try {
      const res = await api.meta.getHealth();
      const isOk = res.status === "ok";
      setApiConnected(isOk);
      return isOk;
    } catch {
      setApiConnected(false);
      return false;
    }
  }, []);

  useEffect(() => {
    // 1. Initial health ping
    checkHealth();

    // 2. Hydrate token and user from localStorage
    const savedToken = getStoredToken();
    const savedUserJson = typeof window !== "undefined" ? localStorage.getItem("greencore_user") : null;

    if (savedToken && savedUserJson) {
      try {
        const parsedUser = JSON.parse(savedUserJson) as UserSession;
        setUser(parsedUser);
        setToken(savedToken);
      } catch {
        clearStoredTokens();
      }
    }
    setIsLoading(false);
  }, [checkHealth]);

  // Route protection
  useEffect(() => {
    if (isLoading) return;

    const isPublicPage = pathname === "/login";
    if (!token && !isPublicPage) {
      router.push("/login");
    } else if (token && isPublicPage) {
      router.push("/");
    }
  }, [token, isLoading, pathname, router]);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const response = await api.auth.login(credentials);
      setStoredTokens(response.access_token, response.refresh_token);
      localStorage.setItem("greencore_user", JSON.stringify(response.user));
      setUser(response.user);
      setToken(response.access_token);
      router.push("/");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearStoredTokens();
    setUser(null);
    setToken(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        apiConnected,
        login,
        logout,
        checkHealth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
