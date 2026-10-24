"""Capture CryptoGuard website screenshots for the project report."""

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(r"c:\Users\kamod\OneDrive\Desktop\CIS-030(Main)")
OUT = ROOT / "report_images"
APP = "http://127.0.0.1:3000"
API = "http://127.0.0.1:8000"
NOTE = OUT / "release-note.txt"


def set_value(driver, element_id, value):
    driver.execute_script(
        """
        const el = document.getElementById(arguments[0]);
        const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement : HTMLInputElement;
        const setter = Object.getOwnPropertyDescriptor(proto.prototype, 'value').set;
        const tracker = el._valueTracker;
        if (tracker) tracker.setValue(arguments[1] === '' ? (el.value || 'x') : '');
        setter.call(el, arguments[1]);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        """,
        element_id,
        value,
    )


def body_text(driver):
    return driver.find_element(By.TAG_NAME, "body").text


def wait_text(driver, snippet, timeout=30):
    WebDriverWait(driver, timeout).until(lambda d: snippet in body_text(d))


def click_text(driver, snippet):
    driver.execute_script(
        """
        const wanted = arguments[0];
        const nodes = [...document.querySelectorAll('button')];
        const node = nodes.find((item) => item.innerText.includes(wanted) && !item.disabled);
        if (!node) throw new Error('missing button ' + wanted);
        node.click();
        """,
        snippet,
    )


def shot(driver, name):
    time.sleep(0.4)
    driver.execute_script("document.querySelectorAll('.toast-stack').forEach((node) => node.remove())")
    time.sleep(0.2)
    path = OUT / name
    driver.save_screenshot(str(path))
    print("saved", path.name, flush=True)


def open_page(driver, path, ready):
    driver.get(APP + path)
    wait_text(driver, ready, 25)
    wait_text(driver, "Backend connected", 20)


def keygen():
    request = urllib.request.Request(API + "/api/signatures/keygen", data=b"{}", method="POST")
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return payload["result"]["private_key_pem"]


def main():
    OUT.mkdir(exist_ok=True)
    NOTE.write_text("Release candidate 1.4.0\n", encoding="utf-8")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--disable-gpu")
    driver = webdriver.Edge(options=options)
    driver.set_window_size(1440, 1200)
    rest = "--rest" in sys.argv
    try:
        if rest:
            print("continuing from provenance", flush=True)
        else:
            open_page(driver, "/", "Verify what you are about to trust.")
            shot(driver, "01-dashboard.png")
            driver.find_element(By.CSS_SELECTOR, "aside").screenshot(str(OUT / "02-sidebar.png"))
            print("saved 02-sidebar.png", flush=True)

            open_page(driver, "/integrity", "Hash Checker")
            driver.find_element(By.ID, "integrity-file").send_keys(str(NOTE))
            wait_text(driver, "release-note.txt")
            click_text(driver, "Calculate SHA-256")
            wait_text(driver, "Technical result: NOT VERIFIED")
            shot(driver, "03-hash-not-verified.png")
            digest = driver.execute_script(
                "return document.querySelector('.digest-block p.break-all').textContent.trim()"
            )
            set_value(driver, "reference-digest", digest)
            click_text(driver, "Compare Hashes")
            wait_text(driver, "Technical result: MATCH")
            shot(driver, "04-hash-pass.png")
            changed = digest[:-1] + ("0" if digest[-1] != "0" else "1")
            set_value(driver, "reference-digest", changed)
            click_text(driver, "Compare Hashes")
            wait_text(driver, "Technical result: MISMATCH")
            shot(driver, "05-hash-fail.png")

            open_page(driver, "/hmac", "HMAC Verifier")
            click_text(driver, "Generate authentication tag")
            wait_text(driver, "Verify tag", 20)
            WebDriverWait(driver, 20).until(lambda d: len(d.find_element(By.ID, "verify-tag").get_attribute("value") or "") == 64)
            click_text(driver, "Verify tag")
            wait_text(driver, "Technical result: VALID")
            click_text(driver, "Clear secret")
            shot(driver, "06-hmac.png")

            open_page(driver, "/signatures", "Digital Signatures")
            click_text(driver, "Generate key pair")
            WebDriverWait(driver, 30).until(lambda d: "BEGIN" in (d.find_element(By.ID, "public-key").get_attribute("value") or ""))
            click_text(driver, "Sign message")
            WebDriverWait(driver, 20).until(lambda d: len(d.find_element(By.ID, "signature-value").get_attribute("value") or "") > 40)
            click_text(driver, "Verify signature")
            wait_text(driver, "Technical result: VALID")
            driver.execute_script("document.getElementById('signature-value').scrollIntoView({block:'center'})")
            shot(driver, "07-signatures.png")

            open_page(driver, "/history", "Reports")
            WebDriverWait(driver, 25).until(lambda d: "Loading history" not in body_text(d))
            shot(driver, "08-reports.png")

        digest = hashlib.sha256(NOTE.read_bytes()).hexdigest()
        record = json.dumps(
            {
                "artifact_sha256": digest,
                "source_repository": "https://example.com/demo.git",
                "source_revision": "abc123def",
                "builder_id": "local-builder",
                "build_timestamp": "2026-10-17T00:00:00Z",
            },
            indent=2,
        )
        private_key = keygen()
        open_page(driver, "/provenance", "Provenance")
        set_value(driver, "provenance-json", record)
        set_value(driver, "provenance-private", private_key)
        time.sleep(0.4)
        click_text(driver, "Sign canonical record")
        try:
            WebDriverWait(driver, 30).until(lambda d: '"signature"' in (d.find_element(By.ID, "provenance-json").get_attribute("value") or ""))
        except Exception:
            alert = driver.execute_script("return document.querySelector('[role=alert]')?.innerText || 'no alert'")
            print("provenance sign alert:", alert, flush=True)
            raise
        set_value(driver, "provenance-private", "")
        time.sleep(0.4)
        still = driver.execute_script("return document.getElementById('provenance-private').value")
        if "PRIVATE KEY" in (still or ""):
            raise RuntimeError("Private key was still visible after clearing the provenance field.")
        driver.find_element(By.ID, "artifact-file").send_keys(str(NOTE))
        wait_text(driver, "release-note.txt")
        click_text(driver, "Verify provenance")
        wait_text(driver, "Download report")
        driver.execute_script("document.querySelector('[role=status]')?.scrollIntoView({block:'center'})")
        shot(driver, "09-provenance.png")

        manifest = str(ROOT / "sample_data" / "package.json")
        open_page(driver, "/dependencies", "Dependency")
        driver.find_element(By.ID, "manifest-file").send_keys(manifest)
        wait_text(driver, "package.json")
        click_text(driver, "Scan manifest")
        wait_text(driver, "left-pad", 60)
        shot(driver, "10-dependencies.png")

        open_page(driver, "/sbom", "SBOM")
        driver.find_element(By.ID, "sbom-file").send_keys(manifest)
        wait_text(driver, "package.json")
        click_text(driver, "Generate SBOM")
        wait_text(driver, "components from the parsed manifest", 30)
        shot(driver, "11-sbom.png")

        open_page(driver, "/vulnerabilities", "Vulnerability")
        click_text(driver, "Query advisories")
        try:
            WebDriverWait(driver, 45).until(
                lambda d: "advisory record" in body_text(d) or "OSV UNAVAILABLE" in body_text(d)
            )
        except Exception:
            print("vulnerability query did not finish; saving the page anyway", flush=True)
        shot(driver, "12-vulnerabilities.png")

        open_page(driver, "/sources", "Datasets")
        wait_text(driver, "OSV")
        shot(driver, "13-sources.png")

        open_page(driver, "/documentation", "Documentation")
        driver.execute_script("document.getElementById('limits').scrollIntoView({block:'start'})")
        time.sleep(0.4)
        shot(driver, "14-documentation.png")

        driver.get(API + "/docs")
        wait_text(driver, "integrity", 25)
        shot(driver, "15-api-docs.png")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
