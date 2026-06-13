'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Clock,
  FileCheck,
  FileText,
  Inbox,
  PlusCircle,
  TrendingUp,
} from 'lucide-react';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { buttonVariants } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ApplicationTable } from '@/components/application-table';
import { ProviderBadge } from '@/components/provider-badge';
import { useApplications, useSettings } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import type { ApplicationListItem } from '@applypilot/shared-types';

const RECENT_LIMIT = 5;

function StatCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2 pb-2">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="size-4 rounded" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-12" />
        <Skeleton className="mt-1 h-3 w-36" />
      </CardContent>
    </Card>
  );
}

function RecentTableSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      {[0, 1, 2, 3].map((row) => (
        <div
          key={row}
          className="flex items-center gap-4 rounded-lg border p-4"
        >
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-6 w-16 rounded-md" />
          <Skeleton className="h-6 w-10 rounded-md" />
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();

  const {
    data: applications,
    isPending: appsLoading,
    isError: appsError,
    error: appsErrorValue,
  } = useApplications();

  const {
    data: settings,
    isPending: settingsLoading,
  } = useSettings();

  const stats = useMemo(() => {
    if (!applications) {
      return { total: 0, needsReview: 0, highFit: 0 };
    }

    const total = applications.length;

    const needsReview = applications.filter(
      (a) => a.status === 'drafted',
    ).length;

    const highFit = applications.filter(
      (a) => a.fit_score !== null && a.fit_score >= 75,
    ).length;

    return { total, needsReview, highFit };
  }, [applications]);

  const recentApplications = useMemo<ApplicationListItem[]>(() => {
    if (!applications) return [];
    return [...applications]
      .sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      )
      .slice(0, RECENT_LIMIT);
  }, [applications]);

  const isProviderLocal =
    settings?.provider_is_local ??
    (settings?.llm_provider === 'fake' ||
      settings?.llm_provider === 'ollama' ||
      true);

  function handleRowClick(app: ApplicationListItem) {
    router.push(`/applications/${app.id}`);
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
      {/* Page header */}
      <header className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Your job-application pipeline at a glance.
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          {settingsLoading ? (
            <Skeleton className="h-5 w-28 rounded-full" />
          ) : settings ? (
            <ProviderBadge
              provider={settings.llm_provider}
              isLocal={isProviderLocal}
            />
          ) : null}

          <Link
            href="/applications/new"
            className={cn(buttonVariants({ size: 'sm' }))}
          >
            <PlusCircle className="mr-1.5 size-4" aria-hidden="true" />
            New application
          </Link>
        </div>
      </header>

      {/* Stat cards */}
      <section
        aria-label="Pipeline summary"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        {appsLoading ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <Card>
              <CardHeader className="flex-row items-center justify-between gap-2 pb-2">
                <CardDescription>Total applications</CardDescription>
                <FileText
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-semibold tabular-nums">
                  {stats.total}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Tracked across all statuses
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center justify-between gap-2 pb-2">
                <CardDescription>Drafts needing review</CardDescription>
                <FileCheck
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-semibold tabular-nums">
                  {stats.needsReview}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Awaiting your approval
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center justify-between gap-2 pb-2">
                <CardDescription>High-fit opportunities</CardDescription>
                <TrendingUp
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-semibold tabular-nums">
                  {stats.highFit}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Fit score of 75 or higher
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center justify-between gap-2 pb-2">
                <CardDescription>Active pipeline</CardDescription>
                <Clock
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-semibold tabular-nums">
                  {applications?.filter(
                    (a) =>
                      a.status === 'analyzed' ||
                      a.status === 'drafted' ||
                      a.status === 'ready_to_apply' ||
                      a.status === 'applied' ||
                      a.status === 'interviewing',
                  ).length ?? 0}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  In progress (not archived or rejected)
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </section>

      {/* Recent applications */}
      <section aria-label="Recent applications">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div className="flex flex-col gap-1">
              <CardTitle>Recent applications</CardTitle>
              <CardDescription>
                Your most recently updated applications.
              </CardDescription>
            </div>
            <Link
              href="/applications"
              className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}
            >
              View all
            </Link>
          </CardHeader>

          <CardContent>
            {appsLoading ? (
              <RecentTableSkeleton />
            ) : appsError ? (
              <div className="flex flex-col items-center gap-2 py-12 text-center">
                <p className="text-sm font-medium text-destructive">
                  Failed to load applications
                </p>
                <p className="text-xs text-muted-foreground">
                  {appsErrorValue instanceof Error
                    ? appsErrorValue.message
                    : 'Unknown error'}
                </p>
              </div>
            ) : recentApplications.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
                <div className="flex size-12 items-center justify-center rounded-full bg-muted">
                  <Inbox
                    className="size-6 text-muted-foreground"
                    aria-hidden="true"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <p className="text-sm font-medium">No applications yet</p>
                  <p className="text-sm text-muted-foreground">
                    Add a job post to start tracking and drafting with
                    ApplyPilot.
                  </p>
                </div>
                <Link
                  href="/applications/new"
                  className={cn(buttonVariants({ size: 'sm' }))}
                >
                  <PlusCircle className="mr-1.5 size-4" aria-hidden="true" />
                  Add your first application
                </Link>
              </div>
            ) : (
              <ApplicationTable
                applications={recentApplications}
                onRowClick={handleRowClick}
              />
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
