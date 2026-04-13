"use client";

import { useState, useCallback, useEffect } from "react";
import { getLanguageLabel } from "@/lib/constants";

const STORAGE_KEY = "preferred_language";
const MANUAL_KEY = "language_manually_set";
const LANGUAGE_CHANGE_EVENT = "app:language-change";

interface LanguageChangeDetail {
  code: string;
  manual: boolean;
}

export function useLanguage() {
  const [language, setLanguageState] = useState<string>(() => {
    if (typeof window === "undefined") return "en";
    return localStorage.getItem(STORAGE_KEY) || "en";
  });

  const [manuallySet, setManuallySet] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(MANUAL_KEY) === "true";
  });

  const setLanguage = useCallback((code: string, manual = false) => {
    setLanguageState(code);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, code);
      if (manual) {
        localStorage.setItem(MANUAL_KEY, "true");
        setManuallySet(true);
      }
      window.dispatchEvent(
        new CustomEvent(LANGUAGE_CHANGE_EVENT, { detail: { code, manual } })
      );
    }
  }, []);

  const clearManualLanguage = useCallback(() => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(MANUAL_KEY);
    }
    setManuallySet(false);
  }, []);

  useEffect(() => {
    const handleChange = (e: Event) => {
      const { code, manual } = (e as CustomEvent<LanguageChangeDetail>).detail;
      setLanguageState(code);
      if (manual) setManuallySet(true);
    };
    window.addEventListener(LANGUAGE_CHANGE_EVENT, handleChange);
    return () => window.removeEventListener(LANGUAGE_CHANGE_EVENT, handleChange);
  }, []);

  return {
    language,
    setLanguage,
    manuallySet,
    clearManualLanguage,
    languageLabel: getLanguageLabel(language),
  };
}
