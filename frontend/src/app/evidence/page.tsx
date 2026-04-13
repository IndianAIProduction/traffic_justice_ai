"use client";

import { useState, useCallback, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { evidenceApi, casesApi } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { Evidence } from "@/types";
import { extractErrorMessage } from "@/lib/utils";
import { Upload, FileAudio, FileVideo, Image, FileText, CheckCircle2, Loader2 } from "lucide-react";

const typeIcons = {
  audio: FileAudio,
  video: FileVideo,
  image: Image,
  document: FileText,
};

export default function EvidencePage() {
  const { user } = useAuth();
  const [caseId, setCaseId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploaded, setUploaded] = useState<Evidence | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [existingCases, setExistingCases] = useState<Array<{ id: string; title: string }>>([]);

  useEffect(() => {
    casesApi.list().then(({ data }) => {
      setExistingCases(
        (data.cases || data || []).map((c: any) => ({ id: c.id, title: c.title }))
      );
    }).catch(() => {});
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      const { data } = await evidenceApi.upload(caseId, file);
      setUploaded(data);
    } catch (err: any) {
      setError(extractErrorMessage(err, "Upload failed"));
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!uploaded) return;
    setAnalyzing(true);
    try {
      const { data } = await evidenceApi.analyze(uploaded.id);
      setAnalysis(data.analysis);
    } catch (err: any) {
      setError(extractErrorMessage(err, "Analysis failed"));
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
          <Upload className="h-6 w-6 text-primary" /> Evidence Upload
        </h1>
        <p className="text-sm text-muted-foreground mb-8">
          Securely upload audio, video, or photo evidence. Files are encrypted and analyzed by AI.
        </p>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Upload */}
          <div className="space-y-4">
            <div className="rounded-xl border bg-card p-6">
              <label className="block text-sm font-medium mb-1.5">Case</label>
              <select
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm mb-4"
              >
                <option value="">New case (auto-create)</option>
                {existingCases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} ({c.id.slice(0, 8)}...)
                  </option>
                ))}
              </select>

              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
                  dragOver ? "border-primary bg-primary/5" : "border-border"
                }`}
              >
                <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
                <p className="text-sm text-muted-foreground mb-2">
                  Drag & drop evidence file here, or
                </p>
                <label className="cursor-pointer text-sm text-primary hover:underline font-medium">
                  Browse files
                  <input
                    type="file"
                    className="hidden"
                    accept="audio/*,video/*,image/*,.pdf"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </label>
                {file && (
                  <p className="mt-3 text-sm font-medium">
                    Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)
                  </p>
                )}
              </div>

              {error && (
                <div className="mt-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              <div className="mt-4 flex gap-2">
                <button
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  className="flex-1 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                  {uploading ? "Uploading..." : "Upload"}
                </button>
                {uploaded && (
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="flex-1 rounded-md border px-4 py-2.5 text-sm font-medium hover:bg-accent disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {analyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    {analyzing ? "Analyzing..." : "Analyze Evidence"}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Analysis Results</h2>
            {!uploaded && !analysis ? (
              <div className="flex flex-col items-center justify-center h-60 text-muted-foreground">
                <FileAudio className="h-12 w-12 mb-3 opacity-20" />
                <p className="text-sm text-center">Upload and analyze evidence to see results.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {uploaded && (
                  <div className="flex items-center gap-2 rounded-lg border p-3 bg-green-50">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium">File uploaded securely</p>
                      <p className="text-xs text-muted-foreground">
                        {uploaded.file_name} &middot; Hash: {uploaded.file_hash?.slice(0, 16)}...
                      </p>
                    </div>
                  </div>
                )}
                {analysis && (
                  <>
                    <div className={`rounded-lg p-3 ${
                      analysis.misconduct_detected
                        ? "bg-red-50 border border-red-200"
                        : "bg-green-50 border border-green-200"
                    }`}>
                      <p className="font-medium text-sm">
                        {analysis.misconduct_detected
                          ? `Misconduct Detected (Severity: ${analysis.overall_severity}/5)`
                          : "No misconduct detected"}
                      </p>
                      {analysis.summary && (
                        <p className="text-sm text-muted-foreground mt-1">{analysis.summary}</p>
                      )}
                    </div>
                    {analysis.misconduct_flags?.map((flag: any, i: number) => (
                      <div key={i} className="rounded-lg border p-3">
                        <div className="flex justify-between">
                          <span className="text-sm font-medium capitalize">
                            {flag.flag_type?.replace("_", " ")}
                          </span>
                          <span className="text-xs bg-red-100 text-red-700 rounded-full px-2 py-0.5">
                            Severity: {flag.severity}/5
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{flag.description}</p>
                        {flag.raw_quote && (
                          <p className="text-xs italic mt-1 bg-muted p-2 rounded">
                            &ldquo;{flag.raw_quote}&rdquo;
                          </p>
                        )}
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
