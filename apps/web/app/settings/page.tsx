'use client';

import {
  AlertCircle,
  Bot,
  BrainCircuit,
  CheckCircle2,
  FlaskConical,
  Server,
  XCircle,
} from 'lucide-react';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useSettings } from '@/lib/hooks';

// ---------------------------------------------------------------------------
// Helper primitives
// ---------------------------------------------------------------------------

function SettingRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{children}</span>
    </div>
  );
}

function SettingRowSkeleton() {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-4 w-24" />
    </div>
  );
}

function BooleanChip({ value, labels = ['Enabled', 'Disabled'] }: { value: boolean; labels?: [string, string] }) {
  if (value) {
    return (
      <span className="inline-flex items-center gap-1.5 text-sm font-medium text-success">
        <CheckCircle2 className="size-3.5" aria-hidden="true" />
        {labels[0]}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
      <XCircle className="size-3.5" aria-hidden="true" />
      {labels[1]}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const { data: settings, isPending, isError, error } = useSettings();

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Provider configuration, preferences, and account details.
        </p>
      </header>

      {/* Error state */}
      {isError && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <div className="flex flex-col gap-0.5">
            <span className="font-medium">Failed to load settings</span>
            <span className="text-xs text-muted-foreground">
              {error instanceof Error ? error.message : 'Unknown error'}
            </span>
          </div>
        </div>
      )}

      {/* Provider Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bot className="size-4 text-muted-foreground" aria-hidden="true" />
            <CardTitle className="text-base">Provider configuration</CardTitle>
          </div>
          <CardDescription>
            Active LLM and embedding backend used for analysis and drafting.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y">
            {isPending ? (
              <>
                <SettingRowSkeleton />
                <SettingRowSkeleton />
                <SettingRowSkeleton />
                <SettingRowSkeleton />
              </>
            ) : settings ? (
              <>
                <SettingRow label="Provider mode">
                  <Badge
                    variant={settings.provider_is_local ? 'secondary' : 'outline'}
                    className="gap-1.5 font-mono text-xs"
                  >
                    <span
                      aria-hidden="true"
                      className={
                        settings.provider_is_local
                          ? 'size-1.5 rounded-full bg-success'
                          : 'size-1.5 rounded-full bg-warning'
                      }
                    />
                    {settings.provider_is_local ? 'local' : 'cloud'}
                  </Badge>
                </SettingRow>

                <SettingRow label="LLM provider">
                  <span className="font-mono">{settings.llm_provider}</span>
                </SettingRow>

                <SettingRow label="LLM model">
                  <span className="font-mono">{settings.llm_model}</span>
                </SettingRow>

                <SettingRow label="Embedding provider">
                  <span className="font-mono">{settings.embedding_provider}</span>
                </SettingRow>

                <SettingRow label="Embedding model">
                  <span className="font-mono">{settings.embedding_model}</span>
                </SettingRow>
              </>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {/* Test mode / environment */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FlaskConical className="size-4 text-muted-foreground" aria-hidden="true" />
            <CardTitle className="text-base">Environment</CardTitle>
          </div>
          <CardDescription>
            Runtime environment and testing mode status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y">
            {isPending ? (
              <>
                <SettingRowSkeleton />
                <SettingRowSkeleton />
                <SettingRowSkeleton />
              </>
            ) : settings ? (
              <>
                <SettingRow label="App name">
                  <span>{settings.app_name}</span>
                </SettingRow>

                <SettingRow label="Environment">
                  <Badge variant="outline" className="font-mono text-xs">
                    {settings.app_env}
                  </Badge>
                </SettingRow>

                <SettingRow label="Test mode">
                  <BooleanChip
                    value={settings.test_mode}
                    labels={['Active', 'Inactive']}
                  />
                </SettingRow>
              </>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {/* Preferences (static / placeholder) */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BrainCircuit className="size-4 text-muted-foreground" aria-hidden="true" />
            <CardTitle className="text-base">Preferences</CardTitle>
          </div>
          <CardDescription>
            Your job-search preferences used to personalise drafts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y">
            <SettingRow label="Target salary">
              <span className="text-muted-foreground">Not configured</span>
            </SettingRow>

            <SettingRow label="Preferred tone">
              <span className="text-muted-foreground">Not configured</span>
            </SettingRow>

            <SettingRow label="Work arrangement">
              <span className="text-muted-foreground">Not configured</span>
            </SettingRow>

            <SettingRow label="Timezone">
              <span className="text-muted-foreground">Not configured</span>
            </SettingRow>
          </div>

          <p className="mt-4 text-xs text-muted-foreground">
            Preferences are managed via your profile. Editing will be available
            in a future release.
          </p>
        </CardContent>
      </Card>

      {/* Infrastructure */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Server className="size-4 text-muted-foreground" aria-hidden="true" />
            <CardTitle className="text-base">Infrastructure</CardTitle>
          </div>
          <CardDescription>
            Backend connection and API details.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y">
            <SettingRow label="API base URL">
              <span className="font-mono text-xs text-muted-foreground">
                {process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}
              </span>
            </SettingRow>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
