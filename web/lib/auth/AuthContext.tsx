"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, setAuthToken } from "@/lib/api/client";
import { login as loginRequest } from "@/lib/api/login";
import type { components } from "@/lib/api/schema";

type User = components["schemas"]["UserRead"];

const TOKEN_STORAGE_KEY = "noar.token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function fetchCurrentUser(): Promise<User | null> {
  const { data } = await api.GET("/auth/me");
  return data ?? null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!storedToken) {
      // Nothing to restore: this is the end of the fetch-on-mount lookup,
      // not a side effect reacting to render state.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsLoading(false);
      return;
    }

    setAuthToken(storedToken);
    fetchCurrentUser()
      .then((currentUser) => {
        if (currentUser === null) {
          window.localStorage.removeItem(TOKEN_STORAGE_KEY);
          setAuthToken(null);
        } else {
          setToken(storedToken);
        }
        setUser(currentUser);
      })
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string): Promise<void> {
    const loggedInToken = await loginRequest(email, password);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, loggedInToken.access_token);
    setAuthToken(loggedInToken.access_token);
    setToken(loggedInToken.access_token);
    setUser(await fetchCurrentUser());
  }

  async function register(email: string, password: string): Promise<void> {
    const { error } = await api.POST("/auth/register", { body: { email, password } });
    if (error) {
      throw new Error("Não foi possível criar a conta. O e-mail já pode estar em uso.");
    }
    await login(email, password);
  }

  function logout(): void {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setAuthToken(null);
    setToken(null);
    setUser(null);
  }

  async function refreshUser(): Promise<void> {
    setUser(await fetchCurrentUser());
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
