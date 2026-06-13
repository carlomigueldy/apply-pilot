/**
 * API client functions for graph-run endpoints.
 */

import type { GraphRun } from "@applypilot/shared-types";
import { apiGet } from "./client";

export function listGraphRuns(applicationId: string): Promise<GraphRun[]> {
  return apiGet<GraphRun[]>(
    `/graph-runs?application_id=${encodeURIComponent(applicationId)}`,
  );
}

export function getGraphRun(id: string): Promise<GraphRun> {
  return apiGet<GraphRun>(`/graph-runs/${id}`);
}
