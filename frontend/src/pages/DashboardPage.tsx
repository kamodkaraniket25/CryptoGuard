import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowRight, FileKey2, Fingerprint, KeyRound, RefreshCw } from "lucide-react";
import { Alert, Badge, BrandMark, EmptyState, ResultBadge, Skeleton } from "../components/ui";
import { errorMessage, getDashboard, getHealth } from "../services/api";
import type { DashboardStats, HealthResponse } from "../types";
import { formatWhen, operationLabels, recordResult } from "../utils/format";

const chartColors = ["#3dbe8b", "#e06b6b", "#e2b15a", "#3b82f6", "#8b7cf6", "#67e8f9", "#94a3b8"];

const features = [
  {
    title: "SHA-256 Integrity",
    body: "Hash a file and compare it with a digest published by a source you trust.",
    to: "/integrity",
    action: "Open Hash Checker",
    icon: Fingerprint,
  },
  {
    title: "HMAC Authentication",
    body: "Confirm a shared secret produced the authentication tag for these exact bytes.",
    to: "/hmac",
    action: "Open HMAC Verifier",
    icon: KeyRound,
  },
  {
    title: "Digital Signatures",
    body: "Sign a record with RSA-PSS and check it with the matching public key.",
    to: "/signatures",
    action: "Open Digital Signatures",
    icon: FileKey2,
  },
];

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadedAt, setLoadedAt] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStats(await getDashboard());
      setLoadedAt(new Date().toISOString());
    } catch (reason) {
      setStats(null);
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((result) => {
        if (!active) return;
        setHealth(result);
        setHealthError(null);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setHealth(null);
        setHealthError(errorMessage(reason));
      });
    return () => {
      active = false;
    };
  }, []);

  const outcomes = stats
    ? [
        { name: "Integrity match", value: stats.integrity_success },
        { name: "Integrity mismatch", value: stats.integrity_failed },
        { name: "Hash without reference", value: stats.integrity_not_verified },
        { name: "HMAC valid", value: stats.hmac_verified_success },
        { name: "HMAC invalid", value: stats.hmac_verified_failed },
        { name: "Signature valid", value: stats.signatures_verified_success },
        { name: "Signature invalid", value: stats.signatures_verified_failed },
      ].filter((item) => item.value > 0)
    : [];

  return (
    <section className="space-y-4">
      <section className="hero-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <BrandMark size={44} />
            <div>
              <p className="kicker mb-0">CryptoGuard</p>
              <p className="text-sm text-[var(--cg-muted)]">Software Supply Chain Integrity Verification Framework</p>
            </div>
          </div>
          <button className="btn btn-secondary" type="button" onClick={() => void load()} disabled={loading}>
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
        <h1 className="hero-title">Verify what you are about to trust.</h1>
        <p className="hero-tagline">Verify Integrity. Authenticate Messages. Trust Digital Signatures.</p>
        <p className="lede max-w-[68ch]">
          CryptoGuard checks a file digest, a shared-secret authentication tag, or an RSA signature on the backend.
          PASS means the evidence you supplied matched. FAIL means it did not. NOT VERIFIED means a comparison could not be made.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <Link className="btn btn-primary" to="/integrity">Start Verification</Link>
          <Link className="btn btn-secondary" to="/documentation">How to demonstrate</Link>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link key={feature.to} className="feature-link" to={feature.to}>
                <span className="icon-tile"><Icon size={16} /></span>
                <h2 className="text-sm font-semibold">{feature.title}</h2>
                <p className="text-sm leading-6 text-[var(--cg-muted)]">{feature.body}</p>
                <span className="mt-auto inline-flex items-center gap-1 text-sm text-[var(--cg-cyan)]">
                  {feature.action}
                  <ArrowRight size={14} />
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="panel-flat panel-pad">
        <h2 className="text-sm font-semibold">Verification workflow</h2>
        <p className="mb-3 text-xs text-[var(--cg-faint)]">Every check follows the same path. The cryptography runs on the backend.</p>
        <ol className="pipeline">
          <li>
            <span className="pipeline-index">01</span>
            <h3 className="text-sm font-medium">Input</h3>
            <p className="mt-1 text-sm text-[var(--cg-muted)]">Upload a file, or enter a message, secret, and key.</p>
          </li>
          <li>
            <span className="pipeline-index">02</span>
            <h3 className="text-sm font-medium">Cryptographic verification</h3>
            <p className="mt-1 text-sm text-[var(--cg-muted)]">SHA-256, HMAC-SHA256, or RSA-PSS with SHA-256 runs against that input.</p>
          </li>
          <li>
            <span className="pipeline-index">03</span>
            <h3 className="text-sm font-medium">Result</h3>
            <p className="mt-1 text-sm text-[var(--cg-muted)]">Read PASS, FAIL, or NOT VERIFIED, then open the stored report.</p>
          </li>
        </ol>
      </section>

      <section className="status-legend" aria-label="Result meanings">
        <article>
          <Badge value="PASS" />
          <p className="mt-2 text-sm text-[var(--cg-muted)]">The supplied evidence matched. The check does not claim the software is safe.</p>
        </article>
        <article>
          <Badge value="FAIL" />
          <p className="mt-2 text-sm text-[var(--cg-muted)]">The digest, tag, or signature did not match. Something in the evidence is different.</p>
        </article>
        <article>
          <Badge value="NOT VERIFIED" />
          <p className="mt-2 text-sm text-[var(--cg-muted)]">A comparison was not possible, for example because no trusted reference hash was entered.</p>
        </article>
      </section>

      {error && <Alert tone="error" onRetry={() => void load()}>{error}</Alert>}
      {loading && !stats && (
        <div className="grid gap-3 lg:grid-cols-3">
          <Skeleton className="h-56 lg:col-span-2" />
          <Skeleton className="h-56" />
        </div>
      )}

      {stats && (
        <div className="space-y-4">
          {stats.total_operations > 0 && (
            <div className="grid gap-4 lg:grid-cols-5">
              <article className="panel-flat p-4 lg:col-span-3">
                <div className="mb-3 flex items-end justify-between gap-3">
                  <div>
                    <h2 className="text-sm font-semibold">Recorded activity</h2>
                    <p className="text-xs text-[var(--cg-faint)]">{stats.total_operations} stored operations over the last 14 days.</p>
                  </div>
                </div>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats.activity}>
                      <CartesianGrid stroke="rgba(226,232,240,0.08)" vertical={false} />
                      <XAxis dataKey="date" stroke="#8b97ab" tick={{ fontSize: 11 }} tickFormatter={(value: string) => value.slice(5)} />
                      <YAxis allowDecimals={false} stroke="#8b97ab" width={28} tick={{ fontSize: 11 }} />
                      <Tooltip content={<ChartTip />} />
                      <Bar dataKey="count" name="Operations" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </article>
              <article className="panel-flat p-4 lg:col-span-2">
                <h2 className="text-sm font-semibold">Stored outcomes</h2>
                <p className="mb-3 text-xs text-[var(--cg-faint)]">Counts from integrity, HMAC, and signature records.</p>
                {outcomes.length === 0 ? (
                  <p className="text-sm text-[var(--cg-muted)]">No comparable verification outcomes are stored yet.</p>
                ) : (
                  <div className="grid items-center gap-3 sm:grid-cols-[150px_minmax(0,1fr)]">
                    <div className="h-36">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={outcomes} dataKey="value" nameKey="name" innerRadius={40} outerRadius={64} paddingAngle={outcomes.length > 1 ? 2 : 0}>
                            {outcomes.map((item, index) => (
                              <Cell key={item.name} fill={chartColors[index % chartColors.length]} />
                            ))}
                          </Pie>
                          <Tooltip content={<ChartTip />} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <ul className="space-y-1.5 text-xs">
                      {outcomes.map((item, index) => (
                        <li key={item.name} className="flex items-center justify-between gap-3">
                          <span className="flex min-w-0 items-center gap-2">
                            <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: chartColors[index % chartColors.length] }} />
                            <span className="truncate">{item.name}</span>
                          </span>
                          <span className="font-mono">{item.value}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </article>
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-3">
            <article className="panel-flat lg:col-span-2">
              <div className="flex items-center justify-between px-4 pt-4">
                <div>
                  <h2 className="text-sm font-semibold">Recent verification activity</h2>
                  <p className="text-xs text-[var(--cg-faint)]">
                    {stats.recent_operations[0] ? `Latest record ${formatWhen(stats.recent_operations[0].created_at)}.` : "History is read from the local database."}
                    {loadedAt ? ` Loaded ${formatWhen(loadedAt)}.` : ""}
                  </p>
                </div>
                <Link className="text-xs text-[var(--cg-cyan)]" to="/reports">Open reports</Link>
              </div>
              {stats.recent_operations.length === 0 ? (
                <EmptyState
                  title="No verification operations have been recorded yet."
                  body="Calculate a file hash, authenticate a message, or verify a signature. This list fills from those stored results."
                  action={<Link className="btn btn-primary" to="/integrity">Perform the first verification</Link>}
                />
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Operation</th>
                        <th>Status</th>
                        <th>Algorithm</th>
                        <th>When</th>
                        <th>Identifier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.recent_operations.map((item) => (
                        <tr key={item.operation_id}>
                          <td>{operationLabels[item.operation_type] || item.operation_type}</td>
                          <td><ResultBadge value={recordResult(item.operation_type, item.status, item.verdict)} /></td>
                          <td className="font-mono text-xs">{item.algorithm || "—"}</td>
                          <td>{formatWhen(item.created_at)}</td>
                          <td>
                            <Link className="font-mono text-xs text-[var(--cg-cyan)]" to={`/reports?operation=${item.operation_id}`}>
                              {item.operation_id.slice(0, 8)}
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
            <article className="panel-flat p-4">
              <h2 className="text-sm font-semibold">System health</h2>
              <p className="mb-3 text-xs text-[var(--cg-faint)]">Live status from the backend health endpoint. Source rows are the last stored check.</p>
              <div className="space-y-3 border-b border-[var(--cg-line)] pb-3">
                {health && (
                  <>
                    <HealthRow label="Backend" value={`API ${health.status}`} />
                    <HealthRow label="Database" value={health.database} />
                    <HealthRow label="Version" value={health.version} />
                  </>
                )}
                {!health && healthError && <Alert tone="error">{healthError}</Alert>}
                {!health && !healthError && <Skeleton className="h-16" />}
              </div>
              <div className="mt-3 space-y-3">
                {stats.sources.length === 0 && <p className="text-sm text-[var(--cg-muted)]">No source records were returned.</p>}
                {stats.sources.map((source) => (
                  <div key={source.id} className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm">{source.name}</p>
                      <p className="text-xs text-[var(--cg-faint)]">
                        {source.checked_at ? `Last check ${formatWhen(source.checked_at)}` : "Not checked"}
                      </p>
                    </div>
                    <Badge value={source.status} />
                  </div>
                ))}
              </div>
            </article>
          </div>
          {stats.notes.length > 0 && (
            <ul className="space-y-1 text-xs text-[var(--cg-faint)]">
              {stats.notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

function HealthRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="text-[var(--cg-faint)]">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function ChartTip({ active, payload, label }: { active?: boolean; payload?: { name?: string; value?: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-[var(--cg-line-strong)] bg-[#172033] px-2 py-1.5 text-xs">
      {label && <p className="text-[var(--cg-faint)]">{label}</p>}
      {payload.map((item) => (
        <p key={`${item.name}-${item.value}`}>{item.name}: {item.value}</p>
      ))}
    </div>
  );
}
