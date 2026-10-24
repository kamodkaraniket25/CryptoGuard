import { useEffect, useState, type FormEvent } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Alert, CopyButton, DownloadButton, Limitations, PageHeader, ResultBanner, Spinner, useToast } from "../components/ui";
import { errorMessage, generateKeys, signMessage, verifySignature, type KeyResult, type SignResult } from "../services/api";
import type { OperationResponse } from "../types";

export function SignaturePage() {
  const push = useToast();
  const [keys, setKeys] = useState<OperationResponse<KeyResult> | null>(null);
  const [privateKey, setPrivateKey] = useState("");
  const [showPrivate, setShowPrivate] = useState(false);
  const [publicKey, setPublicKey] = useState("");
  const [fingerprint, setFingerprint] = useState("");
  const [message, setMessage] = useState("Release candidate 1.4.0");
  const [verifyMessage, setVerifyMessage] = useState("Release candidate 1.4.0");
  const [verifyPublicKey, setVerifyPublicKey] = useState("");
  const [signature, setSignature] = useState("");
  const [signed, setSigned] = useState<OperationResponse<SignResult> | null>(null);
  const [verdict, setVerdict] = useState<string | null>(null);
  const [limitations, setLimitations] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<"keys" | "sign" | "verify" | null>(null);

  useEffect(() => {
    let cancelled = false;
    const pem = (verifyPublicKey || publicKey).trim();
    if (!pem || !globalThis.crypto?.subtle) {
      setFingerprint("");
      return;
    }
    void crypto.subtle.digest("SHA-256", new TextEncoder().encode(pem)).then((buffer) => {
      if (cancelled) return;
      const hex = [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
      setFingerprint(hex);
    });
    return () => {
      cancelled = true;
    };
  }, [publicKey, verifyPublicKey]);

  async function onKeygen() {
    setLoading("keys");
    setError(null);
    try {
      const result = await generateKeys();
      setKeys(result);
      setPrivateKey(result.result.private_key_pem);
      setPublicKey(result.result.public_key_pem);
      setVerifyPublicKey(result.result.public_key_pem);
      setShowPrivate(false);
      push("Key pair generated");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(null);
    }
  }

  async function onSign(event: FormEvent) {
    event.preventDefault();
    if (!privateKey.trim()) {
      setError("Generate or paste a private key before signing.");
      return;
    }
    setLoading("sign");
    setError(null);
    setSigned(null);
    try {
      const result = await signMessage(message, privateKey);
      setSigned(result);
      setSignature(result.result.signature);
      setPublicKey(result.result.public_key_pem);
      setVerifyPublicKey(result.result.public_key_pem);
      setVerifyMessage(message);
      push("Record signed");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(null);
    }
  }

  async function onVerify(event: FormEvent) {
    event.preventDefault();
    if (!verifyPublicKey.trim() || !signature.trim()) {
      setError("A public key and a signature are required before verification.");
      return;
    }
    setLoading("verify");
    setError(null);
    setVerdict(null);
    try {
      const result = await verifySignature(verifyMessage, verifyPublicKey, signature);
      setVerdict(result.result.verdict);
      setLimitations(result.limitations);
      push("Signature check complete");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(null);
    }
  }

  return (
    <section className="space-y-4">
      <PageHeader
        kicker="Verification"
        title="Digital Signatures"
        description="Keys are RSA-2048. Signatures use RSA-PSS with SHA-256. PASS means the supplied public key accepts the signature for these exact bytes. It identifies a person only when you already trust that public key."
      />
      {error && <Alert tone="error">{error}</Alert>}
      <article className="panel-flat panel-pad space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="section-label">Key pair</p>
            <h2 className="text-sm font-semibold">Public key for verification, private key for signing</h2>
            <p className="mt-1 max-w-[70ch] text-sm text-[var(--cg-muted)]">
              The private key stays in this browser session and is hidden until you reveal it. CryptoGuard does not store it.
            </p>
          </div>
          <button className="btn btn-primary" type="button" onClick={() => void onKeygen()} disabled={loading !== null}>Generate key pair</button>
        </div>
        {loading === "keys" && <Spinner label="Generating RSA-2048 key pair…" />}
        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <div className="mb-1 flex items-center justify-between gap-2">
              <label className="label mb-0" htmlFor="private-key">Private key PEM</label>
              <button className="btn btn-ghost" type="button" onClick={() => setShowPrivate((value) => !value)} aria-label={showPrivate ? "Hide private key" : "Show private key"}>
                {showPrivate ? <EyeOff size={14} /> : <Eye size={14} />}
                {showPrivate ? "Hide" : "Show"}
              </button>
            </div>
            <textarea
              id="private-key"
              className={`textarea min-h-36 font-mono text-xs ${showPrivate ? "" : "secret-mask"}`}
              spellCheck={false}
              autoComplete="off"
              value={privateKey}
              onChange={(event) => setPrivateKey(event.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="public-key">Public key PEM</label>
            <textarea
              id="public-key"
              className="textarea min-h-36 font-mono text-xs"
              spellCheck={false}
              value={publicKey}
              onChange={(event) => {
                setPublicKey(event.target.value);
                setVerifyPublicKey(event.target.value);
              }}
            />
          </div>
        </div>
        {fingerprint && (
          <div className="digest-block">
            <p className="mb-1 text-xs text-[var(--cg-faint)]">SHA-256 of the public key text. This is not a certificate identity.</p>
            <p className="break-all font-mono text-xs leading-5">{fingerprint}</p>
          </div>
        )}
        <div className="flex flex-wrap gap-2">
          {publicKey && <CopyButton value={publicKey} label="Copy public key" />}
          {publicKey && <DownloadButton filename="cryptoguard-public.pem" content={publicKey} mime="application/x-pem-file" label="Download public key" />}
          {privateKey && (
            <DownloadButton filename="cryptoguard-private.pem" content={privateKey} mime="application/x-pem-file" label="Download private key" />
          )}
        </div>
        <p className="text-xs text-[var(--cg-faint)]">RSA-2048 · PSS · SHA-256{keys ? ` · ${keys.result.key_size}-bit` : ""}</p>
        {keys && <Limitations items={keys.limitations} />}
      </article>

      <div className="grid items-start gap-4 xl:grid-cols-2">
        <form className="panel-flat panel-pad space-y-3" onSubmit={onSign} aria-busy={loading === "sign"}>
          <p className="section-label">Sign</p>
          <h2 className="text-sm font-semibold">Sign a record</h2>
          <p className="text-sm text-[var(--cg-muted)]">The private key above signs this UTF-8 message. The signature is copied into the verify panel.</p>
          <label className="label" htmlFor="sign-message">Message or record</label>
          <textarea id="sign-message" className="textarea" value={message} onChange={(event) => setMessage(event.target.value)} />
          <button className="btn btn-primary" disabled={loading !== null} type="submit">Sign message</button>
          {loading === "sign" && <Spinner label="Signing record…" />}
          {signed && (
            <>
              <p className="text-xs text-[var(--cg-faint)]">Signature · {signed.result.encoding}</p>
              <p className="mono-block">{signed.result.signature}</p>
              <div className="flex flex-wrap gap-2">
                <CopyButton value={signed.result.signature} label="Copy signature" />
                <DownloadButton
                  filename="cryptoguard-signed-message.json"
                  content={JSON.stringify({ message, signature: signed.result.signature, public_key_pem: signed.result.public_key_pem, algorithm: "RSA-2048-PSS-SHA256" }, null, 2)}
                  label="Download signed record"
                />
              </div>
              <Limitations items={signed.limitations} />
            </>
          )}
        </form>
        <form className="panel-flat panel-pad space-y-3" onSubmit={onVerify} aria-busy={loading === "verify"}>
          <p className="section-label">Verify</p>
          <h2 className="text-sm font-semibold">Verify a signature</h2>
          <p className="text-sm text-[var(--cg-muted)]">PASS means this public key accepts the signature. Edit the message to demonstrate FAIL.</p>
          <label className="label" htmlFor="verify-message">Message</label>
          <textarea id="verify-message" className="textarea" value={verifyMessage} onChange={(event) => setVerifyMessage(event.target.value)} />
          <label className="label" htmlFor="verify-public">Public key PEM</label>
          <textarea id="verify-public" className="textarea min-h-28 font-mono text-xs" spellCheck={false} value={verifyPublicKey} onChange={(event) => setVerifyPublicKey(event.target.value)} />
          <label className="label" htmlFor="signature-value">Signature (base64)</label>
          <textarea id="signature-value" className="textarea min-h-28 font-mono text-xs" spellCheck={false} value={signature} onChange={(event) => setSignature(event.target.value)} />
          <button className="btn btn-primary" disabled={loading !== null} type="submit">Verify signature</button>
          {loading === "verify" && <Spinner label="Checking signature…" />}
          {verdict && (
            <ResultBanner
              verdict={verdict}
              technical={verdict}
              explanation={
                verdict === "VALID"
                  ? "PASS means this public key accepts the signature for the current message. That proves identity only if you already trust the public key."
                  : "FAIL means this public key rejects the signature. The message, key, or signature does not match."
              }
            />
          )}
          {verdict && <Limitations items={limitations} />}
        </form>
      </div>
      <article className="panel-flat panel-pad">
        <h2 className="text-sm font-semibold">How to read a signature result</h2>
        <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
          The private key is PKCS#8 PEM. The signature is RSA-PSS with MGF1-SHA256 and a salt length equal to the SHA-256 digest. A valid signature shows that this private key signed these exact bytes. You still need a separate reason to trust that the public key belongs to the signer. The signed-record download includes the public key and signature, not the private key.
        </p>
      </article>
    </section>
  );
}
