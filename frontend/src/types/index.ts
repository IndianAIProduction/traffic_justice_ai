export interface User {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  state: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Case {
  id: string;
  user_id: string;
  case_type: "traffic_stop" | "challan" | "misconduct";
  status: "open" | "in_progress" | "resolved" | "closed" | "escalated";
  title: string;
  description: string | null;
  state: string | null;
  city: string | null;
  location: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChallanSection {
  section: string;
  amount: number;
}

export interface SectionAnalysis {
  section: string;
  offense: string;
  charged_amount: number;
  valid_range: { min: number | null; max: number | null };
  is_overcharged: boolean;
  note: string;
}

export interface ChallanValidation {
  is_valid: boolean;
  has_overcharge: boolean;
  section_analysis: SectionAnalysis[];
  total_valid_fine: number;
  total_charged: number;
  overcharge_amount: number;
  recommended_action: string;
}

export interface LegalResponse {
  answer: string;
  sections_cited: string[];
  fine_range: { min: number; max: number } | null;
  recommended_action: string;
  disclaimer: string;
}

export interface Evidence {
  id: string;
  case_id: string;
  file_type: "audio" | "video" | "image" | "document";
  file_name: string;
  file_hash: string;
  is_analyzed: boolean;
  transcription: string | null;
  analysis: Record<string, unknown>;
  uploaded_at: string;
}

export interface MisconductFlag {
  id: string;
  flag_type: string;
  severity: number;
  description: string;
  timestamp_in_media: string | null;
  confidence_score: number | null;
  raw_quote: string | null;
}

export interface SubmissionDetails {
  state_name: string;
  portal_name: string;
  portal_url: string;
  complaint_form_url: string | null;
  email_sent: boolean;
  email_recipients: string[];
  email_error: string | null;
  pdf_generated: boolean;
  pdf_path: string | null;
  portal_automation_status: string;
  portal_screenshot_path: string | null;
  helplines: Record<string, string>;
  channels_attempted: string[];
  channels_succeeded: string[];
  submitted_at: string | null;
}

export interface Complaint {
  id: string;
  case_id: string;
  complaint_type: string;
  portal_name: string | null;
  status: "drafted" | "submitted" | "acknowledged" | "in_progress" | "resolved" | "escalated";
  draft_text: string | null;
  final_text: string | null;
  portal_complaint_id: string | null;
  portal_url: string | null;
  submission_screenshot_path: string | null;
  user_consent: boolean;
  submitted_at: string | null;
  resolved_at: string | null;
  created_at: string;
  submission_details: SubmissionDetails | null;
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  type: string;
  city: string;
}

export interface OverchargePattern {
  section: string;
  offense: string;
  charged: number;
  valid_max: number | null;
  overcharge: number;
}
