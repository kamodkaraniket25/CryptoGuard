import { useMemo, useState, type FormEvent } from "react";
import { Download } from "lucide-react";
import { Alert, Badge, FileDrop, JsonView, Limitations, PageHeader, Spinner } from "../components/ui";
import { errorMessage, signProvenance, verifyProvenance, type ProvenanceResult, type ProvenanceSignResult } from "../services/api";
import type { OperationResponse } from "../types";
import { downloadText } from "../utils/download";
import { MAX_UPLOAD_BYTES } from "../utils/format";

const sample = `{
  "artifact_sha256": "",
  "source_repository": "https://example.com/demo.git",
  "source_revision": "abc123def",
  "builder_id": "local-builder",
  "build_timestamp": "2026-10-17T00:00:00Z"
}`;

export function ProvenancePage() {
  const [record, setRecord] = useState(sample);
  const [privateKey, setPrivateKey] = useState("");
  const [publicKey, setPublicKey] = useState("");
  const [artifact, setArtifact] = useState<File | null>(null);
  const [signed, setSigned] = useState<OperationResponse<ProvenanceSignResult> | null>(null);
  const [verified, setVerified] = useState<OperationResponse<ProvenanceResult> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const parsed = useMemo(() => readRecord(record), [record]);

  async function onSign(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await signProvenance(record, privateKey);
      setSigned(result);
      setPublicKey(result.result.public_key_pem);
      const body = JSON.parse(record) as Record<string, unknown>;
      body.signature = result.result.signature;
      setRecord(JSON.stringify(body, null, 2));
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  async function onVerify(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setVerified(null);
    try {
      setVerified(await verifyProvenance(record, publicKey, artifact));
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  async function readJsonFile(file: File | null) {
    if (!file) return;
    setRecord(await file.text());
  }

  return (
    <section className="space-y-4">
      <PageHeader
        kicker="Verification"
        title="Provenance Verification"
        description="Digest comparison and signature checking stay separate. Unsigned JSON is not authenticated evidence, and a complete record is not a SLSA evaluation."
      />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <div className="space-y-4">
          <form className="panel-flat panel-pad space-y-3" onSubmit={onSign}>
            <h2 className="text-sm font-medium">Record</h2>
            <FileDrop id="provenance-file" label="Provenance JSON" file={null} hint="Optional. A JSON file replaces the editor contents. It is read in the browser." onFile={(file) => void readJsonFile(file)} />
            <label className="label" htmlFor="provenance-json">Record editor</label>
            <textarea id="provenance-json" className="textarea min-h-52 font-mono text-xs" value={record} onChange={(event) => setRecord(event.target.value)} />
            <label className="label" htmlFor="provenance-private">Private key PEM</label>
            <textarea id="provenance-private" className="textarea font-mono text-xs" value={privateKey} onChange={(event) => setPrivateKey(event.target.value)} />
            <button className="btn btn-primary" type="submit" disabled={loading}>Sign canonical record</button>
            {signed && (
              <>
                <p className="text-sm text-[var(--cg-muted)]">{signed.result.canonicalization}</p>
                <button className="btn btn-secondary" type="button" onClick={() => downloadText("cryptoguard-provenance.json", record)}>
                  <Download size={14} />
                  Download signed record
                </button>
                <Limitations items={signed.limitations} />
              </>
            )}
          </form>
          <form className="panel-flat panel-pad space-y-3" onSubmit={onVerify}>
            <h2 className="text-sm font-medium">Evidence</h2>
            <FileDrop id="artifact-file" label="Artifact file" file={artifact} maxBytes={MAX_UPLOAD_BYTES} hint="Optional. Used only for the digest comparison. The upload limit is 10 MB." onReject={setError} onFile={(next) => { setError(null); setArtifact(next); }} />
            <label className="label" htmlFor="provenance-public">Public key PEM</label>
            <textarea id="provenance-public" className="textarea font-mono text-xs" value={publicKey} onChange={(event) => setPublicKey(event.target.value)} placeholder="Optional. Without it, the signature stays unverified." />
            <button className="btn btn-primary" type="submit" disabled={loading}>Verify provenance</button>
          </form>
        </div>
        <aside className="panel-flat panel-pad space-y-3">
          <h2 className="text-sm font-medium">Parsed record</h2>
          {!parsed && <Alert tone="error">The editor does not contain valid JSON yet.</Alert>}
          {parsed && (
            <dl className="space-y-2 text-sm">
              <Meta label="Source repository" value={parsed.source_repository} />
              <Meta label="Source revision" value={parsed.source_revision} />
              <Meta label="Builder identity" value={parsed.builder_id} />
              <Meta label="Build timestamp" value={parsed.build_timestamp} />
              <Meta label="Recorded digest" value={parsed.artifact_sha256} mono />
            </dl>
          )}
          {loading && <Spinner label="Checking provenance…" />}
          {error && <Alert tone="error">{error}</Alert>}
          {verified && (
            <div className="space-y-1" role="status">
              <h3 className="pt-2 text-sm font-medium">Checks</h3>
              <Check label="Record" status={verified.result.record_status} />
              <Check label="Artifact digest" status={verified.result.digest_status} />
              <Check label="Signature" status={verified.result.signature_status} />
              {verified.result.computed_sha256 && (
                <div>
                  <p className="mb-1 text-xs text-[var(--cg-faint)]">Computed artifact digest</p>
                  <p className="mono-block">{verified.result.computed_sha256}</p>
                </div>
              )}
              {verified.result.recorded_sha256 && (
                <div>
                  <p className="mb-1 text-xs text-[var(--cg-faint)]">Digest stored in the record</p>
                  <p className="mono-block">{verified.result.recorded_sha256}</p>
                </div>
              )}
              {verified.result.missing_evidence.map((item) => (
                <p key={item} className="text-sm text-[var(--cg-warning)]">{item}</p>
              ))}
              {verified.result.notes.map((note) => (
                <p key={note} className="text-sm text-[var(--cg-muted)]">{note}</p>
              ))}
              <button className="btn btn-secondary" type="button" onClick={() => downloadText(`cryptoguard-provenance-${verified.operation_id}.json`, JSON.stringify(verified, null, 2))}>
                <Download size={14} />
                Download report
              </button>
              <Limitations items={verified.limitations} />
            </div>
          )}
          {signed && (
            <div>
              <p className="mb-1 text-xs text-[var(--cg-faint)]">Canonical JSON that was signed</p>
              <JsonView value={signed.result.canonical_json} />
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}

function Meta({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-[var(--cg-faint)]">{label}</dt>
      <dd className={mono ? "break-all font-mono text-xs" : "break-all"}>{value}</dd>
    </div>
  );
}

function Check({ label, status }: { label: string; status: string }) {
  return (
    <div className="check-row">
      <p className="text-sm">{label}</p>
      <div>
        <Badge value={status} />
        <p className="mt-1 text-xs text-[var(--cg-faint)]">{meaning(status)}</p>
      </div>
    </div>
  );
}

function meaning(status: string): string {
  const text = status.toUpperCase();
  if (text.includes("NOT") || text.includes("INCOMPLETE") || text.includes("UNVERIFIED")) return "Evidence for this check is missing or was not supplied.";
  if (text.includes("MISMATCH") || text.includes("INVALID")) return "The supplied evidence failed this check.";
  if (text.includes("MATCH") || text.includes("VALID")) return "The supplied evidence passed this check.";
  return "Reported separately from the other checks.";
}

function readRecord(value: string): Record<string, string> | null {
  try {
    const data = JSON.parse(value) as Record<string, unknown>;
    return {
      source_repository: textOrMissing(data.source_repository),
      source_revision: textOrMissing(data.source_revision),
      builder_id: textOrMissing(data.builder_id),
      build_timestamp: textOrMissing(data.build_timestamp),
      artifact_sha256: textOrMissing(data.artifact_sha256),
    };
  } catch {
    return null;
  }
}

function textOrMissing(value: unknown): string {
  return typeof value === "string" && value.trim() ? value : "Not present in the record";
}
