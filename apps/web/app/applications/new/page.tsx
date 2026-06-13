"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { useCreateApplication } from "@/lib/hooks";
import type { JobApplicationCreate } from "@applypilot/shared-types";

import { JobPostForm } from "@/components/job-post-form";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function NewApplicationPage() {
  const router = useRouter();
  const { mutateAsync, isPending, isError, error } = useCreateApplication();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (data: JobApplicationCreate) => {
    setSubmitError(null);
    try {
      const newApp = await mutateAsync(data);
      router.push(`/applications/${newApp.id}`);
    } catch (err) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : "Failed to create the application. Please try again.",
      );
    }
  };

  const errorMessage =
    submitError ??
    (isError && error instanceof Error ? error.message : null) ??
    (isError ? "An unexpected error occurred." : null);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      {/* Page header */}
      <header className="flex flex-col gap-3">
        <Link
          href="/applications"
          className={cn(
            buttonVariants({ variant: "ghost", size: "sm" }),
            "-ml-2 w-fit",
          )}
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Back to applications
        </Link>

        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            New application
          </h1>
          <p className="text-sm text-muted-foreground">
            Paste a job post below and optionally fill in additional context.
            ApplyPilot will analyze the role and generate tailored drafts for
            you.
          </p>
        </div>
      </header>

      {/* Error banner */}
      {errorMessage && (
        <div
          role="alert"
          className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3"
        >
          <p className="text-sm text-destructive">{errorMessage}</p>
        </div>
      )}

      {/* Form card */}
      <Card>
        <CardHeader>
          <CardTitle>Job details</CardTitle>
          <CardDescription>
            Only the job post is required — the AI will extract what it can from
            the raw text. All other fields are optional but improve accuracy.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <JobPostForm onSubmit={handleSubmit} isSubmitting={isPending} />
        </CardContent>
      </Card>
    </div>
  );
}
