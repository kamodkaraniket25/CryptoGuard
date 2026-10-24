"""Request bodies for CryptoGuard JSON endpoints."""

from pydantic import BaseModel, Field, field_validator


class HmacGenerateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    secret: str | None = Field(default=None, max_length=512)


class HmacVerifyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    secret: str = Field(min_length=1, max_length=512)
    tag: str = Field(min_length=64, max_length=80)


class SignRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    private_key_pem: str = Field(min_length=1, max_length=20000)


class VerifySignatureRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    public_key_pem: str = Field(min_length=1, max_length=20000)
    signature: str = Field(min_length=1, max_length=20000)


class ProvenanceSignRequest(BaseModel):
    record: dict
    private_key_pem: str = Field(min_length=1, max_length=20000)


class VulnerabilityQueryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=214)
    ecosystem: str
    version: str = Field(min_length=1, max_length=128)
    refresh: bool = False
    include_nvd: bool = False

    @field_validator("ecosystem")
    @classmethod
    def ecosystem_name(cls, value: str) -> str:
        if value not in {"npm", "PyPI"}:
            raise ValueError("Ecosystem must be npm or PyPI.")
        return value


class PackageQuery(BaseModel):
    name: str = Field(min_length=1, max_length=214)
    ecosystem: str
    version: str = Field(min_length=1, max_length=128)

    @field_validator("ecosystem")
    @classmethod
    def ecosystem_name(cls, value: str) -> str:
        if value not in {"npm", "PyPI"}:
            raise ValueError("Ecosystem must be npm or PyPI.")
        return value


class VulnerabilityBatchRequest(BaseModel):
    packages: list[PackageQuery] = Field(min_length=1, max_length=40)
    refresh: bool = False


class NvdLookupRequest(BaseModel):
    cve_id: str = Field(min_length=1, max_length=32)
    refresh: bool = False


class SourceCheckRequest(BaseModel):
    sources: list[str] | None = None
