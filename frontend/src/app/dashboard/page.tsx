"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { useAuth } from "@/hooks/useAuth";
import { casesApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Case } from "@/types";
import {
  Scale,
  FileSearch,
  Shield,
  BarChart3,
  Plus,
  Clock,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

const quickActions = [
  { icon: Scale, label: "Legal Help", href: "/legal-help", color: "text-blue-600" },
  { icon: FileSearch, label: "Validate Challan", href: "/challan", color: "text-green-600" },
  { icon: Shield, label: "Upload Evidence", href: "/evidence", color: "text-purple-600" },
  { icon: BarChart3, label: "Analytics", href: "/analytics", color: "text-orange-600" },
];

const statusIcons: Record<string, typeof Clock> = {
  open: Clock,
  in_progress: AlertTriangle,
  resolved: CheckCircle2,
  escalated: AlertTriangle,
};

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const [cases, setCases] = useState<Case[]>([]);

  useEffect(() => {
    if (user) {
      casesApi.list({ limit: 5 }).then(({ data }) => setCases(data)).catch(() => setCases([]));
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="mb-4 text-muted-foreground">Please sign in to access your dashboard.</p>
          <Link href="/login" className="text-primary hover:underline font-medium">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Welcome, {user.full_name || "Driver"}</h1>
          <p className="text-muted-foreground mt-1">
            Your traffic justice dashboard &mdash; manage cases, evidence, and complaints.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {quickActions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="flex flex-col items-center gap-3 rounded-xl border bg-card p-6 hover:shadow-md transition-all"
            >
              <action.icon className={`h-8 w-8 ${action.color}`} />
              <span className="text-sm font-medium">{action.label}</span>
            </Link>
          ))}
        </div>

        {/* Recent Cases */}
        <div className="rounded-xl border bg-card">
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-lg font-semibold">Recent Cases</h2>
            <Link
              href="/cases"
              className="text-sm text-primary hover:underline flex items-center gap-1"
            >
              View all <Plus className="h-3 w-3" />
            </Link>
          </div>
          {cases.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <p className="mb-4">No cases yet. Create your first case to get started.</p>
              <Link
                href="/cases"
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
              >
                <Plus className="h-4 w-4" /> New Case
              </Link>
            </div>
          ) : (
            <div className="divide-y">
              {cases.map((c) => {
                const StatusIcon = statusIcons[c.status] || Clock;
                return (
                  <Link
                    key={c.id}
                    href={`/cases/${c.id}`}
                    className="flex items-center justify-between p-4 hover:bg-muted/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <StatusIcon className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{c.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {c.case_type.replace("_", " ")} &middot; {c.state || "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.status === "resolved"
                          ? "bg-green-100 text-green-800"
                          : c.status === "escalated"
                          ? "bg-red-100 text-red-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}>
                        {c.status}
                      </span>
                      <p className="text-xs text-muted-foreground mt-1">{formatDate(c.created_at)}</p>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
