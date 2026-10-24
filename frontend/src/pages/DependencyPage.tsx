import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ChevronDown, ChevronRight, Download } from "lucide-react";
import { Alert, Badge, FileDrop, Limitations, PageHeader, Spinner } from "../components/ui";
import { errorMessage, getHealth, scanDependencies, type Advisory, type ScanComponent, type ScanResult } from "../services/api";
import type { OperationResponse } from "../types";
import { downloadText } from "../utils/download";
import { formatWhen, MAX_UPLOAD_BYTES, severityText } from "../utils/format";

export function DependencyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState("auto");
  const [refresh, setRefresh] = useState(false);
  const [nvdEnabled, setNvdEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<OperationResponse<ScanResult> | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then((health) => setNvdEnabled(health.nvd_enabled)).catch(() => setNvdEnabled(false));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a package.json or requirements.txt file.");
      return;
    }
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      setReport(await scanDependencies(file, format, refresh));
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  const components = report?.result.components ?? [];
  const statuses = useMemo(() => ["all", ...new Set(components.map((item) => item.query_status))], [components]);
  const visible = components.filter((component) => {
    const needle = query.trim().toLowerCase();
    const matchesQuery = !needle
      || component.name.toLowerCase().includes(needle)
      || component.advisories.some((advisory) => advisory.id.toLowerCase().includes(needle) || advisory.canonical_id.toLowerCase().includes(needle));
    const matchesStatus = status === "all" || component.query_status === status;
    return matchesQuery && matchesStatus;
  });

  return (
    <section className="space-y-4">
      <PageHeader
        kicker="Supply chain"
        title="Dependency Scanner"
        description="Manifests are parsed locally. Exact versions can be sent to OSV. Packages are not installed and scripts are not run. A package name is not evidence that the package is malicious."
      />
      <form className="panel-flat panel-pad space-y-4" onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
          <FileDrop id="manifest-file" label="Manifest" file={file} maxBytes={MAX_UPLOAD_BYTES} hint="package.json or requirements.txt. The upload limit is 10 MB." onReject={setError} onFile={(next) => { setError(null); setFile(next); }} />
          <div>
            <label className="label" htmlFor="manifest-format">Ecosystem</label>
            <select id="manifest-format" className="select" value={format} onChange={(event) => setFormat(event.target.value)}>
              <option value="auto">Detect from filename</option>
              <option value="npm">npm · package.json</option>
              <option value="pypi">PyPI · requirements.txt</option>
            </select>
            <label className="mt-4 flex items-center gap-2 text-sm">
              <input type="checkbox" checked={refresh} onChange={(event) => setRefresh(event.target.checked)} />
              Refresh cached OSV results
            </label>
          </div>
        </div>
        <p className="text-xs text-[var(--cg-faint)]">
          {nvdEnabled
            ? "NVD enrichment is enabled on the backend. This scan still queries OSV only."
            : "NVD lookups are disabled. This scan uses OSV only."}
        </p>
        <button className="btn btn-primary" disabled={loading} type="submit">Scan manifest</button>
        {loading && <Spinner label="Querying OSV…" />}
        {error && <Alert tone="error">{error}</Alert>}
      </form>
      {report && <ScanResults report={report} visible={visible} statuses={statuses} query={query} status={status} open={open} onQuery={setQuery} onStatus={setStatus} onOpen={setOpen} />}
    </section>
  );
}

function ScanResults({
  report,
  visible,
  statuses,
  query,
  status,
  open,
  onQuery,
  onStatus,
  onOpen,
}: {
  report: OperationResponse<ScanResult>;
  visible: ScanComponent[];
  statuses: string[];
  query: string;
  status: string;
  open: string | null;
  onQuery: (value: string) => void;
  onStatus: (value: string) => void;
  onOpen: (value: string | null) => void;
}) {
  const result = report.result;
  return (
    <article className="panel-flat">
      <div className="flex flex-wrap items-start justify-between gap-3 p-4">
        <div>
          <h2 className="text-sm font-medium">{result.subject_name}</h2>
          <p className="mt-1 text-xs text-[var(--cg-faint)]">
            {result.components.length} packages · {result.queried_count} queried · {result.skipped_count} skipped · {result.source_errors} source errors
          </p>
        </div>
        <Badge value={report.status} />
      </div>
      <div className="space-y-3 px-4">
        <Alert tone="info">{result.no_match_meaning}</Alert>
        {result.warnings.map((warning) => <Alert key={warning} tone="warning">{warning}</Alert>)}
        {result.source_errors > 0 && <Alert tone="error">Some package queries failed. Those rows are partial results, not clean packages.</Alert>}
      </div>
      <div className="grid gap-3 px-4 py-3 md:grid-cols-[minmax(0,1fr)_200px]">
        <input className="field" aria-label="Search packages or advisories" placeholder="Search package or advisory" value={query} onChange={(event) => onQuery(event.target.value)} />
        <select className="select" aria-label="Query status" value={status} onChange={(event) => onStatus(event.target.value)}>
          {statuses.map((item) => <option key={item} value={item}>{item === "all" ? "All query statuses" : item}</option>)}
        </select>
      </div>
      <p className="px-4 pb-2 text-xs text-[var(--cg-faint)]">
        Parser warnings are heuristic. Advisory rows are records returned by OSV. Severity is shown only when that record included it. A missing severity is not treated as low or none.
      </p>
      {visible.length === 0 ? (
        <p className="px-4 py-6 text-sm text-[var(--cg-muted)]">No packages match this filter.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Package</th>
                <th>Version</th>
                <th>Ecosystem</th>
                <th>Advisory</th>
                <th>Source</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((component, index) => {
                const key = `${component.name}-${index}`;
                return (
                  <ComponentRows key={key} component={component} expanded={open === key} onToggle={() => onOpen(open === key ? null : key)} />
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <div className="p-4">
        <button className="btn btn-secondary" type="button" onClick={() => downloadText(`cryptoguard-scan-${report.operation_id}.json`, JSON.stringify(report, null, 2))}>
          <Download size={14} />
          Download scan report
        </button>
        <Limitations items={report.limitations} />
      </div>
    </article>
  );
}

function ComponentRows({ component, expanded, onToggle }: { component: ScanComponent; expanded: boolean; onToggle: () => void }) {
  const advisoryLabel = component.advisories.length === 0 ? "None returned" : component.advisories.map((item) => item.id).join(", ");
  return (
    <>
      <tr>
        <td>
          <button className="sort-btn" type="button" onClick={onToggle} aria-expanded={expanded}>
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            {component.name}
          </button>
          {component.warning && <p className="mt-1 max-w-sm text-xs text-[var(--cg-warning)]">Heuristic: {component.warning}</p>}
        </td>
        <td className="font-mono text-xs">{component.declared_version || "not declared"}</td>
        <td>{component.ecosystem}</td>
        <td className="max-w-xs font-mono text-xs">{advisoryLabel}</td>
        <td>OSV</td>
        <td>
          <Badge value={component.query_status} />
          {component.message && <p className="mt-1 max-w-xs text-xs text-[var(--cg-muted)]">{component.message}</p>}
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={6}>
            <p className="text-xs text-[var(--cg-faint)]">Version status: {component.version_status}. {component.retrieved_at ? `Retrieved ${formatWhen(component.retrieved_at)}${component.cached ? " from cache" : ""}.` : "No retrieval time was returned."}</p>
            {component.advisories.length === 0 && <p className="mt-2 text-sm text-[var(--cg-muted)]">No advisory object was returned for this package.</p>}
            <div className="mt-2 space-y-2">
              {component.advisories.map((advisory) => <AdvisoryBlock key={advisory.id} advisory={advisory} packageName={component.name} />)}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function AdvisoryBlock({ advisory, packageName }: { advisory: Advisory; packageName: string }) {
  return (
    <div className="rounded-lg border border-[var(--cg-line)] p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs">{advisory.id}</span>
        <span className="text-xs text-[var(--cg-faint)]">{advisory.source || "OSV"} · {packageName}</span>
      </div>
      <p className="mt-2">{advisory.summary || "No summary was included in the advisory."}</p>
      <p className="mt-1 text-xs text-[var(--cg-faint)]">{severityText(advisory)}</p>
      <p className="mt-1 text-xs text-[var(--cg-faint)]">Aliases {(advisory.aliases || []).join(", ") || "none"}</p>
      <div className="mt-2 flex flex-wrap gap-3 text-xs">
        {advisory.reference_url && <a className="text-[var(--cg-cyan)] underline" href={advisory.reference_url} target="_blank" rel="noreferrer">Advisory reference</a>}
        {advisory.osv_url && <a className="text-[var(--cg-cyan)] underline" href={advisory.osv_url} target="_blank" rel="noreferrer">OSV record</a>}
      </div>
    </div>
  );
}
