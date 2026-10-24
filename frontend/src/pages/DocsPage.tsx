import { Link } from "react-router-dom";
import { FileKey2, Fingerprint, KeyRound } from "lucide-react";
import { Badge, PageHeader } from "../components/ui";

const sections = [
  { id: "what", title: "What is CryptoGuard?" },
  { id: "why", title: "Why is this needed?" },
  { id: "workflow", title: "How it works" },
  { id: "methods", title: "Three security methods" },
  { id: "compare", title: "Compare the methods" },
  { id: "results", title: "What results mean" },
  { id: "limits", title: "Security limitations" },
  { id: "demo", title: "How to demonstrate" },
];

const comparison = [
  {
    question: "Main purpose",
    hash: "Check data integrity against a reference",
    hmac: "Authenticate a message using a shared secret",
    signature: "Verify a signature using a public key",
  },
  {
    question: "Key required?",
    hash: "No",
    hmac: "Shared secret",
    signature: "Private key to sign; public key to verify",
  },
  {
    question: "What does PASS mean?",
    hash: "Hash matches the reference",
    hmac: "Authentication tag matches",
    signature: "Supplied public key accepts the signature",
  },
  {
    question: "Main limitation",
    hash: "Does not prove origin or safety",
    hmac: "Does not establish a person's identity",
    signature: "Does not automatically establish trust in the public key",
  },
];

const demoSteps = [
  <>Open the <Link className="text-[var(--cg-cyan)]" to="/">Dashboard</Link> and explain the three security methods: SHA-256, HMAC-SHA256, and digital signatures.</>,
  <>Open <Link className="text-[var(--cg-cyan)]" to="/integrity">Hash Checker</Link> and upload a small test file.</>,
  <>Choose Calculate SHA-256. The page shows the real digest. With no reference hash, the result is NOT VERIFIED.</>,
  <>Copy that digest into the reference field and choose Compare Hashes. Expected result: PASS.</>,
  <>Change one character of the reference to a different hexadecimal character, such as changing <span className="font-mono">a</span> to <span className="font-mono">b</span>. Keep all 64 characters. Verify again. Expected result: FAIL.</>,
  <>Open <Link className="text-[var(--cg-cyan)]" to="/hmac">HMAC Verifier</Link>. Generate an authentication tag, then verify it with the same message and secret. Expected result: PASS.</>,
  <>Change the message and verify again with the same secret and tag. Expected result: FAIL. Clear the secret when you finish. CryptoGuard does not save it.</>,
  <>Open <Link className="text-[var(--cg-cyan)]" to="/signatures">Digital Signatures</Link>. Generate a key pair, sign a record, and verify it with the matching public key. Expected result: PASS.</>,
  <>Change the record text and verify again with the same public key and signature. Expected result: FAIL.</>,
  <>Open <Link className="text-[var(--cg-cyan)]" to="/reports">Reports</Link> and review the records those checks actually stored. The page stays empty until you run a real check.</>,
];

export function DocsPage() {
  return (
    <section>
      <PageHeader
        kicker="Product guide"
        title="Documentation"
        description="CryptoGuard — Verify Integrity. Authenticate Messages. Trust Digital Signatures."
      />
      <p className="lede mb-4 max-w-[68ch]">
        This guide explains the project in plain language. The browser collects your input. The backend performs the security check and returns the real result.
      </p>

      <nav className="guide-toc panel-flat mb-4" aria-label="Documentation sections">
        <p className="section-label w-full">On this page</p>
        {sections.map((section, index) => (
          <a key={section.id} href={`#${section.id}`}>
            {index + 1}. {section.title}
          </a>
        ))}
      </nav>

      <div className="space-y-4">
        <article id="what" className="guide-section panel-flat panel-pad">
          <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">What is CryptoGuard?</h2>
          <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
            CryptoGuard is a cybersecurity application. It checks three things: whether a file matches a trusted hash, whether a message can be authenticated with a shared secret, and whether a digital signature is valid.
          </p>
          <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
            You enter the file, message, or keys in the browser. The Python backend does the cryptographic work. The result is stored as a short history record. File contents, shared secrets, and private keys are not saved.
          </p>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <SummaryCard icon={Fingerprint} title="SHA-256" body="Checks whether file contents match a reference hash." />
            <SummaryCard icon={KeyRound} title="HMAC-SHA256" body="Checks whether a message matches an authentication tag created with a shared secret." />
            <SummaryCard icon={FileKey2} title="Digital signatures" body="Checks whether a signature is valid for a record and the supplied public key." />
          </div>
        </article>

        <article id="why" className="guide-section panel-flat panel-pad">
          <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">Why is this project needed?</h2>
          <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
            Imagine downloading a software file from the internet. Someone might change the file before it reaches you. The filename can stay the same even when the contents change.
          </p>
          <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
            CryptoGuard helps you check whether the file matches a trusted reference. A matching hash is useful, but it does not prove who created the file. It also does not prove that the software is safe to run.
          </p>
        </article>

        <article id="workflow" className="guide-section panel-flat panel-pad">
          <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">How does CryptoGuard work?</h2>
          <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
            Every check follows the same three steps. The cryptography runs on the backend. Uploaded files are hashed. They are not opened or executed.
          </p>
          <ol className="pipeline mt-4">
            <li>
              <span className="pipeline-index">Step 1</span>
              <h3 className="text-sm font-medium">Provide input</h3>
              <p className="mt-1 text-sm text-[var(--cg-muted)]">Choose a file, enter a message, or provide a record and the verification information that check needs.</p>
            </li>
            <li>
              <span className="pipeline-index">Step 2</span>
              <h3 className="text-sm font-medium">Perform the security check</h3>
              <p className="mt-1 text-sm text-[var(--cg-muted)]">The backend calculates a SHA-256 hash, checks an HMAC tag, or verifies a digital signature.</p>
            </li>
            <li>
              <span className="pipeline-index">Step 3</span>
              <h3 className="text-sm font-medium">Understand the result</h3>
              <p className="mt-1 text-sm text-[var(--cg-muted)]">Read PASS, FAIL, or NOT VERIFIED. Each label describes only the evidence you supplied.</p>
            </li>
          </ol>
        </article>

        <article id="methods" className="guide-section space-y-3">
          <div className="panel-flat panel-pad">
            <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">Understand the three security methods</h2>
            <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
              A hash, an authentication tag, and a digital signature answer different questions. CryptoGuard keeps those answers separate.
            </p>
          </div>

          <section className="method-card" aria-labelledby="method-sha">
            <p className="section-label">A</p>
            <h3 id="method-sha" className="text-base font-semibold">SHA-256 — file integrity</h3>
            <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
              SHA-256 creates a fixed-length digital fingerprint called a hash. CryptoGuard calculates the hash of the uploaded file and compares it with the reference hash you enter.
            </p>
            <ul className="prose-width mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-[var(--cg-muted)]">
              <li>If both valid hashes match, the result is PASS.</li>
              <li>If they differ, the result is FAIL.</li>
              <li>If no valid reference is available, the file has not been verified against a reference. The result is NOT VERIFIED.</li>
            </ul>
            <Flow label="SHA-256 flow" steps={["File", "Calculate SHA-256", "Compare with reference", "Result"]} />
            <p className="mt-3 text-sm leading-6 text-[var(--cg-muted)]">The reference hash must come from a source you trust, such as the publisher’s own download page.</p>
          </section>

          <section className="method-card" aria-labelledby="method-hmac">
            <p className="section-label">B</p>
            <h3 id="method-hmac" className="text-base font-semibold">HMAC-SHA256 — message authentication</h3>
            <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
              HMAC uses a message and a shared secret to create an authentication tag. The receiver uses the same secret to check that tag.
            </p>
            <ul className="prose-width mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-[var(--cg-muted)]">
              <li>If the tag matches the message and secret, verification succeeds.</li>
              <li>If the message, secret, or expected tag is wrong, verification fails.</li>
              <li>Anyone who knows the shared secret can create a valid tag. HMAC does not name a person.</li>
              <li>CryptoGuard does not save the secret in history or in the downloadable tag report.</li>
            </ul>
            <Flow label="HMAC flow" steps={["Message + shared secret", "HMAC tag", "Verification", "Result"]} />
          </section>

          <section className="method-card" aria-labelledby="method-sign">
            <p className="section-label">C</p>
            <h3 id="method-sign" className="text-base font-semibold">Digital signatures — record verification</h3>
            <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
              A digital signature uses two keys. The private key creates the signature. The public key checks it. CryptoGuard generates a 2048-bit RSA key pair and signs with RSA-PSS and SHA-256. Keys smaller than 2048 bits are rejected.
            </p>
            <ul className="prose-width mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-[var(--cg-muted)]">
              <li>Changing the signed record makes verification fail.</li>
              <li>A valid signature does not automatically prove the real-world identity of the signer. You must trust the public key for a separate reason.</li>
              <li>The private key stays in the browser until you clear it. It is not stored in application history.</li>
            </ul>
            <Flow label="Signing flow" steps={["Record + private key", "Digital signature"]} />
            <Flow label="Signature verification flow" steps={["Record + public key + signature", "Verification result"]} />
          </section>
        </article>

        <article id="compare" className="guide-section panel-flat">
          <div className="panel-pad pb-2">
            <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">Compare the three methods</h2>
            <p className="mt-2 text-sm leading-6 text-[var(--cg-muted)]">Use this table when you explain why a hash, an HMAC tag, and a signature are not the same check.</p>
          </div>
          <div className="table-wrap">
            <table className="data-table guide-table">
              <thead>
                <tr>
                  <th>Question</th>
                  <th>SHA-256</th>
                  <th>HMAC-SHA256</th>
                  <th>Digital signatures</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row) => (
                  <tr key={row.question}>
                    <td data-label="Question">{row.question}</td>
                    <td data-label="SHA-256">{row.hash}</td>
                    <td data-label="HMAC-SHA256">{row.hmac}</td>
                    <td data-label="Digital signatures">{row.signature}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article id="results" className="guide-section panel-flat panel-pad">
          <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">What do the results mean?</h2>
          <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
            The screen uses three labels. Inside the API, a hash match is stored as MATCH and a mismatch as MISMATCH. An HMAC or signature match is stored as VALID, and a failed check as INVALID. The page translates those words into PASS and FAIL.
          </p>
          <div className="status-legend mt-4" aria-label="Result meanings">
            <article className="result-pass">
              <Badge value="PASS" />
              <h3 className="mt-2 text-sm font-semibold">PASS</h3>
              <p className="mt-1 text-sm leading-6 text-[var(--cg-muted)]">The specific verification succeeded using the evidence you supplied.</p>
            </article>
            <article className="result-fail">
              <Badge value="FAIL" />
              <h3 className="mt-2 text-sm font-semibold">FAIL</h3>
              <p className="mt-1 text-sm leading-6 text-[var(--cg-muted)]">The check ran, but the comparison or authentication did not succeed.</p>
            </article>
            <article className="result-neutral">
              <Badge value="NOT VERIFIED" />
              <h3 className="mt-2 text-sm font-semibold">NOT VERIFIED</h3>
              <p className="mt-1 text-sm leading-6 text-[var(--cg-muted)]">There is not enough valid evidence to decide. A missing reference hash is the usual example.</p>
            </article>
          </div>
          <p className="prose-width mt-4 text-sm leading-6 text-[var(--cg-muted)]">
            An input error, a backend connection problem, or an external service outage is shown as an error. Those problems are not reported as a cryptographic FAIL.
          </p>
        </article>

        <article id="limits" className="guide-section panel-flat panel-pad">
          <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">Security limitations</h2>
          <ul className="prose-width mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-[var(--cg-muted)]">
            <li>A matching hash does not prove that software is safe.</li>
            <li>The reference hash must come from a trustworthy source.</li>
            <li>HMAC secrets must remain confidential.</li>
            <li>Private signing keys must be protected.</li>
            <li>A valid digital signature does not automatically establish the signer’s identity.</li>
            <li>OSV, the vulnerability source used by Dependency Scanner and Vulnerability Intelligence, can report only the advisories it returns.</li>
            <li>No advisory returned does not guarantee that a package has no vulnerabilities.</li>
            <li>NVD can be queried for a CVE only when the backend setting NVD_ENABLED is turned on. It is off in the default local setup.</li>
            <li>A CycloneDX SBOM from the SBOM Generator describes the components found in a manifest. It is not itself a vulnerability database.</li>
          </ul>
          <details className="disclosure">
            <summary>Short answers for common questions</summary>
            <div className="space-y-3 pb-2 text-sm leading-6 text-[var(--cg-muted)]">
              <p><strong className="text-[var(--cg-text)]">What is a hash?</strong> A hash is a short fingerprint of the exact bytes in a file. Change one byte and the fingerprint changes.</p>
              <p><strong className="text-[var(--cg-text)]">Why is a calculated hash sometimes NOT VERIFIED?</strong> CryptoGuard can calculate the fingerprint without a trusted reference. Until you supply that reference, it cannot say PASS or FAIL.</p>
              <p><strong className="text-[var(--cg-text)]">Does HMAC identify a person?</strong> No. It shows that someone who knows the shared secret produced the tag.</p>
              <p><strong className="text-[var(--cg-text)]">Does a valid signature prove identity?</strong> Only if you already trust that the public key belongs to that person or organization.</p>
            </div>
          </details>
        </article>

        <article id="demo" className="guide-section panel-flat panel-pad">
          <h2 className="font-[family-name:var(--cg-font-display)] text-lg font-semibold">How to demonstrate CryptoGuard</h2>
          <p className="prose-width mt-2 text-sm leading-6 text-[var(--cg-muted)]">
            Use real inputs. CryptoGuard does not insert sample PASS results. If the reference digest is no longer 64 hexadecimal characters, the form shows an input error instead of FAIL.
          </p>
          <ol className="demo-list">
            {demoSteps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </article>

        <article className="panel-flat panel-pad text-sm">
          <h2 className="text-sm font-semibold">Further reading</h2>
          <p className="mt-1 text-[var(--cg-muted)]">These links match the services the application actually uses.</p>
          <ul className="mt-2 space-y-1">
            <li><a className="text-[var(--cg-cyan)] underline" href="http://127.0.0.1:8000/docs">Backend API docs</a></li>
            <li><a className="text-[var(--cg-cyan)] underline" href="https://google.github.io/osv.dev/api/">OSV API</a></li>
            <li><a className="text-[var(--cg-cyan)] underline" href="https://nvd.nist.gov/developers/vulnerabilities">NVD CVE API</a></li>
            <li><a className="text-[var(--cg-cyan)] underline" href="https://cyclonedx.org/docs/1.7/json/">CycloneDX 1.7 JSON</a></li>
          </ul>
        </article>
      </div>
    </section>
  );
}

function SummaryCard({ icon: Icon, title, body }: { icon: typeof Fingerprint; title: string; body: string }) {
  return (
    <div className="feature-link">
      <span className="icon-tile"><Icon size={16} aria-hidden="true" /></span>
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="text-sm leading-6 text-[var(--cg-muted)]">{body}</p>
    </div>
  );
}

function Flow({ label, steps }: { label: string; steps: string[] }) {
  return (
    <ol className="method-flow" aria-label={label}>
      {steps.map((step) => (
        <li key={step}>{step}</li>
      ))}
    </ol>
  );
}
