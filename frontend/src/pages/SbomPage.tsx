import { useState, type FormEvent } from "react";
import { Download } from "lucide-react";
import { Alert, Badge, CopyButton, FileDrop, JsonView, Limitations, PageHeader, Spinner } from "../components/ui";
import { errorMessage, generateSbom, type SbomResult } from "../services/api";
import type { OperationResponse } from "../types";
import { downloadText } from "../utils/download";
import { MAX_UPLOAD_BYTES } from "../utils/format";

export function SbomPage() {
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState("auto");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<OperationResponse<SbomResult> | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a manifest to turn into an SBOM.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await generateSbom(file, format));
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  const components = report ? componentsOf(report.result.bom) : [];
  const json = report ? JSON.stringify(report.result.bom, null, 2) : "";

  return (
    <section className="space-y-4">
      <PageHeader
        kicker="Supply chain"
        title="SBOM Generator"
        description="CryptoGuard builds a CycloneDX JSON bill of materials from the manifest and validates it with the official schema. This is an inventory, not a vulnerability scan. Missing licenses, suppliers, and hashes stay missing."
      />
      <form className="panel-flat panel-pad space-y-4" onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
          <FileDrop id="sbom-file" label="Manifest" file={file} maxBytes={MAX_UPLOAD_BYTES} hint="package.json or requirements.txt. The upload limit is 10 MB." onReject={setError} onFile={(next) => { setError(null); setFile(next); }} />
          <div>
            <label className="label" htmlFor="sbom-format">Format</label>
            <select id="sbom-format" className="select" value={format} onChange={(event) => setFormat(event.target.value)}>
              <option value="auto">Detect from filename</option>
              <option value="npm">package.json</option>
              <option value="pypi">requirements.txt</option>
            </select>
          </div>
        </div>
        <button className="btn btn-primary" disabled={loading} type="submit">Generate SBOM</button>
        {loading && <Spinner label="Building SBOM…" />}
        {error && <Alert tone="error">{error}</Alert>}
      </form>
      {report && (
        <article className="space-y-4">
          <div className="panel-flat panel-pad">
            <div className="flex flex-wrap items-center gap-2">
              <Badge value={report.result.valid ? "VALID CYCLONEDX 1.7" : "VALIDATION FAILED"} />
              <span className="text-sm text-[var(--cg-muted)]">{report.result.component_count} components from the parsed manifest</span>
            </div>
            <dl className="mt-3 grid gap-2 text-sm md:grid-cols-2">
              <div><dt className="text-xs text-[var(--cg-faint)]">Format</dt><dd>CycloneDX {report.result.spec_version}</dd></div>
              <div><dt className="text-xs text-[var(--cg-faint)]">Schema</dt><dd><a className="break-all text-[var(--cg-cyan)] underline" href={report.result.schema_url}>{report.result.schema_url}</a></dd></div>
            </dl>
            <p className="mt-3 text-sm text-[var(--cg-muted)]">{report.result.note}</p>
            {report.result.validation_errors.map((item) => <div key={item} className="mt-2"><Alert tone="error">{item}</Alert></div>)}
            {report.result.warnings.map((item) => <div key={item} className="mt-2"><Alert tone="warning">{item}</Alert></div>)}
          </div>
          <div className="panel-flat">
            <div className="px-4 pt-4">
              <h2 className="text-sm font-medium">Component inventory</h2>
              <p className="text-xs text-[var(--cg-faint)]">Only fields present in the generated document are shown.</p>
            </div>
            {components.length === 0 ? (
              <p className="px-4 py-6 text-sm text-[var(--cg-muted)]">The document did not include a component array.</p>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr><th>Name</th><th>Version</th><th>Type</th><th>PURL</th></tr>
                  </thead>
                  <tbody>
                    {components.map((component, index) => (
                      <tr key={`${String(component.name)}-${index}`}>
                        <td>{text(component.name)}</td>
                        <td className="font-mono text-xs">{text(component.version)}</td>
                        <td>{text(component.type)}</td>
                        <td className="max-w-xs break-all font-mono text-xs">{text(component.purl)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          <div className="panel-flat panel-pad space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-medium">JSON preview</h2>
              <div className="flex flex-wrap gap-2">
                <CopyButton value={json} label="Copy JSON" />
                <button className="btn btn-secondary" type="button" onClick={() => downloadText("cryptoguard-bom.cdx.json", json)}>
                  <Download size={14} />
                  Download SBOM
                </button>
              </div>
            </div>
            <JsonView value={report.result.bom} />
            <Limitations items={report.limitations} />
          </div>
        </article>
      )}
    </section>
  );
}

function componentsOf(bom: Record<string, unknown>): Record<string, unknown>[] {
  const value = bom.components;
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object");
}

function text(value: unknown): string {
  return typeof value === "string" && value.trim() ? value : "not declared";
}
