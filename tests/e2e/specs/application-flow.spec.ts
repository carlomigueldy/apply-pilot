/**
 * E2E: Core Application Flow
 *
 * Covers the full happy-path journey:
 *   Create → Analyze → Fit → Evidence → Drafts → Approve → Ready
 *
 * Prerequisites (managed externally by the caller):
 *   - API running on http://127.0.0.1:8000 with LLM_PROVIDER=fake
 *   - Database seeded (seeds/seed --reset)
 *   - Web dev server started on http://localhost:3000 (Playwright webServer config handles this)
 */

import { test, expect } from "@playwright/test";
import { SENIOR_FULLSTACK_JOB } from "../fixtures/sample-job-posts";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Wait for the analysis run to finish by polling until the fit-score element
 *  appears. The fake LLM provider is synchronous/fast but the mutation cycle
 *  (POST analyze → query invalidation → refetch → render) still takes a moment. */
async function waitForAnalysis(page: import("@playwright/test").Page) {
  // The fit-score is only rendered after the analysis query resolves with data.
  // We switch to the Fit Analysis tab first, then wait.
  await page.getByTestId("tab-fit").click();
  await expect(page.getByTestId("fit-score")).toBeVisible({ timeout: 30_000 });
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

test.describe("Application Flow", () => {
  test("full happy-path: create → analyze → review → approve", async ({
    page,
  }) => {
    // -----------------------------------------------------------------------
    // (a) Dashboard loads
    // -----------------------------------------------------------------------
    await page.goto("/");
    // The dashboard page renders either an applications list or a welcome call-to-action.
    // Either way, the page should not show an error.
    await expect(page).not.toHaveTitle(/Error/i);
    // Verify the page body is present and not blank.
    await expect(page.locator("body")).toBeVisible();

    // -----------------------------------------------------------------------
    // (b) Navigate to /applications/new, fill, and submit
    // -----------------------------------------------------------------------
    await page.goto("/applications/new");

    // Fill the required job post textarea
    const textarea = page.getByTestId("job-post-textarea");
    await expect(textarea).toBeVisible();
    await textarea.fill(SENIOR_FULLSTACK_JOB);

    // Submit the form
    const submitBtn = page.getByTestId("create-application-submit");
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // After successful creation the router redirects to /applications/<uuid>
    await page.waitForURL(/\/applications\/[^/]+$/, { timeout: 15_000 });

    // The application detail page must have loaded (status badge present)
    const statusBadge = page.getByTestId("application-status").first();
    await expect(statusBadge).toBeVisible({ timeout: 10_000 });

    // -----------------------------------------------------------------------
    // (c) Trigger analysis and wait for it to complete
    // -----------------------------------------------------------------------
    const analyzeBtn = page.getByTestId("analyze-button");
    await expect(analyzeBtn).toBeVisible({ timeout: 10_000 });
    await analyzeBtn.click();

    // Wait until the Analyzing… spinner disappears (button re-enables)
    await expect(analyzeBtn).not.toBeDisabled({ timeout: 30_000 });

    // -----------------------------------------------------------------------
    // (d) Fit Analysis tab — assert fit score 0-100
    // -----------------------------------------------------------------------
    await waitForAnalysis(page);

    const fitScoreEl = page.getByTestId("fit-score");
    await expect(fitScoreEl).toBeVisible();

    const scoreText = await fitScoreEl.textContent();
    const score = Number(scoreText?.trim());
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(100);

    // -----------------------------------------------------------------------
    // (e) Evidence tab — at least one evidence-item
    // -----------------------------------------------------------------------
    await page.getByTestId("tab-evidence").click();

    const firstEvidence = page.getByTestId("evidence-item").first();
    await expect(firstEvidence).toBeVisible({ timeout: 15_000 });

    // -----------------------------------------------------------------------
    // (f) Drafts tab — at least one draft-item; approve one
    // -----------------------------------------------------------------------
    await page.getByTestId("tab-drafts").click();

    // Wait for draft content to appear (first TabsContent with data-testid="draft-item")
    const firstDraftItem = page.getByTestId("draft-item").first();
    await expect(firstDraftItem).toBeVisible({ timeout: 15_000 });

    // The approval panel is rendered inside the active draft tab.
    // Click the approve button for the first visible draft.
    const approveBtn = page.getByTestId("approve-draft-button").first();
    await expect(approveBtn).toBeVisible({ timeout: 10_000 });
    await approveBtn.click();

    // After approval the button may show "Approving…" briefly, then return.
    await expect(approveBtn).not.toBeDisabled({ timeout: 15_000 });

    // -----------------------------------------------------------------------
    // (g) Application status becomes "Ready to apply" / "Ready"
    // -----------------------------------------------------------------------
    // After approving a draft the API sets status → ready_to_apply.
    // TanStack Query invalidates the application query, triggering a refetch.
    await expect(
      page.getByTestId("application-status").first(),
    ).toHaveText(/ready|ready to apply/i, { timeout: 15_000 });
  });
});
