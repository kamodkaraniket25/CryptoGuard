import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowDown, ArrowUp, Download } from "lucide-react";
import { Alert, Dialog, EmptyState, JsonView, PageHeader, ResultBadge, Skeleton, Spinner, useToast } from "../components/ui";
import { deleteHistory, errorMessage, exportHistory, getHistory, getHistoryDetail } from "../services/api";
import type { HistoryItem, HistoryPage } from "../types";
import { downloadBlob, downloadText } from "../utils/download";
import { formatWhen, operationLabels, recordResult } from "../utils/format";

type SortKey = "created_at" | "operation_type" | "status" | "algorithm";

export function HistoryPage() {
  const push = useToast();
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState<HistoryPage | null>(null);
  const [operationType, setOperationType] = useState("");
  const [status, setStatus] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const limit = 20;

  async function load(nextOffset = offset) {
    setLoading(true);
    setError(null);
    try {
      const query: Record<string, string | number> = { limit, offset: nextOffset };
      if (operationType) query.operation_type = operationType;
      if (status) query.status = status;
      if (dateFrom) query.date_from = dateFrom;
      if (dateTo) query.date_to = dateTo;
      setPage(await getHistory(query));
      setOffset(nextOffset);
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(0);
    // Filters are applied by the form so the first view is the unfiltered page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const id = params.get("operation");
    if (!id) return;
    void getHistoryDetail(id).then(setDetail).catch((reason: unknown) => setError(errorMessage(reason)));
  }, [params]);

  async function onExport() {
    const query: Record<string, string> = {};
    if (operationType) query.operation_type = operationType;
    if (status) query.status = status;
    if (dateFrom) query.date_from = dateFrom;
    if (dateTo) query.date_to = dateTo;
    try {
      downloadBlob("cryptoguard-history.csv", await exportHistory(query));
      push("CSV report downloaded");
    } catch (reason) {
      setError(errorMessage(reason));
    }
  }

  const rows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    const items = (page?.items ?? []).filter((item) => {
      if (!needle) return true;
      return [item.operation_id, item.operation_type, item.algorithm, item.file_name, item.status]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    });
    return [...items].sort((left, right) => compare(left, right, sortKey, sortDir));
  }, [page, search, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((dir) => (dir === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function closeDetail() {
    setDetail(null);
    const next = new URLSearchParams(params);
    next.delete("operation");
    setParams(next, { replace: true });
  }

  return (
    <section className="space-y-4">
      <PageHeader
        kicker="Management"
        title="Reports"
        description="These are real verification records stored by CryptoGuard. Private keys, HMAC secrets, and uploaded file bytes are not included. Search filters the loaded page. Operation, status, and date filters are applied by the backend."
        actions={<button className="btn btn-secondary" type="button" onClick={() => void onExport()}><Download size={14} /> Export CSV</button>}
      />
      <form className="panel-flat grid gap-3 p-4 md:grid-cols-4" onSubmit={(event) => { event.preventDefault(); void load(0); }}>
        <select className="select" aria-label="Operation type" value={operationType} onChange={(event) => setOperationType(event.target.value)}>
          <option value="">All operations</option>
          {Object.entries(operationLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <select className="select" aria-label="Result status" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          <option value="success">Recorded or passed</option>
          <option value="failed">Failed</option>
          <option value="warning">Warning</option>
          <option value="not_verified">Not verified</option>
        </select>
        <input className="field" aria-label="From date" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
        <input className="field" aria-label="To date" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        <input className="field md:col-span-2" aria-label="Filter loaded records" placeholder="Filter loaded records" value={search} onChange={(event) => setSearch(event.target.value)} />
        <button className="btn btn-primary" type="submit">Apply filters</button>
      </form>
      {loading && !page && (
        <div className="panel-flat space-y-2 p-4" aria-hidden="true">
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
        </div>
      )}
      {loading && <Spinner label="Loading history…" />}
      {error && <Alert tone="error" onRetry={() => void load(offset)}>{error}</Alert>}
      {page && page.total === 0 && (
        <div className="panel-flat">
          <EmptyState
            title={operationType || status || dateFrom || dateTo ? "No operations match these filters." : "No verification history yet"}
            body={operationType || status || dateFrom || dateTo
              ? "Try a wider operation type, status, or date range. Records appear only after a real check is stored."
              : "Calculate a file hash, authenticate a message, or verify a signature. Those results will appear here."}
            action={!operationType && !status && !dateFrom && !dateTo ? <Link className="btn btn-primary" to="/integrity">Start verification</Link> : undefined}
          />
        </div>
      )}
      {page && page.items.length > 0 && (
        <div className="panel-flat">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <Sortable label="Time" column="created_at" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                  <th>Identifier</th>
                  <Sortable label="Operation" column="operation_type" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                  <Sortable label="Algorithm" column="algorithm" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                  <Sortable label="Status" column="status" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr key={item.operation_id}>
                    <td>{formatWhen(item.created_at)}</td>
                    <td className="font-mono text-xs">{item.operation_id.slice(0, 8)}</td>
                    <td>{operationLabels[item.operation_type] || item.operation_type}</td>
                    <td className="font-mono text-xs">{item.algorithm || "—"}</td>
                    <td><ResultBadge value={recordResult(item.operation_type, item.status, item.verdict)} /></td>
                    <td className="space-x-2 whitespace-nowrap">
                      <button className="btn btn-secondary" type="button" onClick={() => void getHistoryDetail(item.operation_id).then(setDetail)}>View</button>
                      <button className="btn btn-ghost" type="button" onClick={() => { if (window.confirm("Delete this local history record?")) void deleteHistory(item.operation_id).then(() => load(offset)); }}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length === 0 && <p className="px-4 py-4 text-sm text-[var(--cg-muted)]">No loaded records match that text. Backend filters are unchanged.</p>}
          <div className="flex items-center justify-between gap-3 p-4 text-sm">
            <button className="btn btn-secondary" type="button" disabled={offset === 0} onClick={() => void load(Math.max(0, offset - limit))}>Previous</button>
            <span>{offset + 1}–{Math.min(offset + limit, page.total)} of {page.total}</span>
            <button className="btn btn-secondary" type="button" disabled={offset + limit >= page.total} onClick={() => void load(offset + limit)}>Next</button>
          </div>
        </div>
      )}
      {detail && (
        <Dialog title={`Report ${String(detail.operation_id ?? "")}`} onClose={closeDetail}>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-sm font-medium">Report {String(detail.operation_id ?? "")}</h2>
            <button className="btn btn-secondary" type="button" onClick={() => { downloadText(`cryptoguard-${String(detail.operation_id)}.json`, JSON.stringify(detail, null, 2)); push("JSON report downloaded"); }}>Download JSON</button>
          </div>
          <JsonView value={detail} />
        </Dialog>
      )}
    </section>
  );
}

function Sortable({ label, column, sortKey, sortDir, onSort }: { label: string; column: SortKey; sortKey: SortKey; sortDir: "asc" | "desc"; onSort: (key: SortKey) => void }) {
  const active = sortKey === column;
  return (
    <th>
      <button className="sort-btn" type="button" onClick={() => onSort(column)}>
        {label}
        {active && (sortDir === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}
      </button>
    </th>
  );
}

function compare(left: HistoryItem, right: HistoryItem, key: SortKey, dir: "asc" | "desc"): number {
  const a = String(left[key] ?? "");
  const b = String(right[key] ?? "");
  const result = a.localeCompare(b);
  return dir === "asc" ? result : -result;
}
