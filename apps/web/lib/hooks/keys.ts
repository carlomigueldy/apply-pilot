'use client';

/**
 * Centralised TanStack Query key factory.
 *
 * All query keys are defined here so invalidation targets are consistent
 * across the entire application.
 */

export const queryKeys = {
  // Applications
  applications: {
    all: () => ["applications"] as const,
    lists: () => ["applications", "list"] as const,
    detail: (id: string) => ["applications", "detail", id] as const,
    analysis: (id: string) => ["applications", "analysis", id] as const,
    evidence: (id: string) => ["applications", "evidence", id] as const,
    drafts: (id: string) => ["applications", "drafts", id] as const,
  },

  // Profile
  profile: {
    all: () => ["profile"] as const,
    items: () => ["profile", "items"] as const,
    search: (query: string) => ["profile", "search", query] as const,
  },

  // Graph runs
  graphRuns: {
    all: () => ["graphRuns"] as const,
    byApplication: (applicationId: string) =>
      ["graphRuns", "byApplication", applicationId] as const,
    detail: (id: string) => ["graphRuns", "detail", id] as const,
  },

  // Settings
  settings: {
    all: () => ["settings"] as const,
  },
} as const;
