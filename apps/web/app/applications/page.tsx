"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, Search } from "lucide-react";

import { useApplications } from "@/lib/hooks";
import type {
  ApplicationListItem,
  ApplicationStatus,
} from "@applypilot/shared-types";

import { ApplicationTable } from "@/components/application-table";
import { buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface StatusOption {
  value: ApplicationStatus | "";
  label: string;
}

const STATUS_OPTIONS: StatusOption[] = [
  { value: "", label: "All statuses" },
  { value: "saved", label: "Saved" },
  { value: "analyzed", label: "Analyzed" },
  { value: "drafted", label: "Drafted" },
  { value: "ready_to_apply", label: "Ready to apply" },
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offer", label: "Offer" },
  { value: "rejected", label: "Rejected" },
  { value: "archived", label: "Archived" },
];

export default function ApplicationsPage() {
  const router = useRouter();
  const { data: applications, isPending, isError, error } = useApplications();

  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "">("");
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = useMemo<ApplicationListItem[]>(() => {
    if (!applications) return [];

    const lowerQuery = searchQuery.trim().toLowerCase();

    return applications.filter((app) => {
      const matchesStatus = statusFilter === "" || app.status === statusFilter;
      const matchesSearch =
        lowerQuery === "" ||
        (app.company_name?.toLowerCase().includes(lowerQuery) ?? false) ||
        (app.role_title?.toLowerCase().includes(lowerQuery) ?? false);

      return matchesStatus && matchesSearch;
    });
  }, [applications, statusFilter, searchQuery]);

  const handleRowClick = (app: ApplicationListItem) => {
    router.push(`/applications/${app.id}`);
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      {/* Page header */}
      <header className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Applications
          </h1>
          <p className="text-sm text-muted-foreground">
            Track, analyze, and draft responses for every role you pursue.
          </p>
        </div>
        <Link href="/applications/new" className={cn(buttonVariants())}>
          <Plus className="size-4" aria-hidden="true" />
          New application
        </Link>
      </header>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search
            className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            placeholder="Search by company or role…"
            className="pl-8"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search applications"
          />
        </div>
        <Select
          className="sm:w-52"
          value={statusFilter}
          onChange={(e) =>
            setStatusFilter(e.target.value as ApplicationStatus | "")
          }
          aria-label="Filter by status"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>
      </div>

      {/* Content area */}
      {isPending ? (
        <div className="flex flex-col gap-2 overflow-hidden rounded-lg border">
          {/* Table header skeleton */}
          <div className="flex gap-4 border-b bg-muted/50 px-4 py-3">
            {[35, 30, 15, 10, 10].map((w, i) => (
              <Skeleton key={i} className="h-4" style={{ width: `${w}%` }} />
            ))}
          </div>
          {/* Row skeletons */}
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 border-b px-4 py-3 last:border-0">
              <Skeleton className="h-4" style={{ width: "35%" }} />
              <Skeleton className="h-4" style={{ width: "30%" }} />
              <Skeleton className="h-6 w-20 rounded-full" />
              <Skeleton className="ml-auto h-4 w-10" />
              <Skeleton className="h-4 w-24" />
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-6 text-center">
          <p className="text-sm font-medium text-destructive">
            Failed to load applications
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {error instanceof Error
              ? error.message
              : "An unexpected error occurred."}
          </p>
        </div>
      ) : (
        <ApplicationTable applications={filtered} onRowClick={handleRowClick} />
      )}
    </div>
  );
}
