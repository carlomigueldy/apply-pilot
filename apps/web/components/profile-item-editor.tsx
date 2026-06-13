"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v3";
import type {
  ProfileItem,
  ProfileItemCreate,
  ProfileItemType,
} from "@applypilot/shared-types";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const PROFILE_ITEM_TYPES: { value: ProfileItemType; label: string }[] = [
  { value: "role", label: "Role / Experience" },
  { value: "project", label: "Project" },
  { value: "skill", label: "Skill" },
  { value: "achievement", label: "Achievement" },
  { value: "testimonial", label: "Testimonial" },
  { value: "salary", label: "Salary Expectation" },
  { value: "interview_answer", label: "Interview Answer" },
  { value: "preference", label: "Preference" },
];

const schema = z.object({
  type: z.string().min(1, "Type is required"),
  title: z.string().min(1, "Title is required"),
  body: z.string().min(1, "Content is required"),
});

type FormValues = z.infer<typeof schema>;

export interface ProfileItemEditorProps {
  item?: ProfileItem;
  onSave: (data: ProfileItemCreate) => void | Promise<void>;
  className?: string;
}

export function ProfileItemEditor({
  item,
  onSave,
  className,
}: ProfileItemEditorProps) {
  const isEditing = item !== undefined;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: item?.type ?? "",
      title: item?.title ?? "",
      body: item?.body ?? "",
    },
  });

  const handleFormSubmit = (values: FormValues) => {
    void onSave({
      type: values.type as ProfileItemType,
      title: values.title,
      body: values.body,
    });
  };

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      className={className}
    >
      <div className="flex flex-col gap-4">
        {/* Type */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="item-type">
            Type <span aria-hidden="true" className="text-destructive">*</span>
          </Label>
          <Select
            id="item-type"
            aria-describedby={errors.type ? "item-type-error" : undefined}
            {...register("type")}
          >
            <option value="">— Select type —</option>
            {PROFILE_ITEM_TYPES.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
          {errors.type && (
            <p id="item-type-error" role="alert" className="text-xs text-destructive">
              {errors.type.message}
            </p>
          )}
        </div>

        {/* Title */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="item-title">
            Title <span aria-hidden="true" className="text-destructive">*</span>
          </Label>
          <Input
            id="item-title"
            placeholder="e.g. Senior Frontend Engineer at Acme"
            aria-describedby={errors.title ? "item-title-error" : undefined}
            {...register("title")}
          />
          {errors.title && (
            <p id="item-title-error" role="alert" className="text-xs text-destructive">
              {errors.title.message}
            </p>
          )}
        </div>

        {/* Body */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="item-body">
            Content <span aria-hidden="true" className="text-destructive">*</span>
          </Label>
          <Textarea
            id="item-body"
            placeholder="Describe the experience, skill, or achievement in detail…"
            className="min-h-[160px]"
            aria-describedby={errors.body ? "item-body-error" : undefined}
            {...register("body")}
          />
          {errors.body && (
            <p id="item-body-error" role="alert" className="text-xs text-destructive">
              {errors.body.message}
            </p>
          )}
        </div>

        <div className="flex justify-end">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? "Saving…"
              : isEditing
                ? "Update Item"
                : "Add Item"}
          </Button>
        </div>
      </div>
    </form>
  );
}
