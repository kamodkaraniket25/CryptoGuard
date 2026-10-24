import { useState, type FormEvent } from "react";
import { Alert, CopyButton, DownloadButton, FileDrop, Limitations, PageHeader, ResultBanner, Spinner, Steps, useToast } from "../components/ui";
import { errorMessage, hashFile, verifyFile, type HashResult } from "../services/api";
import type { OperationResponse } from "../types";
import { formatBytes, formatWhen, MAX_UPLOAD_BYTES, normalizeSha256, resultLabel, uploadTooLargeMessage, validateOptionalSha256 } from "../utils/format";

export function IntegrityPage() {
  const push = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [reference, setReference] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<OperationResponse<HashResult> | null>(null);

  async function run(compare: boolean) {
    setError(null);
    setReport(null);
    if (!file) {
      setError("Choose a file to hash.");
      return;
    }
    const tooLarge = uploadTooLargeMessage(file);
    if (tooLarge) {
      setError(tooLarge);
      return;
    }
    if (compare && !reference.trim()) {
      setError("Enter a trusted reference digest before comparing hashes.");
      return;
    }
    const validation = validateOptionalSha256(reference);
    if (validation) {
      setError(validation);
      return;
    }
    setLoading(true);
    try {
      const result = compare ? await verifyFile(file, normalizeSha256(reference)) : await hashFile(file);
      setReport(result);
      push(compare ? "Hash comparison complete" : "SHA-256 calculated");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void run(Boolean(reference.trim()));
  }

  return (
    <section>
      <PageHeader
        kicker="Verification"
        title="Hash Checker"
        description="Stream a file through SHA-256, then compare the digest with a reference you trust. A calculated digest alone is NOT VERIFIED. PASS means the bytes match that reference. It does not name the publisher."
      />
      <Steps
        items={[
          { label: "Input", detail: file ? file.name : "Waiting for a file", state: file ? "done" : "current" },
          { label: "SHA-256", detail: loading ? "Computing" : report ? "Computed" : "Not started", state: loading ? "current" : report ? "done" : "idle" },
          { label: "Result", detail: report ? "Recorded" : "Pending", state: report ? "done" : "idle" },
        ]}
      />
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
        <form className="panel-flat panel-pad space-y-4" onSubmit={onSubmit} aria-busy={loading}>
          <FileDrop
            id="integrity-file"
            label="File"
            file={file}
            maxBytes={MAX_UPLOAD_BYTES}
            hint="Any file type. The file is hashed and not executed. The upload limit is 10 MB."
            onReject={setError}
            onFile={(next) => {
              setError(null);
              setFile(next);
            }}
          />
          {file && (
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div className="rounded-lg border border-[var(--cg-line)] px-3 py-2">
                <dt className="text-xs text-[var(--cg-faint)]">Name</dt>
                <dd className="truncate">{file.name}</dd>
              </div>
              <div className="rounded-lg border border-[var(--cg-line)] px-3 py-2">
                <dt className="text-xs text-[var(--cg-faint)]">Size</dt>
                <dd>{formatBytes(file.size)}</dd>
              </div>
              <div className="rounded-lg border border-[var(--cg-line)] px-3 py-2">
                <dt className="text-xs text-[var(--cg-faint)]">Type</dt>
                <dd>{file.type || "unspecified"}</dd>
              </div>
              <div className="rounded-lg border border-[var(--cg-line)] px-3 py-2">
                <dt className="text-xs text-[var(--cg-faint)]">Last modified</dt>
                <dd>{formatWhen(new Date(file.lastModified).toISOString())}</dd>
              </div>
            </dl>
          )}
          <div>
            <label className="label" htmlFor="reference-digest">Reference digest</label>
            <input
              id="reference-digest"
              className="field font-mono"
              spellCheck={false}
              value={reference}
              onChange={(event) => setReference(event.target.value)}
              placeholder="Optional 64-character hex digest"
            />
            <p className="hint">Paste the same digest to demonstrate PASS. Change one character to demonstrate FAIL. Leave it empty to calculate a digest without a comparison.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="btn btn-secondary" type="button" disabled={loading} onClick={() => void run(false)}>Calculate SHA-256</button>
            <button className="btn btn-primary" type="submit" disabled={loading}>Compare Hashes</button>
          </div>
          {loading && <Spinner label="Hashing file…" />}
          {error && <Alert tone="error">{error}</Alert>}
        </form>
        <aside className="panel-flat panel-pad lg:sticky lg:top-20">
          <p className="section-label">Result</p>
          <h2 className="text-sm font-semibold">SHA-256 outcome</h2>
          {!report && <p className="mt-3 text-sm leading-6 text-[var(--cg-muted)]">The digest and comparison appear here after the backend responds.</p>}
          {report && (
            <div className="mt-3 space-y-3">
              <ResultBanner verdict={report.result.verdict} technical={report.result.verdict} explanation={hashExplanation(report.result.verdict)} />
              <div className="digest-block">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="text-xs text-[var(--cg-faint)]">SHA-256</p>
                  <CopyButton value={report.result.sha256} label="Copy digest" />
                </div>
                <p className="break-all font-mono text-xs leading-5 text-[#d7e2f0]">{report.result.sha256}</p>
              </div>
              <dl className="space-y-1 text-xs text-[var(--cg-muted)]">
                <div className="flex justify-between gap-3"><dt>File</dt><dd className="truncate">{report.result.file_name}</dd></div>
                <div className="flex justify-between gap-3"><dt>Size</dt><dd>{formatBytes(report.result.file_size)}</dd></div>
                <div className="flex justify-between gap-3"><dt>Recorded</dt><dd>{formatWhen(report.created_at)}</dd></div>
                <div className="flex justify-between gap-3"><dt>Operation</dt><dd className="font-mono">{report.operation_id.slice(0, 8)}</dd></div>
              </dl>
              <DownloadButton filename={`cryptoguard-${report.operation_id}.json`} content={JSON.stringify(report, null, 2)} label="Download report" />
              <Limitations items={report.limitations} />
            </div>
          )}
          <details className="disclosure">
            <summary>How a digest should be read</summary>
            <p className="pb-2 text-sm leading-6 text-[var(--cg-muted)]">
              SHA-256 maps the file bytes to a 256-bit value. Equal digests are strong evidence that the bytes are equal. They do not name the author, confirm a signature, or show that the software is free of vulnerabilities.
            </p>
          </details>
        </aside>
      </div>
    </section>
  );
}

function hashExplanation(verdict: string): string {
  const label = resultLabel(verdict);
  if (label === "PASS") return "PASS means these file bytes match the trusted reference. It does not name the publisher or prove the file is free of malware. The reference must come from a source you trust.";
  if (label === "FAIL") return "FAIL means the calculated digest is different from the reference. This file is not the same as the trusted version you entered.";
  return "NOT VERIFIED means the digest was calculated and no reference was compared. Paste a trusted SHA-256 value and choose Compare Hashes.";
}
