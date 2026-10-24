import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const python = existsSync(path.join(".venv", "Scripts", "python.exe"))
  ? path.join(".venv", "Scripts", "python.exe")
  : existsSync(path.join(".venv", "bin", "python"))
    ? path.join(".venv", "bin", "python")
    : "python";

console.log("Starting the CryptoGuard API with Uvicorn on http://127.0.0.1:8000");
console.log("Health check: http://127.0.0.1:8000/api/health");

const child = spawn(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], {
  stdio: "inherit",
});

child.on("exit", (code) => {
  process.exit(code ?? 1);
});
