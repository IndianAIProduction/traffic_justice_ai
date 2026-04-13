"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";
import { LANGUAGES } from "@/lib/constants";
import { Shield, Menu, X, Globe } from "lucide-react";
import { useState } from "react";

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/legal-help", label: "Legal Help" },
  { href: "/challan", label: "Challan" },
  { href: "/evidence", label: "Evidence" },
  { href: "/complaints", label: "Complaints" },
  { href: "/cases", label: "Cases" },
  { href: "/analytics", label: "Analytics" },
];

export function Header() {
  const { user, logout } = useAuth();
  const { language, setLanguage, languageLabel } = useLanguage();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex flex-col gap-0.5">
          <Link href="/" className="flex items-center gap-2 w-fit">
            <Shield className="h-6 w-6 text-primary shrink-0" />
            <div className="flex flex-col leading-tight">
              <span className="text-lg font-bold">Traffic Justice AI</span>
              <span className="text-sm font-semibold text-primary/70 tracking-wider">Bhrashtachar Ko Roko</span>
            </div>
          </Link>
          <a
            href="https://indianaiproduction.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-muted-foreground hover:text-primary hover:underline w-fit pl-8"
          >
            Indian AI Production
          </a>
        </div>

        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-1">
            <Globe className="h-3.5 w-3.5 text-muted-foreground" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value, true)}
              className="bg-transparent text-sm font-medium border-none outline-none cursor-pointer text-muted-foreground hover:text-foreground pr-1"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.nativeLabel}
                </option>
              ))}
            </select>
          </div>

          {user ? (
            <div className="hidden md:flex items-center gap-3">
              <span className="text-sm text-muted-foreground">{user.full_name || user.email}</span>
              <button
                onClick={logout}
                className="text-sm font-medium text-destructive hover:underline"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-2">
              <Link href="/login" className="text-sm font-medium hover:underline">
                Login
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Register
              </Link>
            </div>
          )}

          <button
            className="md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t p-4 space-y-3">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className="block text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
          <div className="flex items-center gap-2 pt-2 border-t">
            <Globe className="h-3.5 w-3.5 text-muted-foreground" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value, true)}
              className="bg-transparent text-sm border-none outline-none"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.nativeLabel}</option>
              ))}
            </select>
          </div>
          {user ? (
            <button onClick={logout} className="text-sm text-destructive">
              Logout
            </button>
          ) : (
            <Link href="/login" onClick={() => setMobileOpen(false)} className="text-sm font-medium">
              Login
            </Link>
          )}
        </div>
      )}
    </header>
  );
}
