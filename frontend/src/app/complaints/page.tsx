"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { complaintsApi, casesApi } from "@/lib/api";
import type { Complaint, SubmissionDetails } from "@/types";
import { extractErrorMessage } from "@/lib/utils";
import {
  FileText,
  ArrowRight,
  Loader2,
  Mail,
  FileDown,
  Globe,
  Phone,
  CheckCircle2,
  ExternalLink,
  Shield,
  Copy,
  Check,
} from "lucide-react";
import { useLanguage } from "@/hooks/useLanguage";

function buildMailtoUrl(
  emails: string[],
  ccEmails: string[],
  subject: string,
  body: string
) {
  const to = emails.join(",");
  const params = new URLSearchParams();
  if (ccEmails.length > 0) params.set("cc", ccEmails.join(","));
  params.set("subject", subject);
  params.set("body", body);
  return `mailto:${to}?${params.toString()}`;
}

export default function ComplaintsPage() {
  const [caseId, setCaseId] = useState("");
  const [complaintType, setComplaintType] = useState("misconduct");
  const [description, setDescription] = useState("");
  const [draft, setDraft] = useState<Complaint | null>(null);
  const [editText, setEditText] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);
  const [existingCases, setExistingCases] = useState<
    Array<{ id: string; title: string; state?: string }>
  >([]);
  const [submissionDetails, setSubmissionDetails] =
    useState<SubmissionDetails | null>(null);
  const [submissionStep, setSubmissionStep] = useState("");
  const [copied, setCopied] = useState(false);
  const { language } = useLanguage();

  useEffect(() => {
    casesApi
      .list()
      .then(({ data }) => {
        setExistingCases(
          (data.cases || data || []).map((c: any) => ({
            id: c.id,
            title: c.title,
            state: c.state,
          }))
        );
      })
      .catch(() => {});
  }, []);

  const handleDraft = async () => {
    setError("");
    setLoading(true);
    try {
      const payload: any = { complaint_type: complaintType, language };
      if (caseId) payload.case_id = caseId;
      if (description) payload.description = description;
      const { data } = await complaintsApi.draft(payload);
      setDraft(data);
      setEditText(data.draft_text || "");
    } catch (err: any) {
      setError(extractErrorMessage(err, "Failed to generate draft"));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!draft) return;
    try {
      const { data } = await complaintsApi.edit(draft.id, {
        final_text: editText,
      });
      setDraft(data);
    } catch (err: any) {
      setError(extractErrorMessage(err, "Failed to save"));
    }
  };

  const handleSubmit = async () => {
    if (!draft || !consent) return;
    setSubmitting(true);
    setError("");
    setSubmissionStep("Processing your complaint...");

    try {
      setSubmissionStep("Preparing submission channels...");
      const { data } = await complaintsApi.submit(draft.id, {
        user_consent: true,
      });
      setDraft(data);
      if (data.submission_details) {
        setSubmissionDetails(data.submission_details);
      }
    } catch (err: any) {
      setError(extractErrorMessage(err, "Submission failed"));
    } finally {
      setSubmitting(false);
      setSubmissionStep("");
    }
  };

  const handleCopyText = () => {
    const text = draft?.final_text || draft?.draft_text || editText;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPdf = async () => {
    if (!draft) return;
    try {
      const response = await complaintsApi.downloadPdf(draft.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `complaint_${draft.id.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("PDF not available yet.");
    }
  };

  const complaintText = draft?.final_text || draft?.draft_text || "";
  const emailSubject = `[Grievance] Traffic ${complaintType.replace("_", " ")} Complaint - ${new Date().toLocaleDateString("en-IN")}`;

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
          <FileText className="h-6 w-6 text-primary" /> Complaints
        </h1>
        <p className="text-sm text-muted-foreground mb-8">
          AI-assisted complaint drafting and real grievance portal submission.
        </p>

        {/* Step 1: Generate Draft */}
        {!draft && (
          <div className="rounded-xl border bg-card p-8 max-w-lg mx-auto">
            <h2 className="text-lg font-semibold mb-4">New Complaint</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">
                  Linked Case
                </label>
                <select
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                >
                  <option value="">New case (auto-create)</option>
                  {existingCases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} ({c.id.slice(0, 8)}...)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">
                  Complaint Type
                </label>
                <select
                  value={complaintType}
                  onChange={(e) => setComplaintType(e.target.value)}
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                >
                  <option value="misconduct">Officer Misconduct</option>
                  <option value="overcharge">Fine Overcharge</option>
                  <option value="general">General Grievance</option>
                </select>
              </div>
              {!caseId && (
                <div>
                  <label className="block text-sm font-medium mb-1.5">
                    Brief Description
                  </label>
                  <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="e.g. Officer demanded extra Rs 500 during traffic stop"
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
              )}
              {error && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}
              <button
                onClick={handleDraft}
                disabled={loading}
                className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
                {loading ? "Generating draft..." : "Generate Complaint Draft"}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Review & Edit */}
        {draft && draft.status === "drafted" && (
          <div className="space-y-6">
            <div className="rounded-xl border bg-card p-6">
              <h2 className="text-lg font-semibold mb-4">
                Review & Edit Complaint
              </h2>
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                rows={15}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm font-mono"
              />
              <div className="flex gap-2 mt-4">
                <button
                  onClick={handleSave}
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
                >
                  Save Changes
                </button>
              </div>
            </div>

            {/* Step 3: Consent & Submit */}
            <div className="rounded-xl border bg-card p-6">
              <h2 className="text-lg font-semibold mb-2">
                Submit to Grievance Portal
              </h2>
              <p className="text-xs text-muted-foreground mb-4">
                After submission, you can directly email the complaint to
                authorities from your own email, open the official grievance
                portal, or download a formal PDF to submit manually.
              </p>

              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="mt-1"
                />
                <span className="text-sm text-muted-foreground">
                  I consent to the submission of this complaint. I confirm that
                  the information provided is truthful and based on evidence.
                </span>
              </label>

              {error && (
                <div className="mt-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {submitting && submissionStep && (
                <div className="mt-4 rounded-md bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 p-4">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      {submissionStep}
                    </p>
                  </div>
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={!consent || submitting}
                className="mt-4 w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Shield className="h-4 w-4" />
                )}
                {submitting ? "Processing..." : "Submit Complaint"}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Submission Results -- action-oriented */}
        {draft && draft.status !== "drafted" && (
          <div className="space-y-6">
            {/* Success header */}
            <div className="rounded-xl border bg-card p-8 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
                <CheckCircle2 className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-xl font-bold mb-2">
                Complaint Ready to Submit
              </h2>
              <p className="text-sm text-muted-foreground">
                Your complaint has been recorded. Now choose how to submit it to
                the authorities:
              </p>
            </div>

            {/* Primary actions: Email & Portal */}
            <div className="rounded-xl border bg-card p-6">
              <h3 className="text-lg font-semibold mb-4">
                Choose Submission Method
              </h3>

              <div className="grid gap-4 md:grid-cols-2">
                {/* Option 1: Email via user's own email */}
                <div className="rounded-lg border-2 border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Mail className="h-5 w-5 text-blue-600" />
                    <h4 className="font-semibold text-sm">
                      Email to Authorities
                    </h4>
                    <span className="text-[10px] bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded font-medium">
                      RECOMMENDED
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">
                    Opens your Gmail / email app with the complaint pre-filled
                    and addressed to the right authorities. You just hit Send.
                  </p>
                  {submissionDetails && (
                    <a
                      href={buildMailtoUrl(
                        submissionDetails.email_recipients,
                        [],
                        emailSubject,
                        complaintText +
                          "\n\n---\nSubmitted via Traffic Justice AI"
                      )}
                      className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
                    >
                      <Mail className="h-4 w-4" />
                      Open Email & Send
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                  {submissionDetails &&
                    submissionDetails.email_recipients.length > 0 && (
                      <p className="text-[10px] text-muted-foreground mt-2">
                        To:{" "}
                        {submissionDetails.email_recipients
                          .slice(0, 2)
                          .join(", ")}
                        {submissionDetails.email_recipients.length > 2 &&
                          ` +${submissionDetails.email_recipients.length - 2} more`}
                      </p>
                    )}
                </div>

                {/* Option 2: Open official portal */}
                <div className="rounded-lg border-2 border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-950/20 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Globe className="h-5 w-5 text-green-600" />
                    <h4 className="font-semibold text-sm">
                      Official Grievance Portal
                    </h4>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">
                    Opens the official {submissionDetails?.state_name || ""}{" "}
                    grievance portal where you can register and submit the
                    complaint directly.
                  </p>
                  {submissionDetails?.portal_url && (
                    <a
                      href={
                        submissionDetails.complaint_form_url ||
                        submissionDetails.portal_url
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700 transition-colors"
                    >
                      <Globe className="h-4 w-4" />
                      Open{" "}
                      {submissionDetails.portal_name?.split("(")[0]?.trim() ||
                        "Portal"}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                  {submissionDetails?.portal_url && (
                    <p className="text-[10px] text-muted-foreground mt-2 break-all">
                      {submissionDetails.portal_url}
                    </p>
                  )}
                </div>
              </div>

              {/* Secondary actions */}
              <div className="flex flex-wrap gap-3 mt-4 pt-4 border-t">
                <button
                  onClick={handleCopyText}
                  className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-medium hover:bg-accent transition-colors"
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-green-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                  {copied ? "Copied!" : "Copy Complaint Text"}
                </button>

                {submissionDetails?.pdf_generated && (
                  <button
                    onClick={handleDownloadPdf}
                    className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-medium hover:bg-accent transition-colors"
                  >
                    <FileDown className="h-3.5 w-3.5" />
                    Download PDF
                  </button>
                )}

                {/* PGPortal as fallback */}
                <a
                  href="https://pgportal.gov.in/Registration"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-medium hover:bg-accent transition-colors"
                >
                  <Globe className="h-3.5 w-3.5" />
                  Central PG Portal (CPGRAMS)
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>

            {/* Helpline numbers */}
            {submissionDetails &&
              Object.keys(submissionDetails.helplines).length > 0 && (
                <div className="rounded-xl border bg-card p-6">
                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-1.5">
                    <Phone className="h-4 w-4" /> Helpline Numbers (
                    {submissionDetails.state_name})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(submissionDetails.helplines).map(
                      ([key, number]) => (
                        <a
                          key={key}
                          href={`tel:${number}`}
                          className="inline-flex items-center gap-1.5 text-xs bg-muted px-3 py-1.5 rounded-full hover:bg-accent transition-colors"
                        >
                          <Phone className="h-3 w-3 text-primary" />
                          <span className="text-muted-foreground capitalize">
                            {key.replace(/_/g, " ")}:
                          </span>
                          <span className="font-mono font-semibold text-primary">
                            {number}
                          </span>
                        </a>
                      )
                    )}
                  </div>
                </div>
              )}

            {/* View Case link */}
            <div className="text-center">
              <Link
                href={`/cases/${draft.case_id}`}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm text-primary-foreground hover:bg-primary/90"
              >
                View Case <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
