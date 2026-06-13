import type { ApplicationStatus } from "@applypilot/shared-types";

import { Badge, type BadgeProps } from "@/components/ui/badge";

interface StatusConfig {
  label: string;
  variant: BadgeProps["variant"];
}

const STATUS_MAP: Record<ApplicationStatus, StatusConfig> = {
  saved: { label: "Saved", variant: "secondary" },
  analyzed: { label: "Analyzed", variant: "outline" },
  drafted: { label: "Drafted", variant: "default" },
  ready_to_apply: { label: "Ready", variant: "success" },
  applied: { label: "Applied", variant: "success" },
  interviewing: { label: "Interviewing", variant: "warning" },
  offer: { label: "Offer", variant: "success" },
  rejected: { label: "Rejected", variant: "destructive" },
  archived: { label: "Archived", variant: "secondary" },
};

export interface ApplicationStatusBadgeProps {
  status: ApplicationStatus;
  className?: string;
}

export function ApplicationStatusBadge({
  status,
  className,
}: ApplicationStatusBadgeProps) {
  const config = STATUS_MAP[status] ?? {
    label: status,
    variant: "secondary" as const,
  };

  return (
    <Badge data-testid="application-status" variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}
