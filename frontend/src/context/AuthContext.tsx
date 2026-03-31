import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/api';
import type { User, LoginCredentials } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const currentUser = await authAPI.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };

    initAuth();
    // Heartbeat is handled by WebSocket in useActivityMonitor (single mechanism)
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const response = await authAPI.login(credentials);

    // SECURITY: Use session_start from BACKEND (single source of truth)
    // NEVER create timestamp on frontend - always use backend time
    // This ensures identical timestamp between frontend and backend
    if (response.session_start) {
      localStorage.setItem('session_start', response.session_start);
    }

    // Fetch current user (includes previous_login from backend)
    // Token is set AFTER this succeeds to avoid broken state where token exists but user is null
    const currentUser = await authAPI.getCurrentUser();

    // Only persist token after successful user fetch
    localStorage.setItem('access_token', response.access_token);

    // SECURITY: Save previous_login to localStorage (backend is source of truth)
    // This value is FIXED and should NEVER change during current session
    if (currentUser.previous_login) {
      localStorage.setItem('previous_login', currentUser.previous_login);
    }

    setUser(currentUser);
  };

  const logout = async () => {
    try {
      // Call backend logout endpoint to update online status
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local storage and redirect
      localStorage.removeItem('access_token');
      // SECURITY: Clear session_start and previous_login on logout
      localStorage.removeItem('session_start');
      localStorage.removeItem('previous_login');
      setUser(null);
      window.location.href = '/login';
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
