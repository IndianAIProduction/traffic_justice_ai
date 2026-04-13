export const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Andaman and Nicobar Islands",
  "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi",
  "Jammu and Kashmir",
  "Ladakh",
  "Lakshadweep",
  "Puducherry",
] as const;

export const LANGUAGES = [
  { code: "en", label: "English", nativeLabel: "English" },
  { code: "hi", label: "Hindi", nativeLabel: "हिन्दी" },
  { code: "mr", label: "Marathi", nativeLabel: "मराठी" },
  { code: "ta", label: "Tamil", nativeLabel: "தமிழ்" },
  { code: "te", label: "Telugu", nativeLabel: "తెలుగు" },
  { code: "kn", label: "Kannada", nativeLabel: "ಕನ್ನಡ" },
  { code: "ml", label: "Malayalam", nativeLabel: "മലയാളം" },
  { code: "gu", label: "Gujarati", nativeLabel: "ગુજરાતી" },
  { code: "bn", label: "Bengali", nativeLabel: "বাংলা" },
  { code: "pa", label: "Punjabi", nativeLabel: "ਪੰਜਾਬੀ" },
  { code: "or", label: "Odia", nativeLabel: "ଓଡ଼ିଆ" },
  { code: "as", label: "Assamese", nativeLabel: "অসমীয়া" },
  { code: "ur", label: "Urdu", nativeLabel: "اردو" },
  { code: "ne", label: "Nepali", nativeLabel: "नेपाली" },
  { code: "kok", label: "Konkani", nativeLabel: "कोंकणी" },
] as const;

export const STATE_DEFAULT_LANGUAGE: Record<string, string> = {
  "Andhra Pradesh": "te",
  "Arunachal Pradesh": "en",
  "Assam": "as",
  "Bihar": "hi",
  "Chhattisgarh": "hi",
  "Goa": "kok",
  "Gujarat": "gu",
  "Haryana": "hi",
  "Himachal Pradesh": "hi",
  "Jharkhand": "hi",
  "Karnataka": "kn",
  "Kerala": "ml",
  "Madhya Pradesh": "hi",
  "Maharashtra": "mr",
  "Manipur": "en",
  "Meghalaya": "en",
  "Mizoram": "en",
  "Nagaland": "en",
  "Odisha": "or",
  "Punjab": "pa",
  "Rajasthan": "hi",
  "Sikkim": "ne",
  "Tamil Nadu": "ta",
  "Telangana": "te",
  "Tripura": "bn",
  "Uttar Pradesh": "hi",
  "Uttarakhand": "hi",
  "West Bengal": "bn",
  "Andaman and Nicobar Islands": "hi",
  "Chandigarh": "pa",
  "Dadra and Nagar Haveli and Daman and Diu": "gu",
  "Delhi": "hi",
  "Jammu and Kashmir": "ur",
  "Ladakh": "hi",
  "Lakshadweep": "ml",
  "Puducherry": "ta",
};

export function getLanguageLabel(code: string): string {
  return LANGUAGES.find((l) => l.code === code)?.nativeLabel || "English";
}

export const STATE_NAME_ALIASES: Record<string, string> = {
  "NCT of Delhi": "Delhi",
  "National Capital Territory of Delhi": "Delhi",
  "Orissa": "Odisha",
  "Pondicherry": "Puducherry",
  "Uttaranchal": "Uttarakhand",
  "Chattisgarh": "Chhattisgarh",
  "Andaman & Nicobar Islands": "Andaman and Nicobar Islands",
  "Andaman & Nicobar": "Andaman and Nicobar Islands",
  "Andaman and Nicobar": "Andaman and Nicobar Islands",
  "Dadra & Nagar Haveli and Daman & Diu": "Dadra and Nagar Haveli and Daman and Diu",
  "Dadra and Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
  "Daman and Diu": "Dadra and Nagar Haveli and Daman and Diu",
  "Jammu & Kashmir": "Jammu and Kashmir",
  "J&K": "Jammu and Kashmir",
};

export function matchIndianState(name: string): string | null {
  if (!name) return null;
  const trimmed = name.trim();

  const exact = INDIAN_STATES.find((s) => s === trimmed);
  if (exact) return exact;

  const alias = STATE_NAME_ALIASES[trimmed];
  if (alias) return alias;

  const lower = trimmed.toLowerCase();
  const caseInsensitive = INDIAN_STATES.find((s) => s.toLowerCase() === lower);
  if (caseInsensitive) return caseInsensitive;

  const partial = INDIAN_STATES.find(
    (s) => s.toLowerCase().includes(lower) || lower.includes(s.toLowerCase())
  );
  return partial ?? null;
}
