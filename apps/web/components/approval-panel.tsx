"use client";

import { useState } from "react";
import { ThumbsUp } from "lucide-react";
import type { Draft, DraftApproveRequest } from "@applypilot/shared-types";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export interface ApprovalPanelProps {
  draft: Draft;
  onApprove: (req: DraftApproveRequest) => void | Promise<void>;
  className?: string;
}

export function ApprovalPanel({ draft, onApprove, className }: ApprovalPanelProps) {
  const [editedBody, setEditedBody] = useState(draft.body);
  const [notes, setNotes] = useState("");
  const [isApproving, setIsApproving] = useState(false);

  const bodyChanged = editedBody !== draft.body;

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await onApprove({
        draft_id: draft.id,
        edited_body: bodyChanged ? editedBody : undefined,
        notes: notes.trim() || undefined,
      });
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className={className}>
      <div className="flex flex-col gap-4">
        {/* Editable draft body */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="approval-body">Draft Content</Label>
          <Textarea
            id="approval-body"
            value={editedBody}
            onChange={(e) => setEditedBody(e.target.value)}
            className="min-h-[200px] font-mono text-sm"
          />
          {bodyChanged && (
            <p className="text-xs text-muted-foreground">
              You have made edits — these will be saved with the approval.
            </p>
          )}
        </div>

        {/* Notes */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="approval-notes">Notes (optional)</Label>
          <Textarea
            id="approval-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add any reviewer notes here…"
            className="min-h-[80px]"
          />
        </div>

        {/* Approve button */}
        <div className="flex justify-end">
          <Button
            data-testid="approve-draft-button"
            onClick={() => void handleApprove()}
            disabled={isApproving}
            className="gap-2"
          >
            <ThumbsUp className="size-4" aria-hidden="true" />
            {isApproving ? "Approving…" : "Approve Draft"}
          </Button>
        </div>
      </div>
    </div>
  );
}
