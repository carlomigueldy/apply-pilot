/**
 * String-literal union types mirroring the ApplyPilot API contract enums.
 * Values MUST match the backend string values exactly.
 */

export type ProfileItemType =
  | "role"
  | "project"
  | "skill"
  | "achievement"
  | "testimonial"
  | "salary"
  | "interview_answer"
  | "preference";

export type ApplicationStatus =
  | "saved"
  | "analyzed"
  | "drafted"
  | "ready_to_apply"
  | "applied"
  | "interviewing"
  | "offer"
  | "rejected"
  | "archived";

export type DraftType =
  | "recruiter_reply"
  | "cover_email"
  | "resume_summary"
  | "resume_bullets"
  | "interview_talking_points"
  | "salary_response"
  | "self_introduction";

export type DraftStatus =
  | "generated"
  | "needs_review"
  | "approved"
  | "rejected"
  | "edited";

export type RequirementCategory =
  | "frontend"
  | "backend"
  | "ai"
  | "web3"
  | "devops"
  | "soft_skill"
  | "domain"
  | "other";

export type RequirementPriority = "must_have" | "nice_to_have" | "unknown";

export type MatchLevel = "strong" | "partial" | "weak" | "missing" | "unknown";

export type WorkArrangement = "remote" | "hybrid" | "onsite" | "unknown";

export type GraphRunStatus =
  | "running"
  | "completed"
  | "failed"
  | "interrupted";

export type ReviewDecisionType = "approve" | "edit" | "reject" | "regenerate";

export type Tone = "direct" | "warm_professional" | "confident" | "concise";

export type DraftLength = "short" | "medium" | "detailed";
