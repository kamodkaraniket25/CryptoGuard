import { useState, type FormEvent } from "react";
import { Alert, CopyButton, DownloadButton, Limitations, PageHeader, ResultBanner, SecretInput, Spinner, useToast } from "../components/ui";
import { errorMessage, generateHmac, verifyHmac, type HmacGenerateResult } from "../services/api";
import type { OperationResponse } from "../types";
import { validateHmacTag } from "../utils/format";

export function HmacPage() {
  const push = useToast();
  const [message, setMessage] = useState("The backup completed at 02:00.");
  const [secret, setSecret] = useState("");
  const [verifyMessage, setVerifyMessage] = useState("");
  const [verifySecret, setVerifySecret] = useState("");
  const [tag, setTag] = useState("");
  const [busy, setBusy] = useState<"generate" | "verify" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generated, setGenerated] = useState<OperationResponse<HmacGenerateResult> | null>(null);
  const [secretVisible, setSecretVisible] = useState(false);
  const [verdict, setVerdict] = useState<OperationResponse<{ verdict: string }> | null>(null);

  async function onGenerate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setGenerated(null);
    setVerdict(null);
    setBusy("generate");
    try {
      const result = await generateHmac(message, secret);
      setGenerated(result);
      setSecretVisible(true);
      setVerifyMessage(message);
      setVerifySecret(result.result.secret);
      setTag(result.result.tag);
      push("HMAC tag created");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(null);
    }
  }

  async function onVerify(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setVerdict(null);
    const validation = validateHmacTag(tag);
    if (validation) {
      setError(validation);
      return;
    }
    if (!verifySecret) {
      setError("Enter the shared secret before verifying the tag.");
      return;
    }
    setBusy("verify");
    try {
      setVerdict(await verifyHmac(verifyMessage, verifySecret, tag.trim().toLowerCase()));
      push("HMAC check complete");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(null);
    }
  }

  function clearSecrets() {
    setSecret("");
    setVerifySecret("");
    setSecretVisible(false);
    setGenerated((current) => (current ? { ...current, result: { ...current.result, secret: "" } } : current));
    push("Secret cleared from this page");
  }

  return (
    <section className="space-y-4">
      <PageHeader
        kicker="Verification"
        title="HMAC Verifier"
        description="HMAC-SHA256 shows that someone who knows the shared secret produced this tag for these exact UTF-8 bytes. The secret is not written to history, reports, or logs."
      />
      {error && <Alert tone="error">{error}</Alert>}
      <div className="grid items-start gap-4 xl:grid-cols-2">
        <form className="panel-flat panel-pad space-y-4" onSubmit={onGenerate} aria-busy={busy === "generate"}>
          <div>
            <p className="section-label">Generate</p>
            <h2 className="text-sm font-semibold">Create an authentication tag</h2>
            <p className="mt-1 text-sm text-[var(--cg-muted)]">Leave the secret blank and CryptoGuard will create one for this request only.</p>
          </div>
          <div>
            <label className="label" htmlFor="hmac-message">Message</label>
            <textarea id="hmac-message" className="textarea" value={message} onChange={(event) => setMessage(event.target.value)} />
          </div>
          <SecretInput
            id="hmac-secret"
            label="Shared secret"
            value={secret}
            onChange={setSecret}
            placeholder="Leave blank to generate a secret"
            hint="Both parties must already know this secret. CryptoGuard does not store it."
          />
          <button className="btn btn-primary" disabled={busy !== null} type="submit">Generate authentication tag</button>
          {busy === "generate" && <Spinner label="Generating HMAC tag…" />}
          {generated && (
            <div className="space-y-3 border-t border-[var(--cg-line)] pt-4">
              <Alert tone="warning">This secret is in the browser for the demonstration. It is not saved in the database. Clear it when you are finished.</Alert>
              <div>
                <div className="mb-1 flex items-center justify-between gap-2">
                  <p className="text-xs text-[var(--cg-faint)]">Secret {generated.result.secret_generated ? "· generated for this request" : "· supplied by you"}</p>
                  <button className="btn btn-ghost" type="button" onClick={() => setSecretVisible((value) => !value)}>
                    {secretVisible ? "Hide secret" : "Show secret"}
                  </button>
                </div>
                <p className={`mono-block ${generated.result.secret && !secretVisible ? "secret-mask" : ""}`}>{generated.result.secret || "Cleared from this page"}</p>
              </div>
              <div className="digest-block">
                <p className="mb-1 text-xs text-[var(--cg-faint)]">Authentication tag</p>
                <p className="break-all font-mono text-xs leading-5">{generated.result.tag}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <CopyButton value={generated.result.tag} label="Copy tag" />
                {generated.result.secret && <CopyButton value={generated.result.secret} label="Copy secret" />}
                <DownloadButton
                  filename={`cryptoguard-hmac-${generated.operation_id}.json`}
                  content={JSON.stringify({ message, tag: generated.result.tag, algorithm: "HMAC-SHA256" }, null, 2)}
                  label="Download tag report"
                />
                <button className="btn btn-secondary" type="button" onClick={clearSecrets}>Clear secret</button>
              </div>
              <Limitations items={generated.limitations} />
            </div>
          )}
        </form>
        <form className="panel-flat panel-pad space-y-4" onSubmit={onVerify} aria-busy={busy === "verify"}>
          <div>
            <p className="section-label">Verify</p>
            <h2 className="text-sm font-semibold">Check an authentication tag</h2>
            <p className="mt-1 text-sm text-[var(--cg-muted)]">A matching tag is PASS. A changed message, secret, or tag is FAIL.</p>
          </div>
          <div>
            <label className="label" htmlFor="verify-message">Message</label>
            <textarea id="verify-message" className="textarea" value={verifyMessage} onChange={(event) => setVerifyMessage(event.target.value)} />
          </div>
          <SecretInput
            id="verify-secret"
            label="Shared secret"
            value={verifySecret}
            onChange={setVerifySecret}
            hint="Use the same secret that created the tag. Change it to demonstrate FAIL."
          />
          <div>
            <label className="label" htmlFor="verify-tag">Authentication tag</label>
            <input id="verify-tag" className="field font-mono" spellCheck={false} value={tag} onChange={(event) => setTag(event.target.value)} placeholder="64 hexadecimal characters" />
          </div>
          <button className="btn btn-primary" disabled={busy !== null} type="submit">Verify tag</button>
          {busy === "verify" && <Spinner label="Checking HMAC…" />}
          {verdict && (
            <ResultBanner
              verdict={verdict.result.verdict}
              technical={verdict.result.verdict}
              explanation={
                verdict.result.verdict === "VALID"
                  ? "PASS means this tag matches the message and shared secret. HMAC does not identify a person, and it does not provide non-repudiation."
                  : "FAIL means the tag does not match this message and secret. A changed message, a different secret, or a wrong tag produces this result."
              }
            />
          )}
          {verdict && <Limitations items={verdict.limitations} />}
        </form>
      </div>
      <article className="panel-flat panel-pad">
        <h2 className="text-sm font-semibold">What shared-secret authentication shows</h2>
        <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
          Both parties must already share the secret through a channel they trust. A valid tag shows the message was not changed by someone who lacks that secret. It does not name a person. The secret is omitted from the downloadable tag report and from verification history.
        </p>
      </article>
    </section>
  );
}
