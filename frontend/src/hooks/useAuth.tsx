/**
 * url: /frontend/src/hooks/useAuth.tsx
 * About:
 *   Auth context and hook for ValLG frontend. Provides authentication
 *   state (user, token, loading) and auth actions (login, logout) to
 *   all components via React Context. Token stored in localStorage.
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { User } from '../types';
import * as authApi from '../api/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('vallg_token'));
  const [loading, setLoading] = useState(true);

  // Check token validity on mount
  useEffect(() => {
    async function checkAuth() {
      const storedToken = localStorage.getItem('vallg_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
        setToken(storedToken);
      } catch {
        // Token invalid or expired
        localStorage.removeItem('vallg_token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setToken(response.token);
    setUser(response.user);
  }, []);

  const signup = useCallback(async (name: string, email: string, password: string) => {
    const response = await authApi.signup(name, email, password);
    setToken(response.token);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem('vallg_token');
      setToken(null);
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
