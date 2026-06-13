import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FitScoreCard } from "@/components/fit-score-card";
import type { FitAnalysis } from "@applypilot/shared-types";

const baseMock: FitAnalysis = {
  fit_score: 82,
  summary: "Strong candidate with relevant full-stack experience.",
  items: [],
  red_flags: [],
  positioning_strategy: "Highlight your React and Node.js expertise.",
};

describe("FitScoreCard", () => {
  it("renders the numeric fit score", () => {
    render(<FitScoreCard analysis={baseMock} />);
    expect(screen.getByText("82")).toBeInTheDocument();
  });

  it("renders the summary text", () => {
    render(<FitScoreCard analysis={baseMock} />);
    expect(
      screen.getByText("Strong candidate with relevant full-stack experience."),
    ).toBeInTheDocument();
  });

  it("renders the positioning strategy", () => {
    render(<FitScoreCard analysis={baseMock} />);
    expect(
      screen.getByText("Highlight your React and Node.js expertise."),
    ).toBeInTheDocument();
  });

  it("shows the Fit Analysis heading", () => {
    render(<FitScoreCard analysis={baseMock} />);
    expect(screen.getByText("Fit Analysis")).toBeInTheDocument();
  });

  it("renders red flags when present", () => {
    const withFlags: FitAnalysis = {
      ...baseMock,
      red_flags: ["No Rust experience", "Requires TS 5+ certification"],
    };
    render(<FitScoreCard analysis={withFlags} />);
    expect(screen.getByText("No Rust experience")).toBeInTheDocument();
    expect(
      screen.getByText("Requires TS 5+ certification"),
    ).toBeInTheDocument();
  });

  it("does not render a red flags section when list is empty", () => {
    render(<FitScoreCard analysis={baseMock} />);
    expect(screen.queryByText("Red Flags")).not.toBeInTheDocument();
  });

  it("applies the 'Excellent fit' label for high scores", () => {
    render(<FitScoreCard analysis={{ ...baseMock, fit_score: 90 }} />);
    expect(screen.getByText("Excellent fit")).toBeInTheDocument();
  });

  it("applies the 'Poor fit' label for low scores", () => {
    render(<FitScoreCard analysis={{ ...baseMock, fit_score: 20 }} />);
    expect(screen.getByText("Poor fit")).toBeInTheDocument();
  });
});
