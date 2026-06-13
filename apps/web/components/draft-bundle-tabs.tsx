"use client";

import { RefreshCw } from "lucide-react";
import type { Draft, DraftApproveRequest, DraftType } from "@applypilot/shared-types";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ApprovalPanel } from "@/components/approval-panel";
import { DraftEditor } from "@/components/draft-editor";

const DRAFT_TYPE_LABELS: Record<DraftType, string> = {
  recruiter_reply: "Recruiter Reply",
  cover_email: "Cover Email",
  resume_summary: "Resume Summary",
  resume_bullets: "Resume Bullets",
  interview_talking_points: "Talking Points",
  salary_response: "Salary Response",
  self_introduction: "Introduction",
};

export interface DraftBundleTabsProps {
  drafts: Draft[];
  onApprove: (req: DraftApproveRequest) => void | Promise<void>;
  onRegenerate: (type: DraftType) => void | Promise<void>;
  onEdit: (draft: Draft) => void;
  className?: string;
}

export function DraftBundleTabs({
  drafts,
  onApprove,
  onRegenerate,
  onEdit,
  className,
}: DraftBundleTabsProps) {
  if (drafts.length === 0) {
    return (
      <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">
        {`No drafts generated yet. Use the "Generate Drafts" action to create them.`}
      </div>
    );
  }

  // Group drafts by type (keep latest version per type at top).
  const grouped = drafts.reduce<Map<DraftType, Draft[]>>((acc, draft) => {
    const bucket = acc.get(draft.type) ?? [];
    bucket.push(draft);
    acc.set(draft.type, bucket);
    return acc;
  }, new Map());

  // Stable ordered list of unique types present in the drafts.
  const types = Array.from(grouped.keys());

  const defaultTab = types[0];
  if (!defaultTab) return null;

  return (
    <Tabs defaultValue={defaultTab} className={className}>
      <TabsList className="flex-wrap gap-1 h-auto">
        {types.map((type) => {
          const bucket = grouped.get(type) ?? [];
          const pending = bucket.filter(
            (d) => d.status === "generated" || d.status === "needs_review",
          ).length;
          return (
            <TabsTrigger key={type} value={type} className="gap-1.5">
              {DRAFT_TYPE_LABELS[type]}
              {pending > 0 && (
                <Badge variant="secondary" className="px-1 py-0 text-[10px]">
                  {pending}
                </Badge>
              )}
            </TabsTrigger>
          );
        })}
      </TabsList>

      {types.map((type) => {
        const bucket = (grouped.get(type) ?? []).sort(
          (a, b) => b.version - a.version,
        );
        const latest = bucket[0];

        return (
          <TabsContent key={type} value={type} data-testid="draft-item" className="flex flex-col gap-4">
            {/* Header row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  {DRAFT_TYPE_LABELS[type]}
                </span>
                {latest && (
                  <Badge variant="outline" className="text-xs">
                    v{latest.version}
                  </Badge>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => void onRegenerate(type)}
              >
                <RefreshCw className="size-3.5" aria-hidden="true" />
                Regenerate
              </Button>
            </div>

            {latest ? (
              <>
                {/* Editable area */}
                <DraftEditor
                  draft={latest}
                  onSave={(body) => {
                    onEdit({ ...latest, body });
                  }}
                />
                {/* Approval */}
                <ApprovalPanel draft={latest} onApprove={onApprove} />
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No draft available for this type.</p>
            )}
          </TabsContent>
        );
      })}
    </Tabs>
  );
}
