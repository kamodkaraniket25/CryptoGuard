import { render, screen } from "@testing-library/react";
import { SourcesPage } from "../pages/SourcesPage";
import { getSources } from "../services/api";

vi.mock("../services/api", () => ({
  getSources: vi.fn(),
  checkSources: vi.fn(),
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : "error"),
}));

describe("dataset source display", () => {
  it("renders the three configured sources and their status", async () => {
    vi.mocked(getSources).mockResolvedValue({
      product: "CryptoGuard",
      nvd_enabled: false,
      nvd_key_configured: false,
      cache_ttl_seconds: 21600,
      note: "Source availability is not a security result.",
      sources: [
        source("osv", "OSV Vulnerability Database"),
        source("nvd", "National Vulnerability Database (NVD)"),
        source("cyclonedx", "CycloneDX", "CycloneDX is a specification and schema, not a vulnerability database."),
      ],
    });
    render(<SourcesPage />);
    expect(await screen.findByText("OSV Vulnerability Database")).toBeInTheDocument();
    expect(screen.getByText("National Vulnerability Database (NVD)")).toBeInTheDocument();
    expect(screen.getByText("CycloneDX is a specification and schema, not a vulnerability database.")).toBeInTheDocument();
    expect(screen.getAllByText("NOT CHECKED").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Check source status" })).toBeInTheDocument();
  });
});

function source(id: string, name: string, limitation = "Example limitation") {
  return {
    id,
    name,
    website: "https://example.com",
    documentation_url: "https://example.com/docs",
    endpoint: "https://example.com/api",
    category: "Test",
    purpose: "Shown in the catalog.",
    access_method: "Live HTTP API integration",
    fields_used: ["id"],
    limitations: [limitation],
    attribution: "Test attribution",
    license_note: "See the official site.",
    data_is_downloaded: false,
    status: "NOT CHECKED",
    checked_at: null,
    latency_ms: null,
    error_category: null,
    detail: "This source has not been checked in this database.",
  };
}
