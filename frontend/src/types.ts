export interface OperationResponse<T> {
  product: string;
  full_title: string;
  operation_id: string;
  operation_type: string;
  status: string;
  algorithm: string | null;
  created_at: string;
  duration_ms: number;
  result: T;
  limitations: string[];
}

export interface DashboardStats {
  product: string;
  total_operations: number;
  integrity_success: number;
  integrity_failed: number;
  integrity_not_verified: number;
  hmac_generated: number;
  hmac_verified_success: number;
  hmac_verified_failed: number;
  signatures_generated: number;
  signatures_verified_success: number;
  signatures_verified_failed: number;
  provenance_checks: number;
  dependency_scans: number;
  vulnerability_queries: number;
  vulnerability_findings: number;
  sbom_generated: number;
  recent_operations: HistoryItem[];
  activity: { date: string; count: number }[];
  sources: { id: string; name: string; status: string; checked_at: string | null }[];
  notes: string[];
}

export interface HistoryItem {
  operation_id: string;
  operation_type: string;
  status: string;
  algorithm: string | null;
  file_name: string | null;
  file_size?: number | null;
  sha256_digest?: string | null;
  created_at: string;
  duration_ms?: number;
  verdict?: string | null;
}

export interface HistoryPage {
  total: number;
  limit: number;
  offset: number;
  items: HistoryItem[];
}

export interface SourceRecord {
  id: string;
  name: string;
  website: string;
  documentation_url: string;
  endpoint: string;
  category: string;
  purpose: string;
  access_method: string;
  fields_used: string[];
  limitations: string[];
  attribution: string;
  license_note: string;
  data_is_downloaded: boolean;
  status: string;
  checked_at: string | null;
  latency_ms: number | null;
  error_category: string | null;
  detail: string | null;
}

export interface SourceCatalog {
  product: string;
  nvd_enabled: boolean;
  nvd_key_configured: boolean;
  cache_ttl_seconds: number;
  note: string;
  sources: SourceRecord[];
}

export interface HealthResponse {
  status: string;
  product: string;
  version: string;
  database: string;
  nvd_enabled: boolean;
}
