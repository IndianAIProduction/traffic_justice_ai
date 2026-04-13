import { authApi } from "./api";
import type { User } from "@/types";

export type { User };

export async function login(email: string, password: string): Promise<User> {
  const { data } = await authApi.login({ email, password });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  const { data: user } = await authApi.me();
  return user;
}

export async function register(
  email: string,
  password: string,
  fullName: string,
  state?: string
): Promise<User> {
  const { data: user } = await authApi.register({
    email,
    password,
    full_name: fullName,
    state,
  });
  return user;
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
