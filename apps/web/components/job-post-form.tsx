"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v3";
import type { JobApplicationCreate, WorkArrangement } from "@applypilot/shared-types";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const schema = z.object({
  raw_job_post: z
    .string()
    .min(30, "Paste the full job post (at least 30 characters)"),
  company_name: z.string().optional(),
  role_title: z.string().optional(),
  job_url: z.string().optional(),
  salary_text: z.string().optional(),
  work_arrangement: z.string().optional(),
  timezone_text: z.string().optional(),
  recruiter_name: z.string().optional(),
  recruiter_email: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const WORK_ARRANGEMENT_OPTIONS: { value: WorkArrangement; label: string }[] = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
  { value: "unknown", label: "Unknown" },
];

export interface JobPostFormProps {
  onSubmit: (data: JobApplicationCreate) => void | Promise<void>;
  isSubmitting?: boolean;
}

export function JobPostForm({ onSubmit, isSubmitting }: JobPostFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      raw_job_post: "",
      company_name: "",
      role_title: "",
      job_url: "",
      salary_text: "",
      work_arrangement: "",
      timezone_text: "",
      recruiter_name: "",
      recruiter_email: "",
    },
  });

  const handleFormSubmit = (values: FormValues) => {
    const workArrangement = values.work_arrangement as WorkArrangement | undefined;
    void onSubmit({
      raw_job_post: values.raw_job_post,
      company_name: values.company_name || undefined,
      role_title: values.role_title || undefined,
      job_url: values.job_url || undefined,
      salary_text: values.salary_text || undefined,
      work_arrangement: workArrangement || undefined,
      timezone_text: values.timezone_text || undefined,
      recruiter_name: values.recruiter_name || undefined,
      recruiter_email: values.recruiter_email || undefined,
    });
  };

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      className="flex flex-col gap-6"
    >
      {/* Raw job post — required */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="raw_job_post">
          Job Post <span aria-hidden="true" className="text-destructive">*</span>
        </Label>
        <Textarea
          id="raw_job_post"
          data-testid="job-post-textarea"
          placeholder="Paste the full job description here…"
          className="min-h-[200px]"
          aria-describedby={errors.raw_job_post ? "raw_job_post_error" : undefined}
          {...register("raw_job_post")}
        />
        {errors.raw_job_post && (
          <p
            id="raw_job_post_error"
            role="alert"
            className="text-xs text-destructive"
          >
            {errors.raw_job_post.message}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Company name */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="company_name">Company</Label>
          <Input
            id="company_name"
            placeholder="Acme Corp"
            {...register("company_name")}
          />
        </div>

        {/* Role title */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="role_title">Role Title</Label>
          <Input
            id="role_title"
            placeholder="Senior Frontend Engineer"
            {...register("role_title")}
          />
        </div>

        {/* Job URL */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="job_url">Job URL</Label>
          <Input
            id="job_url"
            type="url"
            placeholder="https://…"
            {...register("job_url")}
          />
        </div>

        {/* Salary */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="salary_text">Salary / Compensation</Label>
          <Input
            id="salary_text"
            placeholder="$120k – $150k"
            {...register("salary_text")}
          />
        </div>

        {/* Work arrangement */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="work_arrangement">Work Arrangement</Label>
          <Select id="work_arrangement" {...register("work_arrangement")}>
            <option value="">— Select —</option>
            {WORK_ARRANGEMENT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </div>

        {/* Timezone */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="timezone_text">Timezone</Label>
          <Input
            id="timezone_text"
            placeholder="UTC-8, PST, etc."
            {...register("timezone_text")}
          />
        </div>

        {/* Recruiter name */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="recruiter_name">Recruiter Name</Label>
          <Input
            id="recruiter_name"
            placeholder="Jane Smith"
            {...register("recruiter_name")}
          />
        </div>

        {/* Recruiter email */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="recruiter_email">Recruiter Email</Label>
          <Input
            id="recruiter_email"
            type="email"
            placeholder="recruiter@company.com"
            {...register("recruiter_email")}
          />
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="submit" data-testid="create-application-submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving…" : "Save Application"}
        </Button>
      </div>
    </form>
  );
}
