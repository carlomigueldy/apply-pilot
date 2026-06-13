/**
 * API client functions for the settings endpoint.
 */

import type { AppSettings } from "@applypilot/shared-types";
import { apiGet } from "./client";

export function getSettings(): Promise<AppSettings> {
  return apiGet<AppSettings>("/settings");
}
