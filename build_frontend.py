"""Build the React app into public/ so Vercel can serve it beside the API."""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    subprocess.check_call(["npm", "ci", "--prefix", "frontend"], cwd=ROOT)
    subprocess.check_call(["npm", "run", "build", "--prefix", "frontend"], cwd=ROOT)
    public = ROOT / "public"
    if public.exists():
        shutil.rmtree(public)
    shutil.copytree(ROOT / "frontend" / "dist", public)


if __name__ == "__main__":
    main()
