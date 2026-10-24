"""CryptoGuard HTTP routes."""

import json
import time

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import LIMITATIONS, Op, Status
from app.database import get_db
from app.schemas import (
    HmacGenerateRequest,
    HmacVerifyRequest,
    NvdLookupRequest,
    ProvenanceSignRequest,
    SignRequest,
    SourceCheckRequest,
    VerifySignatureRequest,
    VulnerabilityBatchRequest,
    VulnerabilityQueryRequest,
)
from app.services import signatures
from app.services.cache import clear_cache
from app.services.dashboard import dashboard_stats
from app.services.history import delete_history, detail, export_csv, get_history, list_history
from app.services.hmac_service import compute_tag, generate_secret, verify_tag
from app.services.integrity import hash_result, start_timer
from app.services.manifest import parse_manifest
from app.services.osv import lookup_package
from app.services.provenance import CANONICAL_FIELDS, canonical_bytes, describe_canonicalization
from app.services.records import envelope
from app.services.sbom import generate_sbom, validate_sbom
from app.services.sources import check_sources, list_sources
from app.services.supply import analyze_manifest, query_cve, query_one
from app.utils.files import read_upload_hashed, read_upload_text
from app.utils.security import digests_match, normalize_sha256, public_key_fingerprint, sha256_text
from app.api import client_error

router = APIRouter()


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@router.get("/health", tags=["platform"])
def health(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        client_error(503, "Database is unavailable.")
    return {
        "status": "ok",
        "product": "CryptoGuard",
        "version": settings.app_version,
        "database": "ok",
        "nvd_enabled": settings.nvd_enabled,
    }


@router.get("/dashboard/stats", tags=["platform"])
def stats(db: Session = Depends(get_db)) -> dict:
    return dashboard_stats(db)


@router.post("/integrity/hash", tags=["integrity"])
async def hash_file(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    started = start_timer()
    file_name, file_size, digest = await read_upload_hashed(file)
    return hash_result(db, started=started, file_name=file_name, file_size=file_size, digest=digest, reference=None)


@router.post("/integrity/verify", tags=["integrity"])
async def verify_file(
    file: UploadFile = File(...),
    reference_digest: str = Form(...),
    db: Session = Depends(get_db),
) -> dict:
    try:
        normalize_sha256(reference_digest)
    except ValueError as exc:
        client_error(400, str(exc))
    started = start_timer()
    file_name, file_size, digest = await read_upload_hashed(file)
    return hash_result(
        db,
        started=started,
        file_name=file_name,
        file_size=file_size,
        digest=digest,
        reference=reference_digest,
    )


@router.post("/hmac/generate", tags=["hmac"])
def hmac_generate(body: HmacGenerateRequest, db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    if body.secret is not None and not body.secret.strip():
        client_error(400, "Secret cannot be blank. Omit it to generate one.")
    secret = body.secret if body.secret else generate_secret()
    tag = compute_tag(body.message, secret)
    return envelope(
        db,
        operation_type=Op.HMAC_GENERATE,
        status=Status.SUCCESS,
        algorithm="HMAC-SHA256",
        started=started,
        result={
            "tag": tag,
            "secret": secret,
            "secret_generated": body.secret is None,
            "secret_visible": True,
            "message_length": len(body.message.encode("utf-8")),
        },
        limitations=LIMITATIONS[Op.HMAC_GENERATE],
        metadata={"message_length": len(body.message.encode("utf-8")), "secret_generated": body.secret is None},
    )


@router.post("/hmac/verify", tags=["hmac"])
def hmac_verify(body: HmacVerifyRequest, db: Session = Depends(get_db)) -> dict:
    tag = body.tag.strip().lower()
    if len(tag) != 64 or any(ch not in "0123456789abcdef" for ch in tag):
        client_error(400, "HMAC-SHA256 tag must be 64 hexadecimal characters.")
    started = time.perf_counter()
    valid = verify_tag(body.message, body.secret, tag)
    verdict = "VALID" if valid else "INVALID"
    return envelope(
        db,
        operation_type=Op.HMAC_VERIFY,
        status=Status.SUCCESS if valid else Status.FAILED,
        algorithm="HMAC-SHA256",
        started=started,
        result={"verdict": verdict, "message_length": len(body.message.encode("utf-8"))},
        limitations=LIMITATIONS[Op.HMAC_VERIFY],
        metadata={"verdict": verdict, "message_length": len(body.message.encode("utf-8"))},
    )


@router.post("/signatures/keygen", tags=["signatures"])
def keygen(db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    private_pem, public_pem = signatures.generate_keypair()
    return envelope(
        db,
        operation_type=Op.SIGNATURE_KEYGEN,
        status=Status.SUCCESS,
        algorithm=signatures.ALGORITHM,
        started=started,
        result={
            "private_key_pem": private_pem,
            "public_key_pem": public_pem,
            "private_key_visible": True,
            "private_key_stored": False,
            "key_size": 2048,
        },
        limitations=LIMITATIONS[Op.SIGNATURE_KEYGEN],
        metadata={"key_size": 2048, "private_key_stored": False},
    )


@router.post("/signatures/sign", tags=["signatures"])
def sign_message(body: SignRequest, db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    try:
        signature = signatures.sign_bytes(body.private_key_pem, body.message.encode("utf-8"))
        public_pem = signatures.public_pem_from_private(body.private_key_pem)
    except ValueError as exc:
        client_error(400, str(exc))
    return envelope(
        db,
        operation_type=Op.SIGNATURE_SIGN,
        status=Status.SUCCESS,
        algorithm=signatures.ALGORITHM,
        started=started,
        result={
            "signature": signature,
            "public_key_pem": public_pem,
            "encoding": "base64",
            "message_length": len(body.message.encode("utf-8")),
            "signed_bytes": "Exact UTF-8 bytes of the message, with no added newline.",
        },
        limitations=LIMITATIONS[Op.SIGNATURE_SIGN],
        metadata={
            "message_length": len(body.message.encode("utf-8")),
            "public_key_sha256": public_key_fingerprint(public_pem),
        },
    )


@router.post("/signatures/verify", tags=["signatures"])
def verify_message(body: VerifySignatureRequest, db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    try:
        valid = signatures.verify_bytes(
            body.public_key_pem,
            body.message.encode("utf-8"),
            body.signature,
        )
    except ValueError as exc:
        client_error(400, str(exc))
    verdict = "VALID" if valid else "INVALID"
    return envelope(
        db,
        operation_type=Op.SIGNATURE_VERIFY,
        status=Status.SUCCESS if valid else Status.FAILED,
        algorithm=signatures.ALGORITHM,
        started=started,
        result={"verdict": verdict, "message_length": len(body.message.encode("utf-8"))},
        limitations=LIMITATIONS[Op.SIGNATURE_VERIFY],
        metadata={
            "verdict": verdict,
            "message_length": len(body.message.encode("utf-8")),
            "public_key_sha256": public_key_fingerprint(body.public_key_pem),
        },
    )


@router.post("/provenance/sign", tags=["provenance"])
def sign_provenance(body: ProvenanceSignRequest, db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    try:
        payload = canonical_bytes(body.record)
        signature = signatures.sign_bytes(body.private_key_pem, payload)
        public_pem = signatures.public_pem_from_private(body.private_key_pem)
    except ValueError as exc:
        client_error(400, str(exc))
    return envelope(
        db,
        operation_type=Op.PROVENANCE_SIGN,
        status=Status.SUCCESS,
        algorithm=signatures.ALGORITHM,
        started=started,
        result={
            "signature": signature,
            "public_key_pem": public_pem,
            "canonical_json": payload.decode("utf-8"),
            "canonicalization": describe_canonicalization(),
            "private_key_stored": False,
        },
        limitations=LIMITATIONS[Op.PROVENANCE_SIGN],
        metadata={
            "canonical_sha256": sha256_text(payload.decode("utf-8")),
            "public_key_sha256": public_key_fingerprint(public_pem),
            "private_key_stored": False,
        },
    )


@router.post("/provenance/verify", tags=["provenance"])
async def verify_provenance(
    record_json: str = Form(...),
    public_key_pem: str = Form(""),
    artifact: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> dict:
    started = time.perf_counter()
    try:
        record = json.loads(record_json)
    except json.JSONDecodeError:
        client_error(400, "Provenance record is not valid JSON.")
    if not isinstance(record, dict):
        client_error(400, "Provenance record must be a JSON object.")

    missing = [
        field
        for field in CANONICAL_FIELDS
        if not isinstance(record.get(field), str) or not record.get(field, "").strip()
    ]
    notes: list[str] = []
    missing_evidence: list[str] = []
    canonical = None
    recorded_digest = None
    if missing:
        record_status = "INCOMPLETE_RECORD"
        missing_evidence.extend(missing)
        notes.append("Required provenance fields are missing or blank.")
    else:
        try:
            recorded_digest = normalize_sha256(record["artifact_sha256"])
            canonical = canonical_bytes(record)
            record_status = "STRUCTURALLY_VALID"
        except ValueError as exc:
            record_status = "INCOMPLETE_RECORD"
            notes.append(str(exc))

    file_name = None
    file_size = None
    computed = None
    if artifact is not None and artifact.filename:
        file_name, file_size, computed = await read_upload_hashed(artifact)
        if recorded_digest and computed:
            digest_status = "DIGEST_MATCH" if digests_match(computed, recorded_digest) else "DIGEST_MISMATCH"
        else:
            digest_status = "NOT_VERIFIED"
            notes.append("The artifact was uploaded, but the recorded digest could not be compared.")
    else:
        digest_status = "NOT_VERIFIED"
        missing_evidence.append("artifact_file")
        notes.append("No artifact was uploaded, so the recorded digest was not compared with file bytes.")

    signature = record.get("signature")
    if not isinstance(signature, str) or not signature.strip():
        signature_status = "NOT_VERIFIED"
        missing_evidence.append("signature")
        notes.append("Unsigned JSON is not authenticated evidence.")
    elif not public_key_pem.strip():
        signature_status = "NOT_VERIFIED"
        missing_evidence.append("public_key")
        notes.append("A signature is present, but no public key was provided.")
    elif canonical is None:
        signature_status = "NOT_VERIFIED"
        notes.append("The signature was not checked because the canonical record is incomplete.")
    else:
        try:
            valid = signatures.verify_bytes(public_key_pem, canonical, signature)
            signature_status = "SIGNATURE_VALID" if valid else "SIGNATURE_INVALID"
        except ValueError as exc:
            signature_status = "NOT_VERIFIED"
            notes.append(str(exc))

    if digest_status == "DIGEST_MISMATCH" or signature_status == "SIGNATURE_INVALID":
        status = Status.FAILED
    elif digest_status == "DIGEST_MATCH" and signature_status == "SIGNATURE_VALID":
        status = Status.SUCCESS
    elif missing_evidence or record_status == "INCOMPLETE_RECORD":
        status = Status.WARNING
    else:
        status = Status.NOT_VERIFIED

    safe_fields = {
        field: record.get(field).strip()
        for field in CANONICAL_FIELDS
        if isinstance(record.get(field), str) and record.get(field).strip()
    }
    return envelope(
        db,
        operation_type=Op.PROVENANCE_VERIFY,
        status=status,
        algorithm="SHA-256+" + signatures.ALGORITHM,
        started=started,
        result={
            "record_status": record_status,
            "digest_status": digest_status,
            "signature_status": signature_status,
            "missing_evidence": missing_evidence,
            "notes": notes,
            "file_name": file_name,
            "file_size": file_size,
            "computed_sha256": computed,
            "recorded_sha256": recorded_digest,
            "canonicalization": describe_canonicalization(),
            "fields": safe_fields,
        },
        limitations=LIMITATIONS[Op.PROVENANCE_VERIFY],
        metadata={
            "record_status": record_status,
            "digest_status": digest_status,
            "signature_status": signature_status,
            "missing_evidence": missing_evidence,
            "notes": notes,
            **safe_fields,
        },
        file_name=file_name,
        file_size=file_size,
        sha256_digest=computed or recorded_digest,
    )


@router.post("/dependencies/scan", tags=["supply-chain"])
async def scan_dependencies(
    file: UploadFile = File(...),
    manifest_format: str = Form("auto"),
    refresh: str = Form("false"),
    include_nvd: str = Form("false"),
    db: Session = Depends(get_db),
) -> dict:
    started = time.perf_counter()
    filename, text = await read_upload_text(file)
    try:
        parsed = parse_manifest(filename, text, manifest_format)
        result = await analyze_manifest(db, parsed, refresh=_bool(refresh), include_nvd=_bool(include_nvd))
    except ValueError as exc:
        client_error(400, str(exc))
    if result["source_errors"] or result["warnings"]:
        status = Status.WARNING
    else:
        status = Status.SUCCESS
    return envelope(
        db,
        operation_type=Op.DEPENDENCY_SCAN,
        status=status,
        algorithm="OSV",
        started=started,
        result=result,
        limitations=LIMITATIONS[Op.DEPENDENCY_SCAN],
        metadata={
            "manifest_format": result["manifest_format"],
            "subject_name": result["subject_name"],
            "queried_count": result["queried_count"],
            "skipped_count": result["skipped_count"],
            "source_errors": result["source_errors"],
            "advisory_ids": result["advisory_ids"],
            "findings": result["findings"][:50],
            "warnings": result["warnings"][:30],
            "file_name": filename,
        },
        file_name=filename,
    )


@router.post("/vulnerabilities/query", tags=["supply-chain"])
async def vulnerability_query(body: VulnerabilityQueryRequest, db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    try:
        result = await query_one(
            db,
            name=body.name,
            ecosystem=body.ecosystem,
            version=body.version,
            refresh=body.refresh,
            include_nvd=body.include_nvd,
        )
    except ValueError as exc:
        client_error(400, str(exc))
    osv_status = result["osv"]["query_status"]
    status = Status.WARNING if osv_status == "error" else Status.SUCCESS
    return envelope(
        db,
        operation_type=Op.VULNERABILITY_QUERY,
        status=status,
        algorithm="OSV",
        started=started,
        result=result,
        limitations=LIMITATIONS[Op.VULNERABILITY_QUERY],
        metadata={
            "package": result["package"],
            "advisory_ids": result["advisory_ids"],
            "source": "osv",
            "retrieved_at": result["osv"].get("retrieved_at"),
            "cached": result["osv"].get("cached"),
            "query_status": osv_status,
            "message": result["osv"].get("message"),
            "findings": [
                {
                    "id": item.get("canonical_id") or item.get("id"),
                    "summary": (item.get("summary") or "")[:300],
                    "source": "osv",
                    "reference_url": item.get("reference_url") or item.get("osv_url"),
                }
                for item in (result["osv"].get("advisories") or [])[:50]
            ],
        },
    )


@router.post("/vulnerabilities/batch", tags=["supply-chain"])
async def vulnerability_batch(body: VulnerabilityBatchRequest, db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    settings = get_settings()
    if len(body.packages) > settings.max_packages_per_scan:
        client_error(400, f"A batch can contain at most {settings.max_packages_per_scan} packages.")
    results = []
    advisory_ids: list[str] = []
    errors = 0
    memo: dict = {}
    for package in body.packages:
        if any(token in package.version for token in "^~><=*"):
            results.append(
                {
                    "name": package.name,
                    "ecosystem": package.ecosystem,
                    "version": package.version,
                    "query_status": "skipped",
                    "message": "Version ranges are not sent to OSV. Provide an exact version.",
                    "advisories": [],
                }
            )
            continue
        live = await lookup_package(
            db,
            name=package.name.strip(),
            ecosystem=package.ecosystem,
            version=package.version.strip(),
            refresh=body.refresh,
            memo=memo,
        )
        if live["query_status"] == "error":
            errors += 1
        for advisory in live.get("advisories") or []:
            canonical = advisory.get("canonical_id") or advisory.get("id")
            if canonical and canonical not in advisory_ids:
                advisory_ids.append(canonical)
        results.append({"name": package.name, "ecosystem": package.ecosystem, "version": package.version, **live})
    result = {"results": results, "advisory_ids": advisory_ids, "source_errors": errors}
    return envelope(
        db,
        operation_type=Op.VULNERABILITY_QUERY,
        status=Status.WARNING if errors else Status.SUCCESS,
        algorithm="OSV",
        started=started,
        result=result,
        limitations=LIMITATIONS[Op.VULNERABILITY_QUERY],
        metadata={"advisory_ids": advisory_ids, "source_errors": errors, "package_count": len(body.packages), "source": "osv"},
    )


@router.post("/vulnerabilities/nvd", tags=["supply-chain"])
async def nvd_lookup(body: NvdLookupRequest, db: Session = Depends(get_db)) -> dict:
    started = time.perf_counter()
    try:
        result = await query_cve(db, body.cve_id, body.refresh)
    except ValueError as exc:
        client_error(400, str(exc))
    nvd_status = result["nvd"]["query_status"]
    if nvd_status == "disabled":
        client_error(409, result["nvd"]["message"])
    status = Status.WARNING if nvd_status == "error" else Status.SUCCESS
    return envelope(
        db,
        operation_type=Op.VULNERABILITY_QUERY,
        status=status,
        algorithm="NVD",
        started=started,
        result=result,
        limitations=LIMITATIONS[Op.VULNERABILITY_QUERY],
        metadata={
            "source": "nvd",
            "advisory_ids": result["advisory_ids"],
            "retrieved_at": result["nvd"].get("retrieved_at"),
            "cached": result["nvd"].get("cached"),
            "query_status": nvd_status,
            "message": result["nvd"].get("message"),
            "cve_id": result["cve_id"],
        },
    )


@router.delete("/vulnerabilities/cache", tags=["supply-chain"])
def delete_vulnerability_cache(db: Session = Depends(get_db)) -> dict:
    deleted = clear_cache(db)
    return {"deleted": deleted, "message": "Cached vulnerability lookups were removed from the local database."}


@router.get("/sources", tags=["sources"])
def sources(db: Session = Depends(get_db)) -> dict:
    return list_sources(db)


@router.get("/sources/status", tags=["sources"])
def source_status(db: Session = Depends(get_db)) -> dict:
    payload = list_sources(db)
    return {
        "note": payload["note"],
        "sources": [
            {
                "id": item["id"],
                "name": item["name"],
                "status": item["status"],
                "checked_at": item["checked_at"],
                "detail": item["detail"],
            }
            for item in payload["sources"]
        ],
    }


@router.post("/sources/check", tags=["sources"])
async def source_check(body: SourceCheckRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return await check_sources(db, body.sources)
    except ValueError as exc:
        client_error(400, str(exc))


@router.post("/sbom/generate", tags=["supply-chain"])
async def sbom_generate(
    file: UploadFile = File(...),
    manifest_format: str = Form("auto"),
    db: Session = Depends(get_db),
) -> dict:
    started = time.perf_counter()
    filename, text = await read_upload_text(file)
    try:
        parsed = parse_manifest(filename, text, manifest_format)
    except ValueError as exc:
        client_error(400, str(exc))
    document = generate_sbom(parsed)
    errors = validate_sbom(document)
    result = {
        "spec_version": get_settings().cyclonedx_spec_version,
        "schema_url": get_settings().cyclonedx_schema_url,
        "valid": not errors,
        "validation_errors": errors,
        "component_count": len(document.get("components") or []),
        "warnings": parsed.warnings,
        "bom": document,
        "note": "Components without an exact version omit version and use an unversioned purl. Ranges are not copied into the version field.",
    }
    return envelope(
        db,
        operation_type=Op.SBOM_GENERATE,
        status=Status.SUCCESS if result["valid"] and not parsed.warnings else Status.WARNING,
        algorithm="CycloneDX-1.7",
        started=started,
        result=result,
        limitations=LIMITATIONS[Op.SBOM_GENERATE],
        metadata={
            "spec_version": result["spec_version"],
            "valid": result["valid"],
            "component_count": result["component_count"],
            "subject_name": parsed.subject_name,
            "validation_errors": errors[:10],
            "file_name": filename,
        },
        file_name=filename,
    )


@router.get("/history", tags=["history"])
def history(
    operation_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return list_history(
            db,
            operation_type=operation_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        client_error(400, str(exc))


@router.get("/history/export", tags=["history"])
def history_export(
    operation_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> Response:
    try:
        csv_text = export_csv(
            db,
            operation_type=operation_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as exc:
        client_error(400, str(exc))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="cryptoguard-history.csv"'},
    )


@router.get("/history/{operation_id}", tags=["history"])
def history_detail(operation_id: str, db: Session = Depends(get_db)) -> dict:
    row = get_history(db, operation_id)
    if row is None:
        client_error(404, "No verification record exists with that operation ID.")
    return detail(row)


@router.delete("/history/{operation_id}", tags=["history"])
def history_delete(operation_id: str, db: Session = Depends(get_db)) -> dict:
    if not delete_history(db, operation_id):
        client_error(404, "No verification record exists with that operation ID.")
    return {"deleted": True, "operation_id": operation_id}
