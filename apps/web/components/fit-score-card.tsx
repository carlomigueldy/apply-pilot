import type { FitAnalysis } from "@applypilot/shared-types";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface FitScoreCardProps {
  analysis: FitAnalysis;
  className?: string;
}

function scoreColor(score: number): string {
  if (score >= 75) return "text-success";
  if (score >= 50) return "text-warning";
  return "text-destructive";
}

function scoreRingColor(score: number): string {
  if (score >= 75) return "stroke-success";
  if (score >= 50) return "stroke-warning";
  return "stroke-destructive";
}

function scoreLabel(score: number): string {
  if (score >= 80) return "Excellent fit";
  if (score >= 65) return "Good fit";
  if (score >= 50) return "Moderate fit";
  if (score >= 35) return "Weak fit";
  return "Poor fit";
}

/** Circular score gauge using an SVG ring. */
function ScoreRing({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const filled = (score / 100) * circumference;

  return (
    <svg
      viewBox="0 0 100 100"
      className={cn("size-28 -rotate-90", className)}
      aria-hidden="true"
    >
      {/* Track */}
      <circle
        cx="50"
        cy="50"
        r={radius}
        fill="none"
        strokeWidth="8"
        className="stroke-muted"
      />
      {/* Fill */}
      <circle
        cx="50"
        cy="50"
        r={radius}
        fill="none"
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={circumference - filled}
        className={cn("transition-all duration-500", scoreRingColor(score))}
      />
    </svg>
  );
}

export function FitScoreCard({ analysis, className }: FitScoreCardProps) {
  const { fit_score, summary, red_flags, positioning_strategy } = analysis;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Fit Analysis</CardTitle>
        <CardDescription>
          AI-generated assessment based on your profile
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {/* Score row */}
        <div className="flex items-center gap-6">
          <div className="relative flex shrink-0 items-center justify-center">
            <ScoreRing score={fit_score} />
            <div className="absolute flex flex-col items-center">
              <span
                data-testid="fit-score"
                className={cn(
                  "text-3xl font-bold tabular-nums leading-none",
                  scoreColor(fit_score),
                )}
              >
                {fit_score}
              </span>
              <span className="mt-0.5 text-[10px] text-muted-foreground">
                / 100
              </span>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <p className="text-sm font-semibold">{scoreLabel(fit_score)}</p>
            <p className="text-sm text-muted-foreground">{summary}</p>
          </div>
        </div>

        {/* Positioning strategy */}
        {positioning_strategy && (
          <div className="rounded-md border bg-muted/40 p-4">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Positioning Strategy
            </p>
            <p className="text-sm">{positioning_strategy}</p>
          </div>
        )}

        {/* Red flags */}
        {red_flags.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-destructive">
              Red Flags
            </p>
            <ul className="flex flex-col gap-1.5">
              {red_flags.map((flag, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-muted-foreground"
                >
                  <span
                    aria-hidden="true"
                    className="mt-1.5 size-1.5 shrink-0 rounded-full bg-destructive"
                  />
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
