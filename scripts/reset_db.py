"""Delete the local CryptoGuard SQLite database so the next startup recreates it."""

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
DATA_DIR = BACKEND_ROOT / "data"

def main() -> None:
    removed = 0
    if DATA_DIR.exists():
        for path in DATA_DIR.glob("cryptoguard.db*"):
            path.unlink()
            removed += 1
            print(f"Removed {path}")
    if removed == 0:
        print("No CryptoGuard database file was found.")
    else:
        print("Start the backend again to create an empty database.")

if __name__ == "__main__":
    main()
