# Data sources

CryptoGuard does not ship a vulnerability dataset. It asks live APIs when a person runs a query or a source check. CycloneDX is a specification. Its JSON Schema is vendored so SBOM validation works without a network connection.

## OSV Vulnerability Database

- Website: https://osv.dev/
- API documentation: https://google.github.io/osv.dev/api/
- Query reference: https://google.github.io/osv.dev/post-v1-query/
- Endpoint used: `POST https://api.osv.dev/v1/query`
- Access: live HTTP request
- Ecosystems used: `npm` and `PyPI`. Those names are case-sensitive in the OSV API.
- Request shape: `{"package": {"name": "...", "ecosystem": "npm"}, "version": "1.2.3"}`
- Fields read when present: `id`, `summary`, `details`, `modified`, `published`, `aliases`, `references`, `affected`, `next_page_token`
- Freshness: each successful response is cached until `VULN_CACHE_TTL_SECONDS` (default 21600 seconds, six hours). The UI shows `retrieved_at`.
- Attribution: CryptoGuard does not copy the OSV database into the repository. Advisories come from the upstream databases that OSV aggregates. See https://osv.dev/ for the attribution of an individual record.
- License: this project does not invent a license for OSV data. Check the OSV site for the current terms.
- Limitation: an empty `vulns` list is reported as "No matching advisory returned by this source for the queried package and version." That is not a claim that the package has no vulnerabilities.

CryptoGuard uses `/v1/query` rather than `/v1/querybatch`. The official batch endpoint returns only vulnerability ids and modified times. The product needs summaries, references, and affected-package information when OSV includes them.

If `next_page_token` is present, CryptoGuard follows it for at most `OSV_MAX_PAGES` pages (default 3) and then marks the result truncated.

PyPI names are normalized with the PEP 503 rule (lowercase, and runs of `-`, `_`, and `.` become a single `-`) before the query. npm names are sent unchanged because npm names are case-sensitive.

## National Vulnerability Database

- Website: https://nvd.nist.gov/
- API documentation: https://nvd.nist.gov/developers/vulnerabilities
- Endpoint used: `GET https://services.nvd.nist.gov/rest/json/cves/2.0`
- Lookup parameter: `cveId`
- Status-check parameter: `resultsPerPage=1`
- Optional header: `apiKey`, taken from `NVD_API_KEY` and never sent to the browser
- Access: live HTTP request, and only for lookups when `NVD_ENABLED=true`
- Fields read when present: CVE `id`, English `descriptions`, `published`, `lastModified`, `references`, and CVSS v3.1 or v3.0 `baseScore` and `baseSeverity`
- The OSV workflow does not need an NVD key or the NVD flag.
- CryptoGuard does not download NVD data feeds at startup.
- Calls are spaced by `NVD_MIN_INTERVAL_SECONDS` (default 6). Confirm the current published rate limits on the NVD developer site. This document does not restate a rate-limit number that was not copied from that page.
- Attribution and license: confirm the current terms at https://nvd.nist.gov/. CryptoGuard does not bundle NVD records.
- A missing CVE record is reported as no matching NVD record for that identifier. It is not a statement that the identifier is harmless.
- The same CVE is counted once in dashboard totals. If an OSV advisory has a CVE alias, the canonical finding id is that CVE. A later NVD lookup of the same CVE does not add a second finding.

## CycloneDX

- Website: https://cyclonedx.org/
- JSON reference: https://cyclonedx.org/docs/1.7/json/
- Schema URL: https://cyclonedx.org/schema/bom-1.7.schema.json
- Local copy: `backend/app/data/bom-1.7.schema.json`
- Category: specification and schema, not a vulnerability database
- Version emitted: `specVersion` `1.7`
- Fields written: `bomFormat`, `specVersion`, `serialNumber`, `version`, `metadata.timestamp`, `metadata.lifecycles`, `metadata.tools`, `metadata.component`, `components.type`, `components.name`, `components.version` when exact, `components.purl`, `components.scope`, `components.bom-ref`
- Fields deliberately omitted when unknown: licenses, suppliers, hashes, and dependency edges
- The schema file's own comment says: "CycloneDX JSON schema is published under the terms of the Apache License 2.0."
- A source check requests the published schema URL and reads a small prefix to see that it looks like JSON. That check is reachability, not a security result.

## GitHub Advisory Database

CryptoGuard does not call the GitHub Advisory API. When OSV returns a `GHSA-` identifier, that identifier is shown as part of the OSV record. There is no separate GitHub client and no GitHub token.

## What is not stored from external responses

Cache rows store the parsed advisory fields listed above. They do not store API keys, uploaded files, messages, or secrets. Source checks store a status, time, latency, error category, and a short detail. NVD status checks do not save the CVE records that happen to be in a one-row pagination response.
