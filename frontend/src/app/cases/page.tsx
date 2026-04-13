"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { useAuth } from "@/hooks/useAuth";
import { casesApi, type CaseCreatePayload } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Case } from "@/types";
import { Briefcase, Plus, Clock, CheckCircle2, AlertTriangle } from "lucide-react";

export default function CasesPage() {
  const { user } = useAuth();
  const [cases, setCases] = useState<Case[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CaseCreatePayload>({
    title: "",
    case_type: "challan",
    state: "",
    description: "",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) casesApi.list().then(({ data }) => setCases(data));
  }, [user]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await casesApi.create(form);
      setCases([data, ...cases]);
      setShowCreate(false);
      setForm({ title: "", case_type: "challan", state: "", description: "" });
    } finally {
      setLoading(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "resolved": return "bg-green-100 text-green-800";
      case "escalated": return "bg-red-100 text-red-800";
      case "in_progress": return "bg-blue-100 text-blue-800";
      default: return "bg-yellow-100 text-yellow-800";
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Briefcase className="h-6 w-6 text-primary" /> My Cases
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Manage your traffic-related cases, evidence, and complaints.
            </p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> New Case
          </button>
        </div>

        {showCreate && (
          <div className="rounded-xl border bg-card p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Create New Case</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input
                type="text"
                placeholder="Case title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                required
              />
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={form.case_type}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      case_type: e.target.value as CaseCreatePayload["case_type"],
                    })
                  }
                  className="rounded-md border bg-background px-3 py-2 text-sm"
                >
                  <option value="traffic_stop">Traffic Stop</option>
                  <option value="challan">Challan</option>
                  <option value="misconduct">Misconduct</option>
                </select>
                <input
                  type="text"
                  placeholder="State"
                  value={form.state}
                  onChange={(e) => setForm({ ...form, state: e.target.value })}
                  className="rounded-md border bg-background px-3 py-2 text-sm"
                />
              </div>
              <textarea
                placeholder="Description (optional)"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {loading ? "Creating..." : "Create Case"}
              </button>
            </form>
          </div>
        )}

        <div className="rounded-xl border bg-card divide-y">
          {cases.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              No cases yet. Click &ldquo;New Case&rdquo; to create one.
            </div>
          ) : (
            cases.map((c) => (
              <Link
                key={c.id}
                href={`/cases/${c.id}`}
                className="flex items-center justify-between p-4 hover:bg-muted/50 transition"
              >
                <div>
                  <p className="font-medium">{c.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {c.case_type.replace("_", " ")} &middot; {c.state || "N/A"} &middot; {formatDate(c.created_at)}
                  </p>
                </div>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(c.status)}`}>
                  {c.status}
                </span>
              </Link>
            ))
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
