/**
 * API client functions for profile item endpoints.
 */

import type {
  ProfileItem,
  ProfileItemCreate,
  ProfileItemUpdate,
  ProfileSearchRequest,
  ProfileSearchResponse,
} from "@applypilot/shared-types";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";

export function listProfileItems(): Promise<ProfileItem[]> {
  return apiGet<ProfileItem[]>("/profile/items");
}

export function createProfileItem(
  body: ProfileItemCreate,
): Promise<ProfileItem> {
  return apiPost<ProfileItem, ProfileItemCreate>("/profile/items", body);
}

export function updateProfileItem(
  id: string,
  body: ProfileItemUpdate,
): Promise<ProfileItem> {
  return apiPatch<ProfileItem, ProfileItemUpdate>(`/profile/items/${id}`, body);
}

export function deleteProfileItem(id: string): Promise<void> {
  return apiDelete<void>(`/profile/items/${id}`);
}

export function regenerateEmbeddings(id: string): Promise<ProfileItem> {
  return apiPost<ProfileItem>(`/profile/items/${id}/regenerate-embeddings`);
}

export function searchProfile(
  body: ProfileSearchRequest,
): Promise<ProfileSearchResponse> {
  return apiPost<ProfileSearchResponse, ProfileSearchRequest>(
    "/profile/search",
    body,
  );
}
