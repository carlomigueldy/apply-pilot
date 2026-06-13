import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApplicationStatusBadge } from "@/components/application-status-badge";

describe("ApplicationStatusBadge", () => {
  it('renders "Saved" for saved status', () => {
    render(<ApplicationStatusBadge status="saved" />);
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it('renders "Analyzed" for analyzed status', () => {
    render(<ApplicationStatusBadge status="analyzed" />);
    expect(screen.getByText("Analyzed")).toBeInTheDocument();
  });

  it('renders "Drafted" for drafted status', () => {
    render(<ApplicationStatusBadge status="drafted" />);
    expect(screen.getByText("Drafted")).toBeInTheDocument();
  });

  it('renders "Ready" for ready_to_apply status', () => {
    render(<ApplicationStatusBadge status="ready_to_apply" />);
    expect(screen.getByText("Ready")).toBeInTheDocument();
  });

  it('renders "Applied" for applied status', () => {
    render(<ApplicationStatusBadge status="applied" />);
    expect(screen.getByText("Applied")).toBeInTheDocument();
  });

  it('renders "Interviewing" for interviewing status', () => {
    render(<ApplicationStatusBadge status="interviewing" />);
    expect(screen.getByText("Interviewing")).toBeInTheDocument();
  });

  it('renders "Offer" for offer status', () => {
    render(<ApplicationStatusBadge status="offer" />);
    expect(screen.getByText("Offer")).toBeInTheDocument();
  });

  it('renders "Rejected" for rejected status', () => {
    render(<ApplicationStatusBadge status="rejected" />);
    expect(screen.getByText("Rejected")).toBeInTheDocument();
  });

  it('renders "Archived" for archived status', () => {
    render(<ApplicationStatusBadge status="archived" />);
    expect(screen.getByText("Archived")).toBeInTheDocument();
  });

  it("accepts and applies a custom className", () => {
    render(
      <ApplicationStatusBadge status="saved" className="custom-class" />,
    );
    const badge = screen.getByText("Saved");
    expect(badge.className).toContain("custom-class");
  });
});
