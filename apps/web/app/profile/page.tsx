'use client';

import React, { useState, useCallback, type FormEvent } from 'react';
import {
  AlertCircle,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import type {
  ProfileItem,
  ProfileItemCreate,
  ProfileItemType,
  ProfileSearchRequest,
  RetrievedEvidence,
} from '@applypilot/shared-types';

import {
  useProfileItems,
  useCreateProfileItem,
  useUpdateProfileItem,
  useDeleteProfileItem,
  useRegenerateEmbeddings,
  useProfileSearch,
} from '@/lib/hooks';
import { ProfileItemEditor } from '@/components/profile-item-editor';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

// ─── Constants ────────────────────────────────────────────────────────────────

const ALL_TYPES: ProfileItemType[] = [
  'role',
  'project',
  'skill',
  'achievement',
  'testimonial',
  'salary',
  'interview_answer',
  'preference',
];

const TYPE_LABELS: Record<ProfileItemType, string> = {
  role: 'Role',
  project: 'Project',
  skill: 'Skill',
  achievement: 'Achievement',
  testimonial: 'Testimonial',
  salary: 'Salary',
  interview_answer: 'Interview',
  preference: 'Preference',
};

const TYPE_FULL_LABELS: Record<ProfileItemType, string> = {
  role: 'Roles & Experience',
  project: 'Projects',
  skill: 'Skills',
  achievement: 'Achievements',
  testimonial: 'Testimonials',
  salary: 'Salary Expectations',
  interview_answer: 'Interview Answers',
  preference: 'Preferences',
};

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function ItemsSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-24 w-full rounded-xl" />
      ))}
    </div>
  );
}

// ─── Evidence search result card ──────────────────────────────────────────────

function EvidenceResultCard({ result }: { result: RetrievedEvidence }) {
  const scorePct = Math.round(result.score * 100);
  return (
    <li className="flex flex-col gap-1.5 rounded-lg border bg-card p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-snug">{result.title}</p>
        <span
          className={cn(
            'shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold',
            scorePct >= 80
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              : scorePct >= 50
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-muted text-muted-foreground',
          )}
        >
          {scorePct}%
        </span>
      </div>
      <p className="line-clamp-3 text-sm text-muted-foreground">{result.snippet}</p>
      <Badge variant="outline" className="w-fit text-[11px]">
        {result.source_type}
      </Badge>
    </li>
  );
}

// ─── Profile item card ────────────────────────────────────────────────────────

interface ProfileItemCardProps {
  item: ProfileItem;
  isEditing: boolean;
  isDeleting: boolean;
  isRegenerating: boolean;
  onEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: (data: ProfileItemCreate) => Promise<void>;
  onDelete: () => void;
  onRegenerate: () => void;
}

function ProfileItemCard({
  item,
  isEditing,
  isDeleting,
  isRegenerating,
  onEdit,
  onCancelEdit,
  onSaveEdit,
  onDelete,
  onRegenerate,
}: ProfileItemCardProps) {
  if (isEditing) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Edit item</CardTitle>
            <Button
              size="icon"
              variant="ghost"
              onClick={onCancelEdit}
              aria-label="Cancel editing"
            >
              <X />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ProfileItemEditor item={item} onSave={onSaveEdit} />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="flex items-start gap-4 pb-4 pt-5">
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <Badge variant="secondary" className="shrink-0 text-[11px]">
              {TYPE_LABELS[item.type]}
            </Badge>
            <span className="truncate text-sm font-medium">{item.title}</span>
          </div>
          <p className="line-clamp-3 text-sm text-muted-foreground">{item.body}</p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button
            size="icon"
            variant="ghost"
            onClick={onRegenerate}
            disabled={isRegenerating}
            aria-label="Regenerate embeddings"
            title="Regenerate embeddings"
          >
            {isRegenerating ? (
              <Loader2 className="animate-spin" />
            ) : (
              <RefreshCw />
            )}
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={onEdit}
            aria-label="Edit item"
            title="Edit"
          >
            <Pencil />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={onDelete}
            disabled={isDeleting}
            aria-label="Delete item"
            title="Delete"
            className="text-destructive hover:text-destructive"
          >
            {isDeleting ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Trash2 />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Type tab panel ───────────────────────────────────────────────────────────

interface TypePanelProps {
  type: ProfileItemType;
  items: ProfileItem[];
  editingItemId: string | null;
  isAdding: boolean;
  deletingId: string | null;
  regeneratingId: string | null;
  onEdit: (id: string) => void;
  onCancelEdit: () => void;
  onSaveEdit: (id: string, data: ProfileItemCreate) => Promise<void>;
  onDelete: (id: string) => void;
  onRegenerate: (id: string) => void;
  onAddToggle: () => void;
  onAddSave: (data: ProfileItemCreate) => Promise<void>;
  onCancelAdd: () => void;
}

function TypePanel({
  type,
  items,
  editingItemId,
  isAdding,
  deletingId,
  regeneratingId,
  onEdit,
  onCancelEdit,
  onSaveEdit,
  onDelete,
  onRegenerate,
  onAddToggle,
  onAddSave,
  onCancelAdd,
}: TypePanelProps) {
  return (
    <div className="flex flex-col gap-4">
      {/* Panel header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium">{TYPE_FULL_LABELS[type]}</h3>
          <p className="text-xs text-muted-foreground">
            {items.length} {items.length === 1 ? 'item' : 'items'}
          </p>
        </div>
        {!isAdding && (
          <Button size="sm" variant="outline" onClick={onAddToggle}>
            <Plus />
            Add {TYPE_LABELS[type]}
          </Button>
        )}
      </div>

      {/* Inline add form */}
      {isAdding && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                Add {TYPE_FULL_LABELS[type]}
              </CardTitle>
              <Button
                size="icon"
                variant="ghost"
                onClick={onCancelAdd}
                aria-label="Cancel"
              >
                <X />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ProfileItemEditor onSave={onAddSave} />
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {items.length === 0 && !isAdding ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed py-12 text-center">
          <p className="text-sm text-muted-foreground">
            No {TYPE_FULL_LABELS[type].toLowerCase()} added yet.
          </p>
          <Button size="sm" variant="ghost" onClick={onAddToggle}>
            <Plus />
            Add your first
          </Button>
        </div>
      ) : (
        <ul className="flex flex-col gap-3">
          {items.map((item) => (
            <li key={item.id}>
              <ProfileItemCard
                item={item}
                isEditing={editingItemId === item.id}
                isDeleting={deletingId === item.id}
                isRegenerating={regeneratingId === item.id}
                onEdit={() => onEdit(item.id)}
                onCancelEdit={onCancelEdit}
                onSaveEdit={(data) => onSaveEdit(item.id, data)}
                onDelete={() => onDelete(item.id)}
                onRegenerate={() => onRegenerate(item.id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ProfilePage() {
  // Queries
  const { data: items, isLoading, error } = useProfileItems();

  // Mutations
  const createMutation = useCreateProfileItem();
  const updateMutation = useUpdateProfileItem();
  const deleteMutation = useDeleteProfileItem();
  const regenerateMutation = useRegenerateEmbeddings();

  // UI state
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [addingType, setAddingType] = useState<ProfileItemType | null>(null);

  // Search state
  const [searchInput, setSearchInput] = useState('');
  const [activeSearchReq, setActiveSearchReq] = useState<ProfileSearchRequest | null>(null);

  const {
    data: searchData,
    isLoading: isSearching,
    error: searchError,
  } = useProfileSearch(activeSearchReq);

  // Derived: which item IDs are in-flight
  const deletingId = deleteMutation.isPending
    ? (deleteMutation.variables ?? null)
    : null;
  const regeneratingId = regenerateMutation.isPending
    ? (regenerateMutation.variables ?? null)
    : null;

  // Group items by type
  const grouped = React.useMemo(() => {
    const map: Record<ProfileItemType, ProfileItem[]> = {
      role: [],
      project: [],
      skill: [],
      achievement: [],
      testimonial: [],
      salary: [],
      interview_answer: [],
      preference: [],
    };
    (items ?? []).forEach((item) => {
      map[item.type].push(item);
    });
    return map;
  }, [items]);

  // Handlers
  const handleSearch = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const q = searchInput.trim();
      if (!q) return;
      setActiveSearchReq({ query: q, top_k: 10 });
    },
    [searchInput],
  );

  const handleClearSearch = useCallback(() => {
    setSearchInput('');
    setActiveSearchReq(null);
  }, []);

  const handleAddSave = useCallback(
    async (data: ProfileItemCreate) => {
      await createMutation.mutateAsync(data);
      setAddingType(null);
    },
    [createMutation],
  );

  const handleEditSave = useCallback(
    async (id: string, data: ProfileItemCreate) => {
      await updateMutation.mutateAsync({ id, body: data });
      setEditingItemId(null);
    },
    [updateMutation],
  );

  const handleDelete = useCallback(
    (id: string) => {
      deleteMutation.mutate(id);
    },
    [deleteMutation],
  );

  const handleRegenerate = useCallback(
    (id: string) => {
      regenerateMutation.mutate(id);
    },
    [regenerateMutation],
  );

  const totalItems = items?.length ?? 0;
  const searchResults: RetrievedEvidence[] = searchData?.results ?? [];

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
      {/* Page header */}
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground">
          Your roles, projects, skills, and evidence that ground every draft.
          {!isLoading && (
            <span className="ml-1 tabular-nums">
              ({totalItems} {totalItems === 1 ? 'item' : 'items'})
            </span>
          )}
        </p>
      </header>

      {/* Evidence search */}
      <section aria-labelledby="evidence-search-heading">
        <Card>
          <CardHeader>
            <CardTitle
              id="evidence-search-heading"
              className="flex items-center gap-2"
            >
              <Search className="size-4" />
              Evidence Search
            </CardTitle>
            <CardDescription>
              Semantically search your knowledge base to preview what evidence
              will be retrieved for a job requirement.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <form onSubmit={handleSearch} className="flex gap-2">
              <Input
                placeholder="e.g. TypeScript performance optimisation"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="flex-1"
                aria-label="Search query"
              />
              <Button
                type="submit"
                disabled={!searchInput.trim() || isSearching}
              >
                {isSearching ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Search />
                )}
                Search
              </Button>
              {activeSearchReq !== null && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClearSearch}
                >
                  Clear
                </Button>
              )}
            </form>

            {/* Search error */}
            {searchError !== null && searchError !== undefined && (
              <div
                role="alert"
                className="flex items-center gap-2 text-sm text-destructive"
              >
                <AlertCircle className="size-4 shrink-0" />
                {searchError instanceof Error
                  ? searchError.message
                  : 'Search failed. Please try again.'}
              </div>
            )}

            {/* Searching skeleton */}
            {isSearching && (
              <div className="flex flex-col gap-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-lg" />
                ))}
              </div>
            )}

            {/* Search results */}
            {activeSearchReq !== null && !isSearching && searchError == null && (
              <>
                {searchResults.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No evidence found for &ldquo;{activeSearchReq.query}&rdquo;.
                    Try a different query or add more profile items.
                  </p>
                ) : (
                  <ul
                    className="flex flex-col gap-2"
                    aria-label="Search results"
                  >
                    {searchResults.map((r) => (
                      <EvidenceResultCard
                        key={r.evidence_chunk_id}
                        result={r}
                      />
                    ))}
                  </ul>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Knowledge base */}
      <section aria-labelledby="knowledge-base-heading">
        <h2
          id="knowledge-base-heading"
          className="mb-4 text-lg font-semibold tracking-tight"
        >
          Knowledge Base
        </h2>

        {/* Loading */}
        {isLoading && <ItemsSkeleton />}

        {/* Error */}
        {error != null && !isLoading && (
          <div
            role="alert"
            className="flex items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive"
          >
            <AlertCircle className="size-4 shrink-0" />
            {error instanceof Error
              ? error.message
              : 'Failed to load profile items.'}
          </div>
        )}

        {/* Content */}
        {!isLoading && error == null && (
          <Tabs defaultValue="role">
            <TabsList className="mb-4 h-auto flex-wrap gap-1 p-1">
              {ALL_TYPES.map((t) => (
                <TabsTrigger key={t} value={t} className="gap-1.5">
                  {TYPE_LABELS[t]}
                  {grouped[t].length > 0 && (
                    <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-semibold tabular-nums leading-none">
                      {grouped[t].length}
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>

            {ALL_TYPES.map((t) => (
              <TabsContent key={t} value={t}>
                <TypePanel
                  type={t}
                  items={grouped[t]}
                  editingItemId={editingItemId}
                  isAdding={addingType === t}
                  deletingId={deletingId}
                  regeneratingId={regeneratingId}
                  onEdit={setEditingItemId}
                  onCancelEdit={() => setEditingItemId(null)}
                  onSaveEdit={handleEditSave}
                  onDelete={handleDelete}
                  onRegenerate={handleRegenerate}
                  onAddToggle={() => {
                    setAddingType(t);
                    setEditingItemId(null);
                  }}
                  onAddSave={handleAddSave}
                  onCancelAdd={() => setAddingType(null)}
                />
              </TabsContent>
            ))}
          </Tabs>
        )}
      </section>
    </div>
  );
}
