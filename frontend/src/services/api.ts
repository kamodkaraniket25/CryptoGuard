import axios from "axios";
import type { DashboardStats, HealthResponse, HistoryPage, OperationResponse, SourceCatalog } from "../types";

const configuredBase = import.meta.env.VITE_API_BASE_URL?.trim();

function defaultApiBase(): string {
  if (import.meta.env.DEV) return "";
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host !== "localhost" && host !== "127.0.0.1") return "";
  }
  return "http://127.0.0.1:8000";
}

/** Explicit VITE_API_BASE_URL wins. Dev and the hosted site call /api on the same origin. */
export const API_BASE_URL = configuredBase ? configuredBase.replace(/\/$/, "") : defaultApiBase();

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

function apiTargetLabel(): string {
  if (API_BASE_URL) return API_BASE_URL;
  if (typeof window === "undefined") return "the frontend origin";
  return `${window.location.origin} (proxied to the API)`;
}

export function errorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    if (error instanceof Error && error.message) return error.message;
    return "Something went wrong.";
  }

  const status = error.response?.status;
  const detail = error.response?.data?.detail;
  const detailText = typeof detail === "string" ? detail : "";
  if (detailText) return detailText;

  if (!error.response) {
    const target = apiTargetLabel();
    if (error.code === "ECONNABORTED") {
      return `The request to ${target} timed out. Confirm Uvicorn is running on port 8000, then retry.`;
    }
    if (!import.meta.env.DEV && !API_BASE_URL) {
      return "The CryptoGuard API on this site did not respond. Wait a few seconds and retry. The hosted backend starts when the first request arrives.";
    }
    return `Cannot reach the CryptoGuard backend at ${target}. Start the API from the backend folder (Python/Uvicorn on port 8000), then retry. If the browser blocked the call, add this page's origin to CORS_ORIGINS and restart the API.`;
  }

  if (status === 502 || status === 504) {
    return "The frontend proxy could not connect to the CryptoGuard API on port 8000. Start Uvicorn, then retry.";
  }
  if (status && status >= 500) return `The CryptoGuard API returned HTTP ${status}.`;
  if (status && status >= 400) return `The CryptoGuard API rejected the request (HTTP ${status}).`;
  return "The backend returned an error.";
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/api/health");
  return response.data;
}

export async function getDashboard(): Promise<DashboardStats> {
  const response = await api.get<DashboardStats>("/api/dashboard/stats");
  return response.data;
}

export async function hashFile(file: File): Promise<OperationResponse<HashResult>> {
  const form = new FormData();
  form.append("file", file);
  const response = await api.post<OperationResponse<HashResult>>("/api/integrity/hash", form);
  return response.data;
}

export async function verifyFile(file: File, reference: string): Promise<OperationResponse<HashResult>> {
  const form = new FormData();
  form.append("file", file);
  form.append("reference_digest", reference);
  const response = await api.post<OperationResponse<HashResult>>("/api/integrity/verify", form);
  return response.data;
}

export interface HashResult {
  verdict: string;
  file_name: string;
  file_size: number;
  sha256: string;
  reference_supplied: boolean;
}

export async function generateHmac(message: string, secret: string): Promise<OperationResponse<HmacGenerateResult>> {
  const response = await api.post("/api/hmac/generate", { message, secret: secret || null });
  return response.data;
}

export async function verifyHmac(message: string, secret: string, tag: string): Promise<OperationResponse<{ verdict: string }>> {
  const response = await api.post("/api/hmac/verify", { message, secret, tag });
  return response.data;
}

export interface HmacGenerateResult {
  tag: string;
  secret: string;
  secret_generated: boolean;
  secret_visible: boolean;
  message_length: number;
}

export async function generateKeys(): Promise<OperationResponse<KeyResult>> {
  const response = await api.post("/api/signatures/keygen");
  return response.data;
}

export async function signMessage(message: string, privateKey: string): Promise<OperationResponse<SignResult>> {
  const response = await api.post("/api/signatures/sign", { message, private_key_pem: privateKey });
  return response.data;
}

export async function verifySignature(
  message: string,
  publicKey: string,
  signature: string,
): Promise<OperationResponse<{ verdict: string }>> {
  const response = await api.post("/api/signatures/verify", { message, public_key_pem: publicKey, signature });
  return response.data;
}

export interface KeyResult {
  private_key_pem: string;
  public_key_pem: string;
  private_key_visible: boolean;
  private_key_stored: boolean;
  key_size: number;
}

export interface SignResult {
  signature: string;
  public_key_pem: string;
  encoding: string;
  message_length: number;
  signed_bytes: string;
}

export async function signProvenance(record: string, privateKey: string): Promise<OperationResponse<ProvenanceSignResult>> {
  const response = await api.post("/api/provenance/sign", { record: JSON.parse(record), private_key_pem: privateKey });
  return response.data;
}

export async function verifyProvenance(record: string, publicKey: string, artifact: File | null): Promise<OperationResponse<ProvenanceResult>> {
  const form = new FormData();
  form.append("record_json", record);
  form.append("public_key_pem", publicKey);
  if (artifact) form.append("artifact", artifact);
  const response = await api.post("/api/provenance/verify", form);
  return response.data;
}

export interface ProvenanceSignResult {
  signature: string;
  public_key_pem: string;
  canonical_json: string;
  canonicalization: string;
  private_key_stored: boolean;
}

export interface ProvenanceResult {
  record_status: string;
  digest_status: string;
  signature_status: string;
  missing_evidence: string[];
  notes: string[];
  file_name: string | null;
  file_size: number | null;
  computed_sha256: string | null;
  recorded_sha256: string | null;
  canonicalization: string;
}

export async function scanDependencies(file: File, manifestFormat: string, refresh: boolean): Promise<OperationResponse<ScanResult>> {
  const form = new FormData();
  form.append("file", file);
  form.append("manifest_format", manifestFormat);
  form.append("refresh", String(refresh));
  form.append("include_nvd", "false");
  const response = await api.post("/api/dependencies/scan", form);
  return response.data;
}

export interface Advisory {
  id: string;
  summary: string;
  modified?: string;
  published?: string;
  aliases: string[];
  reference_url: string | null;
  osv_url: string | null;
  source: string;
  canonical_id: string;
  affected?: { package?: string; ecosystem?: string; versions?: string[] }[];
  severity?: { type: string | null; score: string }[];
  severity_label?: string | null;
}

export interface ScanComponent {
  name: string;
  declared_version: string | null;
  ecosystem: string;
  version_status: string;
  query_status: string;
  message: string | null;
  cached?: boolean;
  retrieved_at?: string | null;
  advisories: Advisory[];
  warning: string | null;
}

export interface ScanResult {
  manifest_format: string;
  subject_name: string;
  components: ScanComponent[];
  warnings: string[];
  advisory_ids: string[];
  queried_count: number;
  skipped_count: number;
  source_errors: number;
  no_match_meaning: string;
}

export async function queryVulnerability(payload: {
  name: string;
  ecosystem: string;
  version: string;
  refresh: boolean;
  include_nvd: boolean;
}): Promise<OperationResponse<VulnQueryResult>> {
  const response = await api.post("/api/vulnerabilities/query", payload);
  return response.data;
}

export interface VulnQueryResult {
  package: { name: string; ecosystem: string; version: string };
  osv: {
    query_status: string;
    cached: boolean;
    retrieved_at: string | null;
    advisories: Advisory[];
    message: string | null;
    source: string;
    truncated: boolean;
  };
  nvd: { status: string; records: NvdRecord[]; errors: { id: string; message: string }[]; message: string | null };
  advisory_ids: string[];
  no_match_meaning: string;
}

export interface NvdRecord {
  id: string;
  summary: string | null;
  published?: string;
  modified?: string;
  reference_url: string | null;
  nvd_url: string;
  cvss_score: number | null;
  cvss_severity: string | null;
  source: string;
}

export async function queryNvd(cveId: string, refresh: boolean): Promise<OperationResponse<{ cve_id: string; nvd: { query_status: string; message: string | null; record: NvdRecord | null; cached: boolean; retrieved_at: string | null } }>> {
  const response = await api.post("/api/vulnerabilities/nvd", { cve_id: cveId, refresh });
  return response.data;
}

export async function generateSbom(file: File, manifestFormat: string): Promise<OperationResponse<SbomResult>> {
  const form = new FormData();
  form.append("file", file);
  form.append("manifest_format", manifestFormat);
  const response = await api.post("/api/sbom/generate", form);
  return response.data;
}

export interface SbomResult {
  spec_version: string;
  schema_url: string;
  valid: boolean;
  validation_errors: string[];
  component_count: number;
  warnings: string[];
  bom: Record<string, unknown>;
  note: string;
}

export async function getSources(): Promise<SourceCatalog> {
  const response = await api.get<SourceCatalog>("/api/sources");
  return response.data;
}

export async function checkSources(): Promise<{ note: string; results: { id: string; status: string; checked_at: string | null; detail: string | null }[] }> {
  const response = await api.post("/api/sources/check", { sources: ["osv", "nvd", "cyclonedx"] });
  return response.data;
}

export async function getHistory(params: Record<string, string | number>): Promise<HistoryPage> {
  const response = await api.get<HistoryPage>("/api/history", { params });
  return response.data;
}

export async function getHistoryDetail(operationId: string): Promise<Record<string, unknown>> {
  const response = await api.get(`/api/history/${operationId}`);
  return response.data;
}

export async function deleteHistory(operationId: string): Promise<void> {
  await api.delete(`/api/history/${operationId}`);
}

export async function exportHistory(params: Record<string, string>): Promise<Blob> {
  const response = await api.get("/api/history/export", { params, responseType: "blob" });
  return response.data as Blob;
}
