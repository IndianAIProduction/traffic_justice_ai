"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { challanApi, type ScheduleSectionItem } from "@/lib/api";
import { formatCurrency, extractErrorMessage } from "@/lib/utils";
import type { ChallanValidation, ChallanSection } from "@/types";
import { FileSearch, Plus, Trash2, CheckCircle2, AlertTriangle, HelpCircle, Info } from "lucide-react";
import { INDIAN_STATES } from "@/lib/constants";

export default function ChallanPage() {
  const [sections, setSections] = useState<ChallanSection[]>([{ section: "", amount: 0 }]);
  const [state, setState] = useState("Maharashtra");
  const [challanNumber, setChallanNumber] = useState("");
  const [result, setResult] = useState<ChallanValidation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showHelper, setShowHelper] = useState(false);
  const [scheduleRows, setScheduleRows] = useState<ScheduleSectionItem[]>([]);
  const [scheduleLoading, setScheduleLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setScheduleLoading(true);
    challanApi
      .scheduleSections(state)
      .then((res) => {
        if (!cancelled) setScheduleRows(res.data);
      })
      .catch(() => {
        if (!cancelled) setScheduleRows([]);
      })
      .finally(() => {
        if (!cancelled) setScheduleLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [state]);

  const addSection = () => setSections([...sections, { section: "", amount: 0 }]);

  const removeSection = (i: number) => {
    if (sections.length > 1) setSections(sections.filter((_, idx) => idx !== i));
  };

  const updateSection = (i: number, field: keyof ChallanSection, value: string | number) => {
    const updated = [...sections];
    (updated[i] as any)[field] = value;
    setSections(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const { data } = await challanApi.validate({
        challan_number: challanNumber || undefined,
        sections: sections.filter((s) => s.section && s.amount > 0),
        state,
      });
      setResult(data.validation_result);
    } catch (err: any) {
      setError(extractErrorMessage(err, "Validation failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-2">
          <FileSearch className="h-6 w-6 text-primary" /> Challan Validation
        </h1>
        <p className="text-sm text-muted-foreground mb-8">
          Enter challan details to verify fines against official schedules and detect overcharges.
        </p>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Input Form */}
          <div className="rounded-xl border bg-card p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">State</label>
                  <select
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  >
                    {INDIAN_STATES.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Challan No.</label>
                  <input
                    type="text"
                    value={challanNumber}
                    onChange={(e) => setChallanNumber(e.target.value)}
                    placeholder="Optional"
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-2">
                  <label className="block text-sm font-medium">Sections & Fines</label>
                  <button
                    type="button"
                    onClick={() => setShowHelper(!showHelper)}
                    className="text-muted-foreground hover:text-primary"
                    title="Show common section codes"
                  >
                    <Info className="h-3.5 w-3.5" />
                  </button>
                </div>
                {showHelper && (
                  <div className="mb-3 rounded-md border bg-blue-50 p-2.5 text-xs">
                    <p className="font-medium text-blue-800 mb-1.5">
                      Sections in our schedule for <strong>{state}</strong>
                      {scheduleRows.length > 0 ? ` (${scheduleRows.length})` : ""}:
                    </p>
                    {scheduleLoading ? (
                      <p className="text-blue-700">Loading section list…</p>
                    ) : scheduleRows.length === 0 ? (
                      <p className="text-blue-700">
                        Could not load sections. You can still type a section code from your challan.
                      </p>
                    ) : (
                      <div className="max-h-56 overflow-y-auto border border-blue-100 rounded bg-white/80 pr-1 text-blue-800">
                        <ul className="divide-y divide-blue-100">
                          {scheduleRows.map((row) => (
                            <li key={row.section} className="py-1 px-1.5 flex gap-2 justify-between">
                              <span>
                                <strong>{row.section}</strong>
                                <span className="text-blue-700"> — {row.offense}</span>
                              </span>
                              <span className="text-blue-600 shrink-0 whitespace-nowrap">
                                max {formatCurrency(row.max_fine)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <p className="text-blue-700 mt-2">
                      Type in the field below for suggestions, or pick from the list. Your challan may cite a
                      section not in this schedule — you can still enter it manually.
                    </p>
                  </div>
                )}
                <div className="space-y-2">
                  {sections.map((s, i) => (
                    <div key={i} className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Section (e.g. 184)"
                        value={s.section}
                        onChange={(e) => updateSection(i, "section", e.target.value)}
                        className="flex-1 rounded-md border bg-background px-3 py-2 text-sm"
                        list="section-suggestions"
                        autoComplete="off"
                      />
                      <input
                        type="number"
                        placeholder="Amount (Rs)"
                        value={s.amount || ""}
                        onChange={(e) => updateSection(i, "amount", Number(e.target.value))}
                        className="w-28 rounded-md border bg-background px-3 py-2 text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => removeSection(i)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <datalist id="section-suggestions" key={state}>
                  {scheduleRows.map((row) => (
                    <option key={row.section} value={row.section} label={row.offense} />
                  ))}
                </datalist>
                <button
                  type="button"
                  onClick={addSection}
                  className="mt-2 flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  <Plus className="h-3 w-3" /> Add section
                </button>
              </div>

              {error && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {loading ? "Validating..." : "Validate Challan"}
              </button>
            </form>
          </div>

          {/* Results */}
          <div className="rounded-xl border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Validation Result</h2>
            {!result ? (
              <div className="flex flex-col items-center justify-center h-60 text-muted-foreground">
                <FileSearch className="h-12 w-12 mb-3 opacity-20" />
                <p className="text-sm text-center">
                  Enter challan details and click validate to see results.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {(() => {
                  const hasUnknown = result.section_analysis.some(
                    (a) => a.valid_range?.min == null && a.valid_range?.max == null
                  );
                  if (result.has_overcharge) {
                    return (
                      <div className="flex items-center gap-2 rounded-lg p-3 bg-red-50 text-red-800 border border-red-200">
                        <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                        <span className="font-medium">
                          Overcharge Detected: {formatCurrency(result.overcharge_amount)}
                        </span>
                      </div>
                    );
                  }
                  if (hasUnknown) {
                    return (
                      <div className="flex items-center gap-2 rounded-lg p-3 bg-amber-50 text-amber-800 border border-amber-200">
                        <HelpCircle className="h-5 w-5 flex-shrink-0" />
                        <span className="font-medium">
                          Could not verify — unknown section(s)
                        </span>
                      </div>
                    );
                  }
                  return (
                    <div className="flex items-center gap-2 rounded-lg p-3 bg-green-50 text-green-800 border border-green-200">
                      <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
                      <span className="font-medium">All fines are within the official range</span>
                    </div>
                  );
                })()}

                {result.total_valid_fine > 0 && (
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="rounded-lg border p-3">
                      <div className="text-lg font-bold">{formatCurrency(result.total_charged)}</div>
                      <div className="text-xs text-muted-foreground">Charged</div>
                    </div>
                    <div className="rounded-lg border p-3">
                      <div className="text-lg font-bold text-green-600">{formatCurrency(result.total_valid_fine)}</div>
                      <div className="text-xs text-muted-foreground">Valid Fine</div>
                    </div>
                    <div className="rounded-lg border p-3">
                      <div className={`text-lg font-bold ${result.overcharge_amount > 0 ? "text-red-600" : ""}`}>
                        {formatCurrency(result.overcharge_amount)}
                      </div>
                      <div className="text-xs text-muted-foreground">Overcharge</div>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  {result.section_analysis.map((a, i) => {
                    const isUnknown = a.valid_range?.min == null && a.valid_range?.max == null;
                    let borderClass = "";
                    let badge = null;
                    if (a.is_overcharged) {
                      borderClass = "border-red-200 bg-red-50/50";
                      badge = <span className="text-xs text-red-600 font-medium px-1.5 py-0.5 rounded bg-red-100">OVERCHARGED</span>;
                    } else if (isUnknown) {
                      borderClass = "border-amber-200 bg-amber-50/50";
                      badge = <span className="text-xs text-amber-700 font-medium px-1.5 py-0.5 rounded bg-amber-100">UNKNOWN</span>;
                    } else {
                      borderClass = "border-green-200 bg-green-50/50";
                      badge = <span className="text-xs text-green-700 font-medium px-1.5 py-0.5 rounded bg-green-100">VALID</span>;
                    }

                    return (
                      <div key={i} className={`rounded-lg border p-3 ${borderClass}`}>
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-sm">Section {a.section}</span>
                          {badge}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">{a.offense}</p>
                        {!isUnknown && a.valid_range?.max != null && (
                          <p className="text-xs mt-1">
                            Charged: <strong>{formatCurrency(a.charged_amount)}</strong>
                            {" | "}Official max: <strong>{formatCurrency(a.valid_range.max)}</strong>
                          </p>
                        )}
                        <p className="text-xs mt-1 text-muted-foreground">{a.note}</p>
                      </div>
                    );
                  })}
                </div>

                <div className={`rounded-lg p-3 ${
                  result.has_overcharge ? "bg-red-50 border border-red-200" :
                  !result.is_valid ? "bg-amber-50 border border-amber-200" :
                  "bg-muted"
                }`}>
                  <p className="text-sm font-medium">Recommendation</p>
                  <p className="text-sm text-muted-foreground mt-0.5">{result.recommended_action}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
