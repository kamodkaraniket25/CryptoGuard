import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { DashboardPage } from "../pages/DashboardPage";
import { getDashboard } from "../services/api";

vi.mock("../services/api", () => ({
  getDashboard: vi.fn(),
  getHealth: vi.fn().mockResolvedValue({
    status: "ok",
    product: "CryptoGuard",
    version: "1.0.0",
    database: "ok",
    nvd_enabled: false,
  }),
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : "error"),
}));

const empty = {
  product: "CryptoGuard",
  total_operations: 0,
  integrity_success: 0,
  integrity_failed: 0,
  integrity_not_verified: 0,
  hmac_generated: 0,
  hmac_verified_success: 0,
  hmac_verified_failed: 0,
  signatures_generated: 0,
  signatures_verified_success: 0,
  signatures_verified_failed: 0,
  provenance_checks: 0,
  dependency_scans: 0,
  vulnerability_queries: 0,
  vulnerability_findings: 0,
  sbom_generated: 0,
  recent_operations: [],
  activity: [],
  sources: [{ id: "osv", name: "OSV Vulnerability Database", status: "NOT CHECKED", checked_at: null }],
  notes: ["Counts come from verification records stored in the local database."],
};

describe("empty dashboard", () => {
  it("shows the empty state from a zero record response", async () => {
    vi.mocked(getDashboard).mockResolvedValue(empty);
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );
    expect(await screen.findByText("No verification operations have been recorded yet.")).toBeInTheDocument();
    expect(screen.getByText("NOT CHECKED")).toBeInTheDocument();
  });
});
