'use client';

import { useParams } from 'next/navigation';
import {
  AlertCircle,
  BarChart3,
  BookOpen,
  FileText,
  Layers,
  Loader2,
  MessageSquare,
  RefreshCw,
  Search,
  Zap,
} from 'lucide-react';
import type { Draft, DraftApproveRequest, DraftType } from '@applypilot/shared-types';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { ApplicationStatusBadge } from '@/components/application-status-badge';
import { FitScoreCard } from '@/components/fit-score-card';
import { RequirementMatchList } from '@/components/requirement-match-list';
import { EvidencePanel } from '@/components/evidence-panel';
import { DraftBundleTabs } from '@/components/draft-bundle-tabs';
import { GraphRunTimeline } from '@/components/graph-run-timeline';

import {
  useApplication,
  useAnalyzeApplication,
  useAnalysis,
  useEvidence,
  useDrafts,
  useApproveDraft,
  useRegenerateSection,
  useGenerateDrafts,
  useGraphRuns,
} from '@/lib/hooks';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function LoadingSkeletonBlock() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
      <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}

function AnalyzePrompt({ onAnalyze, isPending }: { onAnalyze: () => void; isPending: boolean }) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed p-12 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-muted">
        <Search className="size-5 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium">No analysis yet</p>
        <p className="text-sm text-muted-foreground">
          Run an analysis to see fit score, requirement matches, and evidence.
        </p>
      </div>
      <Button onClick={onAnalyze} disabled={isPending} className="gap-2">
        {isPending ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Analyzing…
          </>
        ) : (
          <>
            <Zap className="size-4" aria-hidden="true" />
            Analyze Now
          </>
        )}
      </Button>
    </div>
  );
}

const INTERVIEW_DRAFT_TYPES: DraftType[] = [
  'interview_talking_points',
  'self_introduction',
  'salary_response',
];

const INTERVIEW_DRAFT_LABELS: Record<DraftType, string> = {
  interview_talking_points: 'Interview Talking Points',
  self_introduction: 'Self Introduction',
  salary_response: 'Salary Response',
  recruiter_reply: 'Recruiter Reply',
  cover_email: 'Cover Email',
  resume_summary: 'Resume Summary',
  resume_bullets: 'Resume Bullets',
};

function InterviewPrepContent({ drafts }: { drafts: Draft[] }) {
  const interviewDrafts = drafts.filter((d) => INTERVIEW_DRAFT_TYPES.includes(d.type));

  if (interviewDrafts.length === 0) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed p-12 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-muted">
          <MessageSquare className="size-5 text-muted-foreground" aria-hidden="true" />
        </div>
        <div className="flex flex-col gap-1">
          <p className="text-sm font-medium">No interview materials yet</p>
          <p className="text-sm text-muted-foreground">
            Generate drafts first to populate interview talking points, self-introduction, and
            salary response.
          </p>
        </div>
      </div>
    );
  }

  // Keep the latest version per type
  const latestByType = new Map<DraftType, Draft>();
  for (const draft of interviewDrafts) {
    const existing = latestByType.get(draft.type);
    if (!existing || draft.version > existing.version) {
      latestByType.set(draft.type, draft);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {INTERVIEW_DRAFT_TYPES.map((type) => {
        const draft = latestByType.get(type);
        if (!draft) return null;
        return (
          <Card key={type}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{INTERVIEW_DRAFT_LABELS[type]}</CardTitle>
              <CardDescription>v{draft.version} &middot; {draft.status}</CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="whitespace-pre-wrap font-sans text-sm text-foreground leading-relaxed">
                {draft.body}
              </pre>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Overview tab helpers
// ---------------------------------------------------------------------------

interface OverviewCountRow {
  label: string;
  count: number;
  colorClass: string;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ApplicationDetailPage() {
  const params = useParams();
  const id = params.id as string;

  // Queries
  const appQuery = useApplication(id);
  const analysisQuery = useAnalysis(id);
  const evidenceQuery = useEvidence(id);
  const draftsQuery = useDrafts(id);
  const graphRunsQuery = useGraphRuns(id);

  // Mutations
  const analyzeMutation = useAnalyzeApplication();
  const generateDraftsMutation = useGenerateDrafts();
  const approveDraftMutation = useApproveDraft();
  const regenerateSectionMutation = useRegenerateSection();

  // Derived state
  const app = appQuery.data;
  const isAnalyzed = app?.status !== 'saved';
  const isAnalyzing = analyzeMutation.isPending;

  function handleAnalyze() {
    analyzeMutation.mutate(id);
  }

  function handleGenerateDrafts() {
    generateDraftsMutation.mutate(id);
  }

  function handleApprove(req: DraftApproveRequest) {
    approveDraftMutation.mutate({ id, body: req });
  }

  function handleEdit(draft: Draft) {
    approveDraftMutation.mutate({
      id,
      body: { draft_id: draft.id, edited_body: draft.body },
    });
  }

  function handleRegenerate(type: DraftType) {
    regenerateSectionMutation.mutate({ id, body: { type } });
  }

  // ---------------------------------------------------------------------------
  // Header loading state
  // ---------------------------------------------------------------------------
  if (appQuery.isLoading) {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-5 w-40" />
        </div>
        <LoadingSkeletonBlock />
      </div>
    );
  }

  if (appQuery.isError || !app) {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <ErrorState
          message={
            appQuery.error instanceof Error
              ? appQuery.error.message
              : 'Failed to load application.'
          }
        />
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  const displayTitle = app.role_title ?? 'Untitled Role';
  const displayCompany = app.company_name ?? 'Unknown Company';

  // Counts for overview
  const analysis = analysisQuery.data;
  const overviewCounts: OverviewCountRow[] = analysis
    ? [
        {
          label: 'Strong matches',
          count: analysis.items.filter((i) => i.match_level === 'strong').length,
          colorClass: 'text-success',
        },
        {
          label: 'Partial matches',
          count: analysis.items.filter((i) => i.match_level === 'partial').length,
          colorClass: 'text-warning',
        },
        {
          label: 'Weak / Missing',
          count: analysis.items.filter(
            (i) => i.match_level === 'weak' || i.match_level === 'missing',
          ).length,
          colorClass: 'text-destructive',
        },
        {
          label: 'Red flags',
          count: analysis.red_flags.length,
          colorClass: 'text-destructive',
        },
      ]
    : [];

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      {/* ------------------------------------------------------------------ */}
      {/* Page header                                                          */}
      {/* ------------------------------------------------------------------ */}
      <header className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{displayTitle}</h1>
            <ApplicationStatusBadge status={app.status} />
          </div>
          <p className="text-sm text-muted-foreground">{displayCompany}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Analyze / Re-analyze */}
          <Button
            data-testid="analyze-button"
            size="sm"
            variant={isAnalyzed ? 'outline' : 'default'}
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="gap-2"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                Analyzing…
              </>
            ) : isAnalyzed ? (
              <>
                <RefreshCw className="size-4" aria-hidden="true" />
                Re-analyze
              </>
            ) : (
              <>
                <Zap className="size-4" aria-hidden="true" />
                Analyze
              </>
            )}
          </Button>

          {/* Generate Drafts shortcut */}
          <Button
            size="sm"
            variant="outline"
            onClick={handleGenerateDrafts}
            disabled={generateDraftsMutation.isPending}
            className="gap-2"
          >
            {generateDraftsMutation.isPending ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                Generating…
              </>
            ) : (
              <>
                <FileText className="size-4" aria-hidden="true" />
                Generate Drafts
              </>
            )}
          </Button>
        </div>

        {/* Mutation error banners */}
        {analyzeMutation.isError && (
          <ErrorState
            message={
              analyzeMutation.error instanceof Error
                ? analyzeMutation.error.message
                : 'Analysis failed. Please try again.'
            }
          />
        )}
        {generateDraftsMutation.isError && (
          <ErrorState
            message={
              generateDraftsMutation.error instanceof Error
                ? generateDraftsMutation.error.message
                : 'Draft generation failed. Please try again.'
            }
          />
        )}
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* Tabs                                                                 */}
      {/* ------------------------------------------------------------------ */}
      <Tabs defaultValue="overview">
        <TabsList className="h-auto flex-wrap gap-1">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="job-details">Job Details</TabsTrigger>
          <TabsTrigger data-testid="tab-fit" value="fit-analysis">
            <BarChart3 className="size-3.5" aria-hidden="true" />
            Fit Analysis
          </TabsTrigger>
          <TabsTrigger data-testid="tab-evidence" value="evidence">
            <Search className="size-3.5" aria-hidden="true" />
            Evidence
          </TabsTrigger>
          <TabsTrigger data-testid="tab-drafts" value="drafts">
            <FileText className="size-3.5" aria-hidden="true" />
            Drafts
          </TabsTrigger>
          <TabsTrigger value="interview-prep">
            <MessageSquare className="size-3.5" aria-hidden="true" />
            Interview Prep
          </TabsTrigger>
          <TabsTrigger value="run-logs">
            <Layers className="size-3.5" aria-hidden="true" />
            Run Logs
          </TabsTrigger>
        </TabsList>

        {/* --------------------------------------------------------- */}
        {/* Overview                                                    */}
        {/* --------------------------------------------------------- */}
        <TabsContent value="overview" className="flex flex-col gap-6 pt-4">
          {analysisQuery.isLoading ? (
            <LoadingSkeletonBlock />
          ) : analysisQuery.isError ? (
            <ErrorState
              message={
                analysisQuery.error instanceof Error
                  ? analysisQuery.error.message
                  : 'Failed to load analysis.'
              }
            />
          ) : !analysis ? (
            <AnalyzePrompt onAnalyze={handleAnalyze} isPending={isAnalyzing} />
          ) : (
            <>
              {/* Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">{analysis.summary}</p>
                </CardContent>
              </Card>

              {/* Counts */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {overviewCounts.map((row) => (
                  <Card key={row.label}>
                    <CardContent className="flex flex-col gap-1 pt-6">
                      <span className={`text-3xl font-bold tabular-nums ${row.colorClass}`}>
                        {row.count}
                      </span>
                      <span className="text-xs text-muted-foreground">{row.label}</span>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>

        {/* --------------------------------------------------------- */}
        {/* Job Details                                                 */}
        {/* --------------------------------------------------------- */}
        <TabsContent value="job-details" className="flex flex-col gap-6 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Extracted Fields</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {(
                  [
                    ['Company', app.company_name],
                    ['Role', app.role_title],
                    ['Job URL', app.job_url],
                    ['Work Arrangement', app.work_arrangement],
                    ['Salary', app.salary_text],
                    ['Timezone', app.timezone_text],
                    ['Recruiter Name', app.recruiter_name],
                    ['Recruiter Email', app.recruiter_email],
                  ] as [string, string | null | undefined][]
                ).map(([label, value]) => (
                  <div key={label} className="flex flex-col gap-0.5">
                    <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      {label}
                    </dt>
                    <dd className="text-sm">
                      {value ? (
                        label === 'Job URL' ? (
                          <a
                            href={value}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline-offset-4 hover:underline"
                          >
                            {value}
                          </a>
                        ) : (
                          value
                        )
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="size-4" aria-hidden="true" />
                Raw Job Post
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-[600px] overflow-y-auto whitespace-pre-wrap rounded-md bg-muted p-4 font-mono text-xs leading-relaxed">
                {app.raw_job_post}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>

        {/* --------------------------------------------------------- */}
        {/* Fit Analysis                                                */}
        {/* --------------------------------------------------------- */}
        <TabsContent value="fit-analysis" className="flex flex-col gap-6 pt-4">
          {analysisQuery.isLoading ? (
            <LoadingSkeletonBlock />
          ) : analysisQuery.isError ? (
            <ErrorState
              message={
                analysisQuery.error instanceof Error
                  ? analysisQuery.error.message
                  : 'Failed to load fit analysis.'
              }
            />
          ) : !analysis ? (
            <AnalyzePrompt onAnalyze={handleAnalyze} isPending={isAnalyzing} />
          ) : (
            <>
              <FitScoreCard analysis={analysis} />
              <RequirementMatchList analysis={analysis} />
            </>
          )}
        </TabsContent>

        {/* --------------------------------------------------------- */}
        {/* Evidence                                                    */}
        {/* --------------------------------------------------------- */}
        <TabsContent value="evidence" className="pt-4">
          {evidenceQuery.isLoading ? (
            <LoadingSkeletonBlock />
          ) : evidenceQuery.isError ? (
            <ErrorState
              message={
                evidenceQuery.error instanceof Error
                  ? evidenceQuery.error.message
                  : 'Failed to load evidence.'
              }
            />
          ) : !isAnalyzed && !evidenceQuery.data?.length ? (
            <AnalyzePrompt onAnalyze={handleAnalyze} isPending={isAnalyzing} />
          ) : (
            <EvidencePanel evidence={evidenceQuery.data ?? []} />
          )}
        </TabsContent>

        {/* --------------------------------------------------------- */}
        {/* Drafts                                                      */}
        {/* --------------------------------------------------------- */}
        <TabsContent value="drafts" className="flex flex-col gap-4 pt-4">
          {/* Error banners for draft mutations */}
          {approveDraftMutation.isError && (
            <ErrorState
              message={
                approveDraftMutation.error instanceof Error
                  ? approveDraftMutation.error.message
                  : 'Approval failed. Please try again.'
              }
            />
          )}
          {regenerateSectionMutation.isError && (
            <ErrorState
              message={
                regenerateSectionMutation.error instanceof Error
                  ? regenerateSectionMutation.error.message
                  : 'Regeneration failed. Please try again.'
              }
            />
          )}

          {draftsQuery.isLoading ? (
            <LoadingSkeletonBlock />
          ) : draftsQuery.isError ? (
            <ErrorState
              message={
                draftsQuery.error instanceof Error
                  ? draftsQuery.error.message
                  : 'Failed to load drafts.'
              }
            />
          ) : !draftsQuery.data?.length ? (
            <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed p-12 text-center">
              <div className="flex size-12 items-center justify-center rounded-full bg-muted">
                <FileText className="size-5 text-muted-foreground" aria-hidden="true" />
              </div>
              <div className="flex flex-col gap-1">
                <p className="text-sm font-medium">No drafts yet</p>
                <p className="text-sm text-muted-foreground">
                  Generate AI-powered cover letters, resume bullets, and more.
                </p>
              </div>
              <Button
                onClick={handleGenerateDrafts}
                disabled={generateDraftsMutation.isPending}
                className="gap-2"
              >
                {generateDraftsMutation.isPending ? (
                  <>
                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                    Generating…
                  </>
                ) : (
                  <>
                    <FileText className="size-4" aria-hidden="true" />
                    Generate Drafts
                  </>
                )}
              </Button>
            </div>
          ) : (
            <DraftBundleTabs
              drafts={draftsQuery.data}
              onApprove={handleApprove}
              onEdit={handleEdit}
              onRegenerate={handleRegenerate}
            />
          )}
        </TabsContent>

        {/* --------------------------------------------------------- */}
        {/* Interview Prep                                              */}
        {/* --------------------------------------------------------- */}
        <TabsContent value="interview-prep" className="pt-4">
          {draftsQuery.isLoading ? (
            <LoadingSkeletonBlock />
          ) : draftsQuery.isError ? (
            <ErrorState
              message={
                draftsQuery.error instanceof Error
                  ? draftsQuery.error.message
                  : 'Failed to load interview materials.'
              }
            />
          ) : (
            <InterviewPrepContent drafts={draftsQuery.data ?? []} />
          )}
        </TabsContent>

        {/* --------------------------------------------------------- */}
        {/* Run Logs                                                    */}
        {/* --------------------------------------------------------- */}
        <TabsContent value="run-logs" className="pt-4">
          {graphRunsQuery.isLoading ? (
            <LoadingSkeletonBlock />
          ) : graphRunsQuery.isError ? (
            <ErrorState
              message={
                graphRunsQuery.error instanceof Error
                  ? graphRunsQuery.error.message
                  : 'Failed to load run logs.'
              }
            />
          ) : (
            <GraphRunTimeline runs={graphRunsQuery.data ?? []} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
