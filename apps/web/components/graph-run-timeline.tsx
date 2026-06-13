import type { GraphRun, GraphRunStatus } from "@applypilot/shared-types";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const STATUS_CONFIG: Record<
  GraphRunStatus,
  { label: string; variant: BadgeProps["variant"]; dotClass: string }
> = {
  running: {
    label: "Running",
    variant: "warning",
    dotClass: "bg-warning animate-pulse",
  },
  completed: {
    label: "Completed",
    variant: "success",
    dotClass: "bg-success",
  },
  failed: {
    label: "Failed",
    variant: "destructive",
    dotClass: "bg-destructive",
  },
  interrupted: {
    label: "Interrupted",
    variant: "secondary",
    dotClass: "bg-muted-foreground",
  },
};

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTs(ts: string): string {
  return new Date(ts).toLocaleTimeString();
}

interface NodeTimingRow {
  name: string;
  durationMs: number | null;
}

function parseNodeTimings(timings: Record<string, unknown>): NodeTimingRow[] {
  return Object.entries(timings).map(([name, value]) => {
    let durationMs: number | null = null;
    if (typeof value === "number") {
      durationMs = value;
    } else if (value && typeof value === "object") {
      const obj = value as Record<string, unknown>;
      if (typeof obj.duration_ms === "number") {
        durationMs = obj.duration_ms;
      }
    }
    return { name, durationMs };
  });
}

function GraphRunCard({ run }: { run: GraphRun }) {
  const statusCfg = STATUS_CONFIG[run.status];
  const nodeRows =
    run.node_timings ? parseNodeTimings(run.node_timings) : [];

  return (
    <li className="flex flex-col gap-3 rounded-lg border p-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className={cn("size-2 shrink-0 rounded-full", statusCfg.dotClass)}
          />
          <span className="text-sm font-medium">{run.graph_name}</span>
        </div>
        <Badge variant={statusCfg.variant}>{statusCfg.label}</Badge>
      </div>

      {/* Timestamps */}
      <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
        <div>
          <span className="font-medium">Started: </span>
          {formatTs(run.started_at)}
        </div>
        {run.completed_at && (
          <div>
            <span className="font-medium">Completed: </span>
            {formatTs(run.completed_at)}
          </div>
        )}
        {run.current_node && (
          <div className="col-span-2">
            <span className="font-medium">Current node: </span>
            <code className="rounded bg-muted px-1 py-0.5 font-mono">
              {run.current_node}
            </code>
          </div>
        )}
      </div>

      {/* Node timings */}
      {nodeRows.length > 0 && (
        <div className="flex flex-col gap-1">
          <p className="text-xs font-medium text-muted-foreground">
            Node timings
          </p>
          <ol className="flex flex-col gap-1">
            {nodeRows.map((row, idx) => (
              <li key={idx} className="flex items-center gap-2 text-xs">
                <span
                  aria-hidden="true"
                  className="size-1.5 shrink-0 rounded-full bg-muted-foreground"
                />
                <code className="font-mono">{row.name}</code>
                {row.durationMs != null && (
                  <span className="ml-auto text-muted-foreground">
                    {formatDuration(row.durationMs)}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Error */}
      {run.status === "failed" && run.error_payload && (
        <div className="rounded-md bg-destructive/10 p-3 text-xs text-destructive">
          {typeof run.error_payload.message === "string"
            ? run.error_payload.message
            : "An error occurred during the graph run."}
        </div>
      )}
    </li>
  );
}

export interface GraphRunTimelineProps {
  runs: GraphRun[];
  className?: string;
}

export function GraphRunTimeline({ runs, className }: GraphRunTimelineProps) {
  if (runs.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Graph Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No graph runs yet. Trigger an analysis to start.
          </p>
        </CardContent>
      </Card>
    );
  }

  const sorted = [...runs].sort(
    (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
  );

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Graph Runs</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col gap-3" aria-label="Graph run timeline">
          {sorted.map((run) => (
            <GraphRunCard key={run.id} run={run} />
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
