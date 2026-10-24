import { recordResult, resultLabel, severityText, uploadTooLargeMessage, validateHmacTag, validateOptionalSha256 } from "../utils/format";

describe("form validation", () => {
  it("accepts an empty reference digest", () => {
    expect(validateOptionalSha256("  ")).toBeNull();
  });

  it("rejects a short digest", () => {
    expect(validateOptionalSha256("abc")).toBe("SHA-256 digests must be 64 hexadecimal characters.");
  });

  it("accepts a sha256-prefixed digest", () => {
    expect(validateOptionalSha256(`sha256:${"ab".repeat(32)}`)).toBeNull();
  });

  it("checks HMAC tag length", () => {
    expect(validateHmacTag("zz")).toMatch(/64 hexadecimal/);
    expect(validateHmacTag("ab".repeat(32))).toBeNull();
  });

  it("rejects files above the upload limit", () => {
    const oversized = new File([new Uint8Array(12)], "payload.bin");
    expect(uploadTooLargeMessage(oversized, 10)).toMatch(/payload.bin/);
    expect(uploadTooLargeMessage(oversized, 10)).toMatch(/10 B/);
    expect(uploadTooLargeMessage(new File(["ok"], "note.txt"), 10)).toBeNull();
  });

  it("maps cryptographic verdicts to PASS, FAIL, and NOT VERIFIED", () => {
    expect(resultLabel("MATCH")).toBe("PASS");
    expect(resultLabel("VALID")).toBe("PASS");
    expect(resultLabel("MISMATCH")).toBe("FAIL");
    expect(resultLabel("INVALID")).toBe("FAIL");
    expect(resultLabel("NOT VERIFIED")).toBe("NOT VERIFIED");
    expect(recordResult("hmac_generate", "success")).toBe("RECORDED");
    expect(recordResult("hmac_verify", "success")).toBe("PASS");
  });

  it("shows OSV severity only when the advisory included it", () => {
    expect(severityText({})).toBe("No severity was included in this OSV record.");
    expect(severityText({ severity_label: "HIGH", severity: [{ type: "CVSS_V3", score: "CVSS:3.1/AV:N" }] })).toContain("HIGH");
    expect(severityText({ severity_label: "HIGH", severity: [{ type: "CVSS_V3", score: "CVSS:3.1/AV:N" }] })).toContain("CVSS:3.1/AV:N");
  });
});
