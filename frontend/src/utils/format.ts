export function validateOptionalSha256(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const normalized = trimmed.toLowerCase().replace(/^sha256:/, "");
  if (!/^[0-9a-f]{64}$/.test(normalized)) {
    return "SHA-256 digests must be 64 hexadecimal characters.";
  }
  return null;
}

export function normalizeSha256(value: string): string {
  return value.trim().toLowerCase().replace(/^sha256:/, "");
}

export function validateHmacTag(value: string): string | null {
  const normalized = value.trim().toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(normalized)) {
    return "HMAC-SHA256 tags must be 64 hexadecimal characters.";
  }
  return null;
}

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

export function uploadTooLargeMessage(file: File, maxBytes = MAX_UPLOAD_BYTES): string | null {
  if (file.size <= maxBytes) return null;
  return `${file.name} is ${formatBytes(file.size)}. CryptoGuard accepts files up to ${formatBytes(maxBytes)}.`;
}

export function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function severityText(advisory: {
  severity_label?: string | null;
  severity?: { type: string | null; score: string }[];
}): string {
  const parts: string[] = [];
  if (advisory.severity_label) parts.push(advisory.severity_label);
  for (const item of advisory.severity ?? []) {
    parts.push(item.type ? `${item.type} ${item.score}` : item.score);
  }
  if (parts.length === 0) return "No severity was included in this OSV record.";
  return `Severity reported by OSV: ${parts.join(" · ")}`;
}

export function formatWhen(value: string | null | undefined): string {
  if (!value) return "Not checked";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

const verificationOperations = new Set(["hash_verify", "hmac_verify", "signature_verify"]);

export function resultLabel(value: string): string {
  const text = value.toUpperCase();
  if (text.includes("NOT VERIFIED") || text.includes("NOT_VERIFIED") || text.includes("INCOMPLETE")) return "NOT VERIFIED";
  if (/(MISMATCH|INVALID|\bFAIL\b)/.test(text)) return "FAIL";
  if (/(MATCH|VALID|\bPASS\b)/.test(text)) return "PASS";
  return value;
}

export function recordResult(operationType: string, status: string, verdict?: string | null): string {
  if (verdict) return resultLabel(verdict);
  if (status === "not_verified") return "NOT VERIFIED";
  if (status === "failed") return "FAIL";
  if (status === "warning") return "WARNING";
  if (status === "success" && verificationOperations.has(operationType)) return "PASS";
  if (status === "success") return "RECORDED";
  return status;
}

export const operationLabels: Record<string, string> = {
  hash: "Hash",
  hash_verify: "Hash verification",
  hmac_generate: "HMAC generation",
  hmac_verify: "HMAC verification",
  signature_keygen: "Key generation",
  signature_sign: "Signature",
  signature_verify: "Signature verification",
  provenance_verify: "Provenance verification",
  provenance_sign: "Provenance signature",
  dependency_scan: "Dependency scan",
  vulnerability_query: "Vulnerability query",
  sbom_generate: "SBOM generation",
};
