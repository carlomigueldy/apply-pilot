"use client";

import type { ApplicationListItem } from "@applypilot/shared-types";

import { cn } from "@/lib/utils";
import { ApplicationStatusBadge } from "@/components/application-status-badge";

export interface ApplicationTableProps {
  applications: ApplicationListItem[];
  onRowClick?: (application: ApplicationListItem) => void;
}

export function ApplicationTable({
  applications,
  onRowClick,
}: ApplicationTableProps) {
  if (applications.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">
        No applications yet. Add one to get started.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Company
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Role
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Status
            </th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">
              Fit Score
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Created
            </th>
          </tr>
        </thead>
        <tbody>
          {applications.map((app) => (
            <tr
              key={app.id}
              className={cn(
                "border-b transition-colors last:border-0",
                onRowClick
                  ? "cursor-pointer hover:bg-muted/50"
                  : "cursor-default",
              )}
              onClick={() => onRowClick?.(app)}
            >
              <td className="px-4 py-3 font-medium">
                {app.company_name ?? (
                  <span className="italic text-muted-foreground">Unknown</span>
                )}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {app.role_title ?? (
                  <span className="italic">—</span>
                )}
              </td>
              <td className="px-4 py-3">
                <ApplicationStatusBadge status={app.status} />
              </td>
              <td className="px-4 py-3 text-right">
                {app.fit_score != null ? (
                  <span className="font-mono font-medium">
                    {app.fit_score}%
                  </span>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {new Date(app.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
