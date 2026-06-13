import type { EvidenceMatch } from "@applypilot/shared-types";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface EvidencePanelProps {
  evidence: EvidenceMatch[];
  className?: string;
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  );
}

export function EvidencePanel({ evidence, className }: EvidencePanelProps) {
  if (evidence.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Evidence Matches</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No evidence matches found. Run analysis to populate this panel.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Evidence Matches</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col divide-y">
          {evidence.map((match) => (
            <li
              key={`${match.requirement_id}-${match.evidence_chunk_id}`}
              data-testid="evidence-item"
              className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0"
            >
              <p className="text-sm">{match.summary}</p>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                <ConfidenceBar confidence={match.confidence} />
                <span className="font-mono text-[10px] text-muted-foreground">
                  chunk: {match.evidence_chunk_id.slice(0, 8)}…
                </span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  item: {match.profile_item_id.slice(0, 8)}…
                </span>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
