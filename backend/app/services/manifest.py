"""Parse npm package.json and Python requirements.txt without installing anything."""

import json
import re
from dataclasses import dataclass, field

from app.core.config import get_settings

EXACT_SEMVER = re.compile(
    r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
REQ_LINE = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?P<extras>\[[^\]]+\])?\s*(?P<spec>.*)$"
)
PINNED = re.compile(r"^===\s*([^\s;]+)$|^==\s*([^\s;]+)$")


@dataclass
class ParsedComponent:
    name: str
    declared_version: str | None
    queried_name: str
    queried_version: str | None
    ecosystem: str
    scope: str
    section: str
    version_status: str
    warning: str | None = None
    purl: str | None = None

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "declared_version": self.declared_version,
            "queried_name": self.queried_name,
            "queried_version": self.queried_version,
            "ecosystem": self.ecosystem,
            "scope": self.scope,
            "section": self.section,
            "version_status": self.version_status,
            "warning": self.warning,
            "purl": self.purl,
        }


@dataclass
class ParsedManifest:
    manifest_format: str
    subject_name: str
    subject_version: str | None
    components: list[ParsedComponent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def normalize_pypi_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def npm_purl(name: str, version: str | None) -> str:
    if name.startswith("@") and "/" in name:
        scope, package = name[1:].split("/", 1)
        purl_name = f"%40{scope}/{package}"
    else:
        purl_name = name
    if version:
        return f"pkg:npm/{purl_name}@{version}"
    return f"pkg:npm/{purl_name}"


def pypi_purl(name: str, version: str | None) -> str:
    if version:
        return f"pkg:pypi/{name}@{version}"
    return f"pkg:pypi/{name}"


def _npm_version_status(raw: object) -> tuple[str, str | None, str | None]:
    if not isinstance(raw, str) or not raw.strip():
        return "missing", None, "No version is declared, so OSV was not queried."
    version = raw.strip()
    if EXACT_SEMVER.fullmatch(version):
        return "exact", version, None
    return (
        "range",
        None,
        f"Version '{version}' is not an exact version. CryptoGuard did not query OSV with it.",
    )


def parse_package_json(text: str, filename: str = "package.json") -> ParsedManifest:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("package.json is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise ValueError("package.json must be a JSON object.")
    subject = data.get("name") if isinstance(data.get("name"), str) and data.get("name").strip() else filename
    subject_version = data.get("version") if isinstance(data.get("version"), str) and data.get("version").strip() else None
    sections = (
        ("dependencies", "runtime", "required"),
        ("devDependencies", "development", "excluded"),
        ("optionalDependencies", "optional", "optional"),
    )
    components: list[ParsedComponent] = []
    warnings: list[str] = []
    for section, label, scope in sections:
        block = data.get(section, {})
        if block is None:
            continue
        if not isinstance(block, dict):
            raise ValueError(f"{section} must be a JSON object of package names and versions.")
        for name, version in block.items():
            if not isinstance(name, str) or not name.strip() or " " in name:
                warnings.append(f"Skipped an invalid package name in {section}.")
                continue
            status, queried, warning = _npm_version_status(version)
            declared = version.strip() if isinstance(version, str) else None
            component = ParsedComponent(
                name=name.strip(),
                declared_version=declared,
                queried_name=name.strip(),
                queried_version=queried,
                ecosystem="npm",
                scope=scope,
                section=label,
                version_status=status,
                warning=warning,
                purl=npm_purl(name.strip(), queried),
            )
            components.append(component)
            if warning:
                warnings.append(f"{name}: {warning}")
    _enforce_component_limit(components)
    return ParsedManifest("npm", subject.strip(), subject_version.strip() if isinstance(subject_version, str) else None, components, warnings)


def parse_requirements(text: str, filename: str = "requirements.txt") -> ParsedManifest:
    components: list[ParsedComponent] = []
    warnings: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith(("-r", "--", "-c", "-e", "-f")) or "://" in line:
            warnings.append(f"Line {line_number} was skipped because it is an option, include, URL, or editable install.")
            continue
        line = line.split(";", 1)[0].strip()
        match = REQ_LINE.fullmatch(line)
        if not match:
            warnings.append(f"Line {line_number} could not be parsed as a package requirement.")
            continue
        name = match.group("name")
        spec = (match.group("spec") or "").strip()
        if not spec:
            status, queried, warning = "missing", None, "No version is declared, so PyPI was not queried."
            declared = None
        else:
            pinned = PINNED.fullmatch(spec)
            if pinned:
                version = pinned.group(1) or pinned.group(2)
                if version and "*" not in version:
                    status, queried, warning = "exact", version, None
                    declared = version
                else:
                    status, queried = "range", None
                    warning = f"Version specifier '{spec}' is not an exact version, so PyPI was not queried."
                    declared = spec
            else:
                status, queried = "range", None
                warning = f"Version specifier '{spec}' is not an exact version, so PyPI was not queried."
                declared = spec
        normalized = normalize_pypi_name(name)
        component = ParsedComponent(
            name=name,
            declared_version=declared,
            queried_name=normalized,
            queried_version=queried,
            ecosystem="PyPI",
            scope="required",
            section="runtime",
            version_status=status,
            warning=warning,
            purl=pypi_purl(normalized, queried),
        )
        components.append(component)
        if warning:
            warnings.append(f"{name}: {warning}")
    _enforce_component_limit(components)
    return ParsedManifest("pypi", filename, None, components, warnings)


def parse_manifest(filename: str, text: str, manifest_format: str = "auto") -> ParsedManifest:
    kind = manifest_format.lower().strip()
    lower_name = filename.lower()
    if kind == "auto":
        if lower_name.endswith("package.json"):
            kind = "npm"
        elif lower_name.endswith("requirements.txt"):
            kind = "pypi"
        elif text.lstrip().startswith("{"):
            kind = "npm"
        else:
            kind = "pypi"
    if kind == "npm":
        return parse_package_json(text, filename)
    if kind == "pypi":
        return parse_requirements(text, filename)
    raise ValueError("manifest_format must be auto, npm, or pypi.")


def _enforce_component_limit(components: list[ParsedComponent]) -> None:
    limit = get_settings().max_components
    if len(components) > limit:
        raise ValueError(f"The manifest declares {len(components)} components, above the limit of {limit}.")
