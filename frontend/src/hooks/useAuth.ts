"use client";

import { useState, useEffect, useCallback } from "react";
import { authApi } from "@/lib/api";
import { login as doLogin, logout as doLogout, isAuthenticated } from "@/lib/auth";
import type { User } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    if (!isAuthenticated()) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await authApi.me();
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    const u = await doLogin(email, password);
    setUser(u);
    return u;
  };

  const logout = () => {
    setUser(null);
    doLogout();
  };

  return { user, loading, login, logout, refetch: fetchUser };
}
