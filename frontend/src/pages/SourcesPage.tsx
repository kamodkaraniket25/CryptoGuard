import { useEffect, useState } from "react";
import { Alert, Badge, PageHeader, Spinner } from "../components/ui";
import { checkSources, errorMessage, getSources } from "../services/api";
import type { SourceCatalog, SourceRecord } from "../types";
import { formatWhen } from "../utils/format";

export function SourcesPage() {
  const [catalog, setCatalog] = useState<SourceCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setCatalog(await getSources());
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCheck() {
    setChecking(true);
    setError(null);
    try {
      await checkSources();
      await load();
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setChecking(false);
    }
  }

  return (
    <section className="space-y-4">
      <PageHeader
        kicker="Supply chain"
        title="Datasets & Sources"
        description="These are the external sources CryptoGuard can query. A status of NOT CHECKED means this installation has not asked the source yet. Availability is not a security result."
        actions={<button className="btn btn-primary" type="button" onClick={() => void onCheck()} disabled={checking}>Check source status</button>}
      />
      {catalog && (
        <div className="grid gap-3 md:grid-cols-3">
          <Fact label="NVD lookups" value={catalog.nvd_enabled ? "Enabled" : "Disabled"} />
          <Fact label="NVD API key" value={catalog.nvd_key_configured ? "Configured" : "Not configured"} />
          <Fact label="OSV cache TTL" value={`${Math.round(catalog.cache_ttl_seconds / 3600)} hours`} />
        </div>
      )}
      {checking && <Spinner label="Running bounded source checks…" />}
      {loading && <Spinner label="Loading source catalog…" />}
      {error && <Alert tone="error" onRetry={() => void load()}>{error}</Alert>}
      {catalog && <Alert tone="info">{catalog.note}</Alert>}
      <div className="space-y-3">
        {catalog?.sources.map((source) => <SourceCard key={source.id} source={source} />)}
      </div>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel-flat px-4 py-3">
      <p className="text-[11px] uppercase tracking-[0.08em] text-[var(--cg-faint)]">{label}</p>
      <p className="mt-1 text-sm">{value}</p>
    </div>
  );
}

function sourceKind(source: SourceRecord): string {
  if (source.data_is_downloaded) return "Downloaded dataset";
  if (source.category.toLowerCase().includes("spec")) return "SBOM specification and schema";
  if (/live|api/i.test(source.access_method)) return "Live vulnerability API";
  return source.category;
}

function SourceCard({ source }: { source: SourceRecord }) {
  const kind = sourceKind(source);
  const succeeded = source.status === "AVAILABLE" || source.status === "DEGRADED";
  return (
    <article className="panel-flat panel-pad space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-medium">{source.name}</h2>
          <p className="mt-1 text-sm text-[var(--cg-muted)]">{source.purpose}</p>
        </div>
        <Badge value={source.status} />
      </div>
      <dl className="grid gap-3 text-sm md:grid-cols-2">
        <div><dt className="text-xs text-[var(--cg-faint)]">Kind</dt><dd>{kind}</dd></div>
        <div><dt className="text-xs text-[var(--cg-faint)]">Integration</dt><dd>{source.access_method}</dd></div>
        <div><dt className="text-xs text-[var(--cg-faint)]">Last checked</dt><dd>{source.checked_at ? formatWhen(source.checked_at) : "Not checked"}</dd></div>
        <div><dt className="text-xs text-[var(--cg-faint)]">Last successful retrieval</dt><dd>{succeeded ? formatWhen(source.checked_at) : "No successful check is stored."}</dd></div>
        <div className="md:col-span-2"><dt className="text-xs text-[var(--cg-faint)]">Fields used</dt><dd>{source.fields_used.join(", ")}</dd></div>
      </dl>
      <p className="text-sm">
        <a className="text-[var(--cg-cyan)] underline" href={source.website}>Website</a>
        {" · "}
        <a className="text-[var(--cg-cyan)] underline" href={source.documentation_url}>Documentation</a>
      </p>
      <p className="break-all font-mono text-xs text-[var(--cg-faint)]">{source.endpoint}</p>
      {source.latency_ms !== null && <p className="text-xs text-[var(--cg-faint)]">Last check latency {source.latency_ms} ms</p>}
      {source.error_category && <p className="text-xs text-[var(--cg-warning)]">{source.error_category}{source.detail ? ` · ${source.detail}` : ""}</p>}
      <div>
        <p className="text-xs uppercase tracking-[0.08em] text-[var(--cg-faint)]">Known limitations</p>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-[var(--cg-muted)]">
          {source.limitations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </div>
      <p className="text-xs leading-5 text-[var(--cg-faint)]">{source.attribution}</p>
      <p className="text-xs leading-5 text-[var(--cg-faint)]">{source.license_note}</p>
    </article>
  );
}
