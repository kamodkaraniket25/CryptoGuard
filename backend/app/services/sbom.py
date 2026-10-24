"""CycloneDX 1.7 SBOM generation and schema validation."""

import json
import uuid
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from app.core.config import get_settings
from app.services.manifest import ParsedManifest
from app.utils.timeutil import isoformat_utc, utcnow

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "bom-1.7.schema.json"


@lru_cache
def _validator() -> Draft7Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft7Validator(schema, format_checker=FormatChecker())


def validate_sbom(document: dict) -> list[str]:
    errors: list[str] = []
    for error in sorted(_validator().iter_errors(document), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.path) or "(document)"
        errors.append(f"{location}: {error.message}")
        if len(errors) >= 20:
            break
    return errors


def generate_sbom(parsed: ParsedManifest) -> dict:
    settings = get_settings()
    seen: set[str] = set()
    components: list[dict] = []
    for component in parsed.components:
        base_ref = component.purl or f"{component.ecosystem}/{component.name}"
        ref = base_ref
        suffix = 2
        while ref in seen:
            ref = f"{base_ref}#{suffix}"
            suffix += 1
        seen.add(ref)
        item = {
            "type": "library",
            "name": component.name,
            "bom-ref": ref,
            "scope": component.scope,
        }
        if component.queried_version:
            item["version"] = component.queried_version
        if component.purl:
            item["purl"] = component.purl
        components.append(item)
    subject = {
        "type": "application",
        "name": parsed.subject_name[:255] or "unnamed-project",
        "bom-ref": "cryptoguard-subject",
    }
    if parsed.subject_version:
        subject["version"] = parsed.subject_version[:1024]
    document = {
        "$schema": settings.cyclonedx_schema_url,
        "bomFormat": "CycloneDX",
        "specVersion": settings.cyclonedx_spec_version,
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": isoformat_utc(utcnow()),
            "lifecycles": [{"phase": "pre-build"}],
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "CryptoGuard",
                        "version": settings.app_version,
                        "bom-ref": f"cryptoguard-{settings.app_version}",
                    }
                ]
            },
            "component": subject,
        },
        "components": components,
    }
    return document


def validation_error_count(errors: list[str]) -> int:
    return len(errors)


def schema_exception_message(exc: ValidationError) -> str:
    return exc.message
