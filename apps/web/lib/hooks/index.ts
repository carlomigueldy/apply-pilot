'use client';

/**
 * TanStack Query hooks for all ApplyPilot API resources.
 *
 * Mutation hooks automatically invalidate related queries on success so that
 * stale data is never displayed after a write operation.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  analyzeApplication,
  approveDraft,
  createApplication,
  generateDrafts,
  getAnalysis,
  getDrafts,
  getEvidence,
  listApplications,
  getApplication,
  regenerateSection,
  updateApplication,
} from "@/lib/api/applications";
import {
  createProfileItem,
  deleteProfileItem,
  listProfileItems,
  regenerateEmbeddings,
  searchProfile,
  updateProfileItem,
} from "@/lib/api/profile";
import { getGraphRun, listGraphRuns } from "@/lib/api/graphRuns";
import { getSettings } from "@/lib/api/settings";

import type {
  DraftApproveRequest,
  JobApplicationCreate,
  JobApplicationUpdate,
  ProfileItemCreate,
  ProfileItemUpdate,
  ProfileSearchRequest,
  RegenerateSectionRequest,
} from "@applypilot/shared-types";

import { queryKeys } from "./keys";

// ---------------------------------------------------------------------------
// Applications
// ---------------------------------------------------------------------------

export function useApplications() {
  return useQuery({
    queryKey: queryKeys.applications.lists(),
    queryFn: listApplications,
  });
}

export function useApplication(id: string) {
  return useQuery({
    queryKey: queryKeys.applications.detail(id),
    queryFn: () => getApplication(id),
    enabled: Boolean(id),
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: JobApplicationCreate) => createApplication(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.lists(),
      });
    },
  });
}

export function useUpdateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: JobApplicationUpdate }) =>
      updateApplication(id, body),
    onSuccess: (_data, { id }) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.detail(id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.lists(),
      });
    },
  });
}

export function useAnalyzeApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => analyzeApplication(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.detail(id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.analysis(id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.evidence(id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.drafts(id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.graphRuns.byApplication(id),
      });
    },
  });
}

export function useGenerateDrafts() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => generateDrafts(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.drafts(id),
      });
    },
  });
}

export function useDrafts(id: string) {
  return useQuery({
    queryKey: queryKeys.applications.drafts(id),
    queryFn: () => getDrafts(id),
    enabled: Boolean(id),
  });
}

export function useApproveDraft() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: DraftApproveRequest;
    }) => approveDraft(id, body),
    onSuccess: (_data, { id }) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.drafts(id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.detail(id),
      });
    },
  });
}

export function useRegenerateSection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: RegenerateSectionRequest;
    }) => regenerateSection(id, body),
    onSuccess: (_data, { id }) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.applications.drafts(id),
      });
    },
  });
}

export function useAnalysis(id: string) {
  return useQuery({
    queryKey: queryKeys.applications.analysis(id),
    queryFn: () => getAnalysis(id),
    enabled: Boolean(id),
  });
}

export function useEvidence(id: string) {
  return useQuery({
    queryKey: queryKeys.applications.evidence(id),
    queryFn: () => getEvidence(id),
    enabled: Boolean(id),
  });
}

// ---------------------------------------------------------------------------
// Profile
// ---------------------------------------------------------------------------

export function useProfileItems() {
  return useQuery({
    queryKey: queryKeys.profile.items(),
    queryFn: listProfileItems,
  });
}

export function useCreateProfileItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ProfileItemCreate) => createProfileItem(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.profile.items(),
      });
    },
  });
}

export function useUpdateProfileItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ProfileItemUpdate }) =>
      updateProfileItem(id, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.profile.items(),
      });
    },
  });
}

export function useDeleteProfileItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteProfileItem(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.profile.items(),
      });
    },
  });
}

export function useRegenerateEmbeddings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => regenerateEmbeddings(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.profile.items(),
      });
    },
  });
}

export function useProfileSearch(request: ProfileSearchRequest | null) {
  return useQuery({
    queryKey: queryKeys.profile.search(request?.query ?? ""),
    queryFn: () => searchProfile(request!),
    enabled: Boolean(request?.query),
  });
}

// ---------------------------------------------------------------------------
// Graph Runs
// ---------------------------------------------------------------------------

export function useGraphRuns(applicationId: string) {
  return useQuery({
    queryKey: queryKeys.graphRuns.byApplication(applicationId),
    queryFn: () => listGraphRuns(applicationId),
    enabled: Boolean(applicationId),
  });
}

export function useGraphRun(id: string) {
  return useQuery({
    queryKey: queryKeys.graphRuns.detail(id),
    queryFn: () => getGraphRun(id),
    enabled: Boolean(id),
  });
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings.all(),
    queryFn: getSettings,
  });
}

export { queryKeys };
