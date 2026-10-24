import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "../App";
import { navItems } from "../components/Layout";

vi.mock("../services/api", () => ({
  getHealth: vi.fn().mockResolvedValue({ status: "ok", product: "CryptoGuard", version: "1.0.0", database: "ok", nvd_enabled: false }),
  getSources: vi.fn().mockResolvedValue({
    product: "CryptoGuard",
    nvd_enabled: false,
    nvd_key_configured: false,
    cache_ttl_seconds: 21600,
    note: "Source availability is not a security result.",
    sources: [],
  }),
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : "error"),
  getDashboard: vi.fn().mockResolvedValue({
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
    sources: [],
    notes: [],
  }),
}));

describe("navigation", () => {
  it("links every primary section", () => {
    render(
      <MemoryRouter>
        <AppRoutes />
      </MemoryRouter>,
    );
    for (const item of navItems) {
      expect(screen.getByRole("link", { name: item.label })).toHaveAttribute("href", item.to);
    }
  });
});
