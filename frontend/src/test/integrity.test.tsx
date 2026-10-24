import { fireEvent, render, screen } from "@testing-library/react";
import { IntegrityPage } from "../pages/IntegrityPage";
import { verifyFile } from "../services/api";

vi.mock("../services/api", () => ({
  hashFile: vi.fn(),
  verifyFile: vi.fn(),
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : "error"),
}));

describe("integrity checker", () => {
  it("requires a file before calling the API", async () => {
    render(<IntegrityPage />);
    fireEvent.click(screen.getByRole("button", { name: "Calculate SHA-256" }));
    expect(await screen.findByText("Choose a file to hash.")).toBeInTheDocument();
    expect(verifyFile).not.toHaveBeenCalled();
  });

  it("shows a loading state and then the verdict", async () => {
    let resolveResult: (value: Awaited<ReturnType<typeof verifyFile>>) => void = () => undefined;
    vi.mocked(verifyFile).mockImplementation(
      () =>
        new Promise((done) => {
          resolveResult = done;
        }),
    );
    render(<IntegrityPage />);
    const file = new File(["abc"], "demo.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText("File"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("Reference digest"), { target: { value: "ab".repeat(32) } });
    fireEvent.click(screen.getByRole("button", { name: "Compare Hashes" }));
    expect(await screen.findByText("Hashing file…")).toBeInTheDocument();
    resolveResult({
      product: "CryptoGuard",
      full_title: "CryptoGuard",
      operation_id: "op-1",
      operation_type: "hash_verify",
      status: "success",
      algorithm: "SHA-256",
      created_at: "2026-10-17T00:00:00Z",
      duration_ms: 3,
      result: { verdict: "MATCH", file_name: "demo.txt", file_size: 3, sha256: "ab".repeat(32), reference_supplied: true },
      limitations: ["A matching SHA-256 digest shows the file bytes are equal to the supplied reference."],
    });
    expect(await screen.findByText("PASS")).toBeInTheDocument();
  });

  it("shows an API error", async () => {
    vi.mocked(verifyFile).mockRejectedValue(new Error("Backend unavailable"));
    render(<IntegrityPage />);
    const file = new File(["abc"], "demo.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText("File"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("Reference digest"), { target: { value: "cd".repeat(32) } });
    fireEvent.click(screen.getByRole("button", { name: "Compare Hashes" }));
    expect(await screen.findByText("Backend unavailable")).toBeInTheDocument();
  });
});
