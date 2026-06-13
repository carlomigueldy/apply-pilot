/**
 * API client functions for job application endpoints.
 */

import type {
  AnalyzeResponse,
  ApplicationListItem,
  Draft,
  DraftApproveRequest,
  EvidenceMatch,
  FitAnalysis,
  JobApplication,
  JobApplicationCreate,
  JobApplicationUpdate,
  RegenerateSectionRequest,
} from "@applypilot/shared-types";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";

export function listApplications(): Promise<ApplicationListItem[]> {
  return apiGet<ApplicationListItem[]>("/applications");
}

export function getApplication(id: string): Promise<JobApplication> {
  return apiGet<JobApplication>(`/applications/${id}`);
}

export function createApplication(
  body: JobApplicationCreate,
): Promise<JobApplication> {
  return apiPost<JobApplication, JobApplicationCreate>("/applications", body);
}

export function updateApplication(
  id: string,
  body: JobApplicationUpdate,
): Promise<JobApplication> {
  return apiPatch<JobApplication, JobApplicationUpdate>(
    `/applications/${id}`,
    body,
  );
}

export function analyzeApplication(id: string): Promise<AnalyzeResponse> {
  return apiPost<AnalyzeResponse>(`/applications/${id}/analyze`);
}

export function generateDrafts(id: string): Promise<Draft[]> {
  return apiPost<Draft[]>(`/applications/${id}/generate-drafts`);
}

export function approveDraft(
  id: string,
  body: DraftApproveRequest,
): Promise<Draft> {
  return apiPost<Draft, DraftApproveRequest>(
    `/applications/${id}/approve-draft`,
    body,
  );
}

export function regenerateSection(
  id: string,
  body: RegenerateSectionRequest,
): Promise<Draft> {
  return apiPost<Draft, RegenerateSectionRequest>(
    `/applications/${id}/regenerate-section`,
    body,
  );
}

export function getAnalysis(id: string): Promise<FitAnalysis> {
  return apiGet<FitAnalysis>(`/applications/${id}/analysis`);
}

export function getEvidence(id: string): Promise<EvidenceMatch[]> {
  return apiGet<EvidenceMatch[]>(`/applications/${id}/evidence`);
}

export function getDrafts(id: string): Promise<Draft[]> {
  return apiGet<Draft[]>(`/applications/${id}/drafts`);
}

// Re-export apiDelete for callers that need it
export { apiDelete };
