import type { FitAnalysis, FitAnalysisItem, MatchLevel } from "@applypilot/shared-types";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const MATCH_LEVEL_CONFIG: Record<
  MatchLevel,
  { label: string; className: string }
> = {
  strong: {
    label: "Strong",
    className: "border-transparent bg-success text-success-foreground",
  },
  partial: {
    label: "Partial",
    className: "border-transparent bg-warning text-warning-foreground",
  },
  weak: {
    label: "Weak",
    className: "border-transparent bg-muted text-muted-foreground",
  },
  missing: {
    label: "Missing",
    className: "border-transparent bg-destructive text-destructive-foreground",
  },
  unknown: {
    label: "Unknown",
    className: "border text-muted-foreground",
  },
};

function MatchLevelBadge({ level }: { level: MatchLevel }) {
  const config = MATCH_LEVEL_CONFIG[level];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        config.className,
      )}
    >
      {config.label}
    </span>
  );
}

function MatchItem({ item }: { item: FitAnalysisItem }) {
  return (
    <li className="flex flex-col gap-2 rounded-md border p-3">
      <div className="flex items-center justify-between gap-2">
        <MatchLevelBadge level={item.match_level} />
        <span className="text-xs text-muted-foreground">
          {Math.round(item.confidence * 100)}% confidence
        </span>
      </div>
      <p className="text-sm text-muted-foreground">{item.explanation}</p>
      {item.evidence_chunk_ids.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {item.evidence_chunk_ids.map((id) => (
            <Badge key={id} variant="outline" className="font-mono text-[10px]">
              {id.slice(0, 8)}…
            </Badge>
          ))}
        </div>
      )}
    </li>
  );
}

export interface RequirementMatchListProps {
  analysis: FitAnalysis;
  className?: string;
}

export function RequirementMatchList({
  analysis,
  className,
}: RequirementMatchListProps) {
  const { items } = analysis;

  if (items.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Requirement Matches</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No requirement matches available.
          </p>
        </CardContent>
      </Card>
    );
  }

  const sorted = [...items].sort((a, b) => {
    const order: MatchLevel[] = ["strong", "partial", "weak", "missing", "unknown"];
    return order.indexOf(a.match_level) - order.indexOf(b.match_level);
  });

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Requirement Matches</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col gap-3">
          {sorted.map((item) => (
            <MatchItem key={item.requirement_id} item={item} />
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
