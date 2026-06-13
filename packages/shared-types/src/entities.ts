/**
 * Read-model entity interfaces mirroring the ApplyPilot API JSON responses.
 * Field names are snake_case to match the JSON payloads emitted by the
 * FastAPI / Pydantic backend exactly.
 */

import type {
  ApplicationStatus,
  DraftLength,
  DraftStatus,
  DraftType,
  GraphRunStatus,
  MatchLevel,
  ProfileItemType,
  RequirementCategory,
  RequirementPriority,
  Tone,
  WorkArrangement,
} from "./enums.js";

/** Arbitrary JSON object as stored in jsonb metadata columns. */
export type JsonObject = Record<string, unknown>;

/** Mirrors UserRead (users table). */
export interface User {
  id: string;
  name: string | null;
  email: string | null;
  timezone: string | null;
  target_salary_min_usd: number | null;
  target_salary_max_usd: number | null;
  remote_preference: string | null;
  preferred_tone: string | null;
  created_at: string;
  updated_at: string;
}

/** Mirrors ProfileItemRead (profile_items table). */
export interface ProfileItem {
  id: string;
  user_id: string;
  type: ProfileItemType;
  title: string;
  body: string;
  item_metadata: JsonObject | null;
  created_at: string;
  updated_at: string;
}

/** Mirrors RetrievedEvidence (profile semantic search result). */
export interface RetrievedEvidence {
  evidence_chunk_id: string;
  profile_item_id: string;
  title: string;
  snippet: string;
  score: number;
  source_type: string;
}

/** Mirrors JobApplicationRead (job_applications table). */
export interface JobApplication {
  id: string;
  user_id: string;
  company_name: string | null;
  role_title: string | null;
  job_url: string | null;
  raw_job_post: string;
  status: ApplicationStatus;
  work_arrangement: WorkArrangement;
  salary_text: string | null;
  timezone_text: string | null;
  recruiter_name: string | null;
  recruiter_email: string | null;
  created_at: string;
  updated_at: string;
}

/** Mirrors ApplicationListItem (list view projection). */
export interface ApplicationListItem {
  id: string;
  company_name: string | null;
  role_title: string | null;
  status: ApplicationStatus;
  fit_score: number | null;
  created_at: string;
  updated_at: string;
}

/** Mirrors JobRequirement (extracted job requirement). */
export interface JobRequirement {
  id: string;
  text: string;
  category: RequirementCategory;
  priority: RequirementPriority;
}

/** Mirrors EvidenceMatch (requirement -> evidence chunk link). */
export interface EvidenceMatch {
  requirement_id: string;
  profile_item_id: string;
  evidence_chunk_id: string;
  summary: string;
  confidence: number;
}

/** Mirrors FitAnalysisItem (per-requirement fit detail). */
export interface FitAnalysisItem {
  requirement_id: string;
  match_level: MatchLevel;
  explanation: string;
  evidence_chunk_ids: string[];
  confidence: number;
}

/** Mirrors FitAnalysis (overall fit assessment). */
export interface FitAnalysis {
  fit_score: number;
  summary: string;
  items: FitAnalysisItem[];
  red_flags: string[];
  positioning_strategy: string;
}

/** Mirrors DraftRead (drafts table). */
export interface Draft {
  id: string;
  application_id: string;
  type: DraftType;
  title: string;
  body: string;
  status: DraftStatus;
  version: number;
  tone: Tone | null;
  length: DraftLength | null;
  review_notes: string | null;
  created_at: string;
  updated_at: string;
}

/** Mirrors GraphRunRead (graph_runs table). */
export interface GraphRun {
  id: string;
  application_id: string;
  graph_name: string;
  status: GraphRunStatus;
  current_node: string | null;
  node_timings: JsonObject | null;
  input_payload: JsonObject | null;
  output_payload: JsonObject | null;
  error_payload: JsonObject | null;
  model_metadata: JsonObject | null;
  started_at: string;
  completed_at: string | null;
}

/** Mirrors AppSettingsRead (runtime app/provider configuration). */
export interface AppSettings {
  app_env: string;
  app_name: string;
  llm_provider: string;
  llm_model: string;
  embedding_provider: string;
  embedding_model: string;
  test_mode: boolean;
  provider_is_local: boolean;
}
