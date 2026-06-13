"use client";

import { useState } from "react";
import type { Draft } from "@applypilot/shared-types";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export interface DraftEditorProps {
  draft: Draft;
  onSave: (body: string) => void | Promise<void>;
  className?: string;
}

export function DraftEditor({ draft, onSave, className }: DraftEditorProps) {
  const [body, setBody] = useState(draft.body);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(body);
    } finally {
      setIsSaving(false);
    }
  };

  const isDirty = body !== draft.body;

  return (
    <div className={className}>
      <Textarea
        data-testid="draft-edit-textarea"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        className="min-h-[240px] font-mono text-sm"
        aria-label="Draft content"
      />
      <div className="mt-3 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          v{draft.version} &middot; {draft.status}
        </p>
        <Button
          data-testid="draft-save-button"
          size="sm"
          onClick={() => void handleSave()}
          disabled={!isDirty || isSaving}
        >
          {isSaving ? "Saving…" : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}
