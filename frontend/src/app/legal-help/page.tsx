"use client";

import { useState, useRef, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { legalApi } from "@/lib/api";
import { formatCurrency, extractErrorMessage } from "@/lib/utils";
import type { LegalResponse } from "@/types";
import ReactMarkdown from "react-markdown";
import { Send, Scale, AlertCircle, RotateCcw, MapPin, Loader2, X, MessageSquare } from "lucide-react";
import { INDIAN_STATES, STATE_DEFAULT_LANGUAGE } from "@/lib/constants";
import { useLanguage } from "@/hooks/useLanguage";
import { useAutoLocation } from "@/hooks/useAutoLocation";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: LegalResponse;
}

const VEHICLE_OPTIONS = [
  { id: "two_wheeler", emoji: "\u{1F3CD}\uFE0F", label: "Bike / Scooter", sublabel: "Two-wheeler" },
  { id: "four_wheeler", emoji: "\u{1F697}", label: "Car / SUV", sublabel: "Four-wheeler" },
  { id: "heavy", emoji: "\u{1F69B}", label: "Truck / Bus", sublabel: "Heavy / Commercial" },
] as const;

type VehicleType = (typeof VEHICLE_OPTIONS)[number]["id"] | "general" | null;

const VEHICLE_BADGE: Record<string, { emoji: string; short: string }> = {
  two_wheeler: { emoji: "\u{1F3CD}\uFE0F", short: "Bike" },
  four_wheeler: { emoji: "\u{1F697}", short: "Car" },
  heavy: { emoji: "\u{1F69B}", short: "Truck" },
  general: { emoji: "\u{1F4AC}", short: "General" },
};

export default function LegalHelpPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [state, setState] = useState("Maharashtra");
  const [manualCity, setManualCity] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [userManuallySelected, setUserManuallySelected] = useState(false);
  const [vehicleType, setVehicleType] = useState<VehicleType>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { language, setLanguage, manuallySet } = useLanguage();
  const { detectedState, city: detectedCity, detecting, error: locationError, detect } = useAutoLocation(true);

  const city = manualCity || detectedCity || "";
  const chatReady = vehicleType !== null;

  useEffect(() => {
    if (detectedState && !userManuallySelected) {
      setState(detectedState);
      if (!manuallySet) {
        const lang = STATE_DEFAULT_LANGUAGE[detectedState];
        if (lang) setLanguage(lang);
      }
    }
    if (detectedCity && !userManuallySelected) {
      setManualCity(detectedCity);
    }
  }, [detectedState, detectedCity, userManuallySelected, manuallySet, setLanguage]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewChat = () => {
    setMessages([]);
    setThreadId(null);
    setVehicleType(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    const currentThreadId = threadId || crypto.randomUUID();
    if (!threadId) setThreadId(currentThreadId);

    try {
      const { data } = await legalApi.query({
        query: userMsg,
        state,
        city: city || undefined,
        language,
        language_explicit: manuallySet,
        vehicle_type: vehicleType !== "general" ? vehicleType ?? undefined : undefined,
        thread_id: currentThreadId,
      });

      if (data.thread_id) {
        setThreadId(data.thread_id);
      }

      const response = data.response as LegalResponse;
      const answer =
        (typeof response === "object" && response?.answer) ||
        (typeof response === "string" ? response : JSON.stringify(response, null, 2));
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: String(answer), data: typeof response === "object" ? response : undefined },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: extractErrorMessage(err, "Sorry, an error occurred. Please try again.") },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-6 flex flex-col max-w-4xl">
        <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Scale className="h-6 w-6 text-primary" /> Legal Help
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Ask any question about Indian traffic law. AI-powered, grounded in the Motor Vehicles Act.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {chatReady && (
              <button
                onClick={handleNewChat}
                className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm hover:bg-accent transition"
                title="Start new conversation"
              >
                <RotateCcw className="h-3.5 w-3.5" /> New Chat
              </button>
            )}
            {chatReady && vehicleType && VEHICLE_BADGE[vehicleType] && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/5 px-3 py-1 text-sm font-medium text-primary">
                <span>{VEHICLE_BADGE[vehicleType].emoji}</span>
                {VEHICLE_BADGE[vehicleType].short}
                <button
                  onClick={() => { setVehicleType(null); setMessages([]); setThreadId(null); }}
                  className="ml-0.5 rounded-full hover:bg-primary/10 p-0.5 transition"
                  title="Change vehicle"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            <button
              onClick={() => {
                setUserManuallySelected(false);
                detect();
              }}
              disabled={detecting}
              className={`flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm transition ${
                detecting
                  ? "opacity-60 cursor-wait"
                  : detectedState
                    ? "border-green-500/40 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-950/20"
                    : locationError
                      ? "border-orange-500/40 text-orange-700 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-950/20"
                      : "hover:bg-accent"
              }`}
              title={
                detecting
                  ? "Detecting your location..."
                  : locationError
                    ? locationError
                    : "Auto-detect my city & state"
              }
            >
              {detecting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <MapPin className={`h-3.5 w-3.5 ${detectedState ? "text-green-600 dark:text-green-400" : locationError ? "text-orange-500" : ""}`} />
              )}
              {detecting ? "Detecting..." : "Auto Detect"}
            </button>
            <input
              type="text"
              value={manualCity}
              onChange={(e) => {
                setManualCity(e.target.value);
                setUserManuallySelected(true);
              }}
              placeholder="City"
              className="rounded-md border bg-background px-3 py-1.5 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <select
              value={state}
              onChange={(e) => {
                const newState = e.target.value;
                setState(newState);
                setUserManuallySelected(true);
                if (!manuallySet) {
                  const lang = STATE_DEFAULT_LANGUAGE[newState];
                  if (lang) setLanguage(lang);
                }
                setMessages([]);
                setThreadId(null);
                setVehicleType(null);
              }}
              className="rounded-md border bg-background px-3 py-1.5 text-sm"
            >
              {INDIAN_STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Vehicle Selector — shown before chat starts */}
        {!chatReady && (
          <div className="flex-1 rounded-xl border bg-card p-8 mb-4 min-h-[400px] flex flex-col items-center justify-center">
            <Scale className="h-10 w-10 text-primary/30 mb-4" />
            <h2 className="text-xl font-semibold mb-1">Select Your Vehicle</h2>
            <p className="text-sm text-muted-foreground mb-8">
              Fines vary by vehicle type. Select yours for accurate advice.
            </p>

            <div className="grid grid-cols-3 gap-4 w-full max-w-lg mb-6">
              {VEHICLE_OPTIONS.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setVehicleType(v.id)}
                  className="group flex flex-col items-center gap-2 rounded-xl border-2 border-border bg-background p-6 transition-all hover:border-primary hover:shadow-md hover:scale-[1.03] active:scale-[0.98]"
                >
                  <span className="text-5xl transition-transform group-hover:scale-110">
                    {v.emoji}
                  </span>
                  <span className="font-semibold text-sm">{v.label}</span>
                  <span className="text-xs text-muted-foreground">{v.sublabel}</span>
                </button>
              ))}
            </div>

            <button
              onClick={() => setVehicleType("general")}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition"
            >
              <MessageSquare className="h-4 w-4" />
              I just have a general question
            </button>
          </div>
        )}

        {/* Chat Messages — shown after vehicle selected */}
        {chatReady && (
          <>
            <div className="flex-1 rounded-xl border bg-card overflow-y-auto p-4 space-y-4 mb-4 min-h-[400px] max-h-[600px]">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Scale className="h-12 w-12 mb-4 opacity-20" />
                  <p className="text-center">
                    {vehicleType !== "general"
                      ? `${VEHICLE_BADGE[vehicleType!]?.emoji} Vehicle selected. Ask your question about traffic law, fines, or rights.`
                      : "Ask a question about traffic law, your rights during a stop, fine amounts, or complaint procedures."
                    }
                  </p>
                </div>
              )}
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="text-sm prose prose-sm prose-neutral dark:prose-invert max-w-none [&>p]:mb-2 [&>ul]:mb-2 [&>ol]:mb-2 [&>ul]:pl-4 [&>ol]:pl-4">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    )}
                    {msg.data && (
                      <div className="mt-3 space-y-2">
                        {msg.data.sections_cited?.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {msg.data.sections_cited.map((s) => (
                              <span
                                key={s}
                                className="inline-block rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                        {msg.data.fine_range && (
                          <p className="text-xs opacity-80">
                            Fine range: {formatCurrency(msg.data.fine_range.min)} -{" "}
                            {formatCurrency(msg.data.fine_range.max)}
                          </p>
                        )}
                        {msg.data.recommended_action && (
                          <p className="text-xs font-medium opacity-80">
                            Recommended: {msg.data.recommended_action}
                          </p>
                        )}
                        {msg.data.disclaimer && (
                          <div className="flex items-start gap-1 mt-2 pt-2 border-t border-border/50">
                            <AlertCircle className="h-3 w-3 mt-0.5 shrink-0 opacity-60" />
                            <p className="text-[11px] opacity-60">{msg.data.disclaimer}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg p-4">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" />
                      <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce delay-100" />
                      <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about traffic law, fines, rights, procedures..."
                className="flex-1 rounded-md border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={loading}
                autoFocus
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="rounded-md bg-primary px-4 py-3 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </>
        )}
      </main>
      <Footer />
    </div>
  );
}
