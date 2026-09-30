"use client";
import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchClient } from './api';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Basic check for auth status if needed. 
    // Since we use HttpOnly cookies, we can't read the token in JS.
    // We could either add a /me endpoint, or assume false and let fetch calls fail with 401.
    // For now, assume false on mount until they login, or if they have a non-httponly flag cookie.
    setIsLoading(false);
  }, []);

  const login = () => {
    setIsAuthenticated(true);
    router.push('/dashboard');
  };

  const logout = async () => {
    try {
      await fetchClient('/api/v1/auth/logout', { method: 'POST' });
    } catch (e) {
      // ignore
    }
    setIsAuthenticated(false);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
