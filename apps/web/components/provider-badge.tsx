import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface ProviderBadgeProps {
  /** LLM provider name, e.g. "fake", "ollama", "openai", "anthropic". */
  provider?: string;
  /** Whether the provider runs locally (fake/ollama) vs. a hosted cloud API. */
  isLocal?: boolean;
  className?: string;
}

/**
 * Compact badge that surfaces the active LLM provider and whether it runs
 * locally. Placeholder values are used until the `/health` endpoint is wired up
 * in a later phase.
 */
export function ProviderBadge({
  provider = "fake",
  isLocal = true,
  className,
}: ProviderBadgeProps) {
  return (
    <Badge
      variant={isLocal ? "secondary" : "outline"}
      className={cn("gap-1.5 font-mono", className)}
    >
      <span
        aria-hidden="true"
        className={cn(
          "size-1.5 rounded-full",
          isLocal ? "bg-success" : "bg-warning",
        )}
      />
      <span>{provider}</span>
      <span className="text-muted-foreground">
        {isLocal ? "local" : "cloud"}
      </span>
    </Badge>
  );
}
