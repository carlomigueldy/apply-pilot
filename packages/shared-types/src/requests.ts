/**
 * Request and response payload types mirroring the ApplyPilot API contract.
 * Field names are snake_case to match the JSON bodies expected/returned by
 * the FastAPI / Pydantic backend exactly.
 */

import type { JsonObject, RetrievedEvidence } from "./entities.js";
import type {
  DraftLength,
  DraftType,
  ProfileItemType,
  Tone,
  WorkArrangement,
} from "./enums.js";

/** Mirrors JobApplicationCreate (raw_job_post min length 30). */
export interface JobApplicationCreate {
  raw_job_post: string;
  company_name?: string | null;
  role_title?: string | null;
  job_url?: string | null;
  salary_text?: string | null;
  work_arrangement?: WorkArrangement | null;
  timezone_text?: string | null;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
}

/** Mirrors JobApplicationUpdate (all fields optional). */
export interface JobApplicationUpdate {
  company_name?: string | null;
  role_title?: string | null;
  job_url?: string | null;
  raw_job_post?: string | null;
  salary_text?: string | null;
  work_arrangement?: WorkArrangement | null;
  timezone_text?: string | null;
  recruiter_name?: string | null;
  recruiter_email?: string | null;
}

/** Mirrors ProfileItemCreate. */
export interface ProfileItemCreate {
  type: ProfileItemType;
  title: string;
  body: string;
  item_metadata?: JsonObject | null;
}

/** Mirrors ProfileItemUpdate (all fields optional). */
export interface ProfileItemUpdate {
  type?: ProfileItemType;
  title?: string;
  body?: string;
  item_metadata?: JsonObject | null;
}

/** Mirrors ProfileSearchRequest. */
export interface ProfileSearchRequest {
  query: string;
  top_k?: number;
  types?: ProfileItemType[] | null;
}

/** Mirrors ProfileSearchResponse. */
export interface ProfileSearchResponse {
  results: RetrievedEvidence[];
}

/** Mirrors AnalyzeResponse. */
export interface AnalyzeResponse {
  application_id: string;
  graph_run_id: string;
  status: string;
}

/** Mirrors DraftApproveRequest. */
export interface DraftApproveRequest {
  draft_id: string;
  edited_body?: string | null;
  notes?: string | null;
}

/** Mirrors RegenerateSectionRequest. */
export interface RegenerateSectionRequest {
  type: DraftType;
  tone?: Tone | null;
  length?: DraftLength | null;
  instructions?: string | null;
}
