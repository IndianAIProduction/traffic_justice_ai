"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { casesApi, evidenceApi, complaintsApi } from "@/lib/api";
import { formatDate, formatCurrency } from "@/lib/utils";
import {
  Briefcase,
  FileText,
  FileAudio,
  Scale,
  Clock,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const [caseData, setCaseData] = useState<any>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (caseId) {
      Promise.all([
        casesApi.get(caseId),
        evidenceApi.listByCase(caseId),
      ])
        .then(([caseRes, evRes]) => {
          setCaseData(caseRes.data);
          setEvidence(evRes.data);
        })
        .finally(() => setLoading(false));
    }
  }, [caseId]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading case...</div>
        </main>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Case not found.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        {/* Case Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Briefcase className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold">{caseData.title}</h1>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
              caseData.status === "resolved"
                ? "bg-green-100 text-green-800"
                : caseData.status === "escalated"
                ? "bg-red-100 text-red-800"
                : "bg-yellow-100 text-yellow-800"
            }`}>
              {caseData.status}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            {caseData.case_type?.replace("_", " ")} &middot;{" "}
            {caseData.state || "N/A"} &middot;{" "}
            Created {formatDate(caseData.created_at)}
          </p>
          {caseData.description && (
            <p className="mt-3 text-sm">{caseData.description}</p>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Challans */}
          <div className="rounded-xl border bg-card p-5">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Scale className="h-5 w-5 text-primary" /> Challans
            </h2>
            {caseData.challans?.length > 0 ? (
              <div className="space-y-2">
                {caseData.challans.map((c: any) => (
                  <div key={c.id} className="rounded-lg border p-3">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">{c.challan_number || "Challan"}</span>
                      {c.has_overcharge ? (
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Charged: {formatCurrency(c.total_fine_charged || 0)} &middot;
                      Valid: {formatCurrency(c.total_fine_valid || 0)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No challans linked.</p>
            )}
            <Link
              href="/challan"
              className="mt-3 flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Validate a challan <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {/* Evidence */}
          <div className="rounded-xl border bg-card p-5">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <FileAudio className="h-5 w-5 text-primary" /> Evidence
            </h2>
            {evidence.length > 0 ? (
              <div className="space-y-2">
                {evidence.map((e: any) => (
                  <div key={e.id} className="rounded-lg border p-3">
                    <p className="text-sm font-medium">{e.file_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {e.file_type} &middot; {e.is_analyzed ? "Analyzed" : "Pending analysis"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No evidence uploaded.</p>
            )}
            <Link
              href="/evidence"
              className="mt-3 flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Upload evidence <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {/* Complaints */}
          <div className="rounded-xl border bg-card p-5 md:col-span-2">
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" /> Complaints
            </h2>
            {caseData.complaints?.length > 0 ? (
              <div className="space-y-2">
                {caseData.complaints.map((comp: any) => (
                  <div key={comp.id} className="rounded-lg border p-3 flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium">{comp.complaint_type} complaint</p>
                      <p className="text-xs text-muted-foreground">
                        {comp.portal_name || "Portal TBD"} &middot; {formatDate(comp.created_at)}
                      </p>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      comp.status === "resolved"
                        ? "bg-green-100 text-green-800"
                        : comp.status === "submitted"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}>
                      {comp.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No complaints filed.</p>
            )}
            <Link
              href="/complaints"
              className="mt-3 flex items-center gap-1 text-sm text-primary hover:underline"
            >
              File a complaint <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
