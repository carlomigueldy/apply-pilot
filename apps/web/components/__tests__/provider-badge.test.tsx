import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProviderBadge } from "@/components/provider-badge";

describe("ProviderBadge", () => {
  it("renders the provider name and local indicator", () => {
    render(<ProviderBadge provider="fake" isLocal />);

    expect(screen.getByText("fake")).toBeInTheDocument();
    expect(screen.getByText("local")).toBeInTheDocument();
  });

  it("renders the cloud indicator for non-local providers", () => {
    render(<ProviderBadge provider="openai" isLocal={false} />);

    expect(screen.getByText("openai")).toBeInTheDocument();
    expect(screen.getByText("cloud")).toBeInTheDocument();
  });
});
