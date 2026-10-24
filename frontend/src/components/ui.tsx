import { createContext, useContext, useEffect, useId, useState, type ReactNode } from "react";
import { resultLabel, uploadTooLargeMessage } from "../utils/format";
import { downloadText } from "../utils/download";
import { AlertTriangle, Check, Copy, Download, Eye, EyeOff, Info, RefreshCw, Upload } from "lucide-react";

type ToastItem = { id: number; message: string };

const ToastContext = createContext<(message: string) => void>(() => undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  function push(message: string) {
    const id = Date.now() + Math.random();
    setItems((current) => [...current, { id, message }]);
    window.setTimeout(() => {
      setItems((current) => current.filter((item) => item.id !== id));
    }, 2400);
  }

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {items.map((item) => (
          <div key={item.id} className="toast" role="status">{item.message}</div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): (message: string) => void {
  return useContext(ToastContext);
}

export async function copyText(value: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return false;
  }
}

export function CopyButton({ value, label = "Copy" }: { value: string; label?: string }) {
  const push = useToast();
  const [done, setDone] = useState(false);

  async function onCopy() {
    const ok = await copyText(value);
    if (!ok) {
      push("Clipboard is unavailable in this browser.");
      return;
    }
    setDone(true);
    push("Copied to clipboard");
    window.setTimeout(() => setDone(false), 1600);
  }

  return (
    <button className="btn btn-secondary" type="button" onClick={() => void onCopy()}>
      {done ? <Check size={14} /> : <Copy size={14} />}
      {done ? "Copied" : label}
    </button>
  );
}

export function PageHeader({
  kicker,
  title,
  description,
  actions,
}: {
  kicker?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        {kicker && <p className="kicker">{kicker}</p>}
        <h1>{title}</h1>
        {description && <p className="lede">{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

export function Alert({
  tone,
  children,
  onRetry,
}: {
  tone: "error" | "warning" | "info";
  children: ReactNode;
  onRetry?: () => void;
}) {
  const Icon = tone === "info" ? Info : AlertTriangle;
  return (
    <div className={`alert alert-${tone}`} role={tone === "error" ? "alert" : "status"}>
      <div className="flex gap-2">
        <Icon size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
        <div>{children}</div>
      </div>
      {onRetry && (
        <button className="btn btn-secondary" type="button" onClick={onRetry}>
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}

export function badgeTone(value: string): "ok" | "bad" | "warn" | "muted" {
  const text = value.toUpperCase();
  if (text.includes("NOT CHECKED") || text.includes("NOT VERIFIED") || text.includes("NOT_VERIFIED")) return "muted";
  if (/(UNAVAILABLE|MISMATCH|INVALID|FAILED|ERROR|CRITICAL)/.test(text)) return "bad";
  if (/(DEGRADED|WARNING|INCOMPLETE|SKIPPED)/.test(text)) return "warn";
  if (/(AVAILABLE|MATCH|VALID|SUCCESS|RESPONDED|^OK$|^PASS$)/.test(text)) return "ok";
  if (text === "FAIL") return "bad";
  return "muted";
}

export function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${badgeTone(value)}`}>{value}</span>;
}

export function ResultBadge({ value }: { value: string }) {
  const label = resultLabel(value);
  return <span className={`badge badge-${badgeTone(label)}`}>{label}</span>;
}

export function Limitations({ items }: { items: string[] }) {
  if (!items.length) return null;
  return (
    <details className="disclosure">
      <summary>What this result does not prove</summary>
      <ul className="space-y-1 pb-2 text-sm text-[var(--cg-muted)]">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </details>
  );
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="empty">
      <Info className="mx-auto text-[var(--cg-cyan)]" size={18} />
      <h2>{title}</h2>
      <p>{body}</p>
      {action && <div className="empty-actions">{action}</div>}
    </div>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <p className="flex items-center gap-2 text-sm text-[var(--cg-muted)]" role="status">
      <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--cg-line-strong)] border-t-[var(--cg-cyan)]" />
      {label}
    </p>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function Tip({ label, text }: { label: string; text: string }) {
  return (
    <span className="tip" tabIndex={0}>
      {label}
      <span className="tip-bubble" role="tooltip">{text}</span>
    </span>
  );
}

export function Tabs({
  tabs,
  value,
  onChange,
}: {
  tabs: { id: string; label: string }[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className="tab"
          type="button"
          role="tab"
          aria-selected={value === tab.id}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export function Dialog({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog" role="dialog" aria-modal="true" aria-label={title} onClick={(event) => event.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

export function FileDrop({
  id,
  label,
  file,
  hint,
  onFile,
  maxBytes,
  onReject,
}: {
  id: string;
  label: string;
  file: File | null;
  hint: string;
  onFile: (file: File | null) => void;
  maxBytes?: number;
  onReject?: (message: string) => void;
}) {
  const [hot, setHot] = useState(false);
  const described = useId();

  function take(list: FileList | null) {
    const next = list?.[0] ?? null;
    if (next && maxBytes) {
      const message = uploadTooLargeMessage(next, maxBytes);
      if (message) {
        onReject?.(message);
        return;
      }
    }
    onFile(next);
  }

  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <div
        className={`dropzone ${hot ? "is-hot" : ""} ${file ? "has-file" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setHot(true);
        }}
        onDragLeave={() => setHot(false)}
        onDrop={(event) => {
          event.preventDefault();
          setHot(false);
          take(event.dataTransfer.files);
        }}
      >
        <input id={id} aria-describedby={described} type="file" onChange={(event) => take(event.target.files)} />
        <div className="flex flex-col items-center gap-2">
          <span className="icon-tile">
            <Upload size={16} />
          </span>
          <p className="text-sm text-[var(--cg-text)]">{file ? file.name : "Drop a file here, or browse"}</p>
          <p id={described} className="hint">{hint}</p>
        </div>
      </div>
    </div>
  );
}

export function DownloadButton({
  filename,
  content,
  mime,
  label,
}: {
  filename: string;
  content: string;
  mime?: string;
  label: string;
}) {
  const push = useToast();
  return (
    <button
      className="btn btn-secondary"
      type="button"
      onClick={() => {
        downloadText(filename, content, mime);
        push(`${label} downloaded`);
      }}
    >
      <Download size={14} />
      {label}
    </button>
  );
}

export function SecretInput({
  id,
  label,
  value,
  onChange,
  placeholder,
  hint,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  hint?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <div className="flex gap-2">
        <input
          id={id}
          className="field font-mono"
          type={show ? "text" : "password"}
          autoComplete="off"
          spellCheck={false}
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          className="btn btn-secondary"
          type="button"
          onClick={() => setShow((current) => !current)}
          aria-label={show ? `Hide ${label}` : `Show ${label}`}
        >
          {show ? <EyeOff size={14} /> : <Eye size={14} />}
        </button>
      </div>
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}

export function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <span className="brand-mark" style={{ width: size, height: size }}>
      <svg width={size * 0.62} height={size * 0.62} viewBox="0 0 64 64" aria-hidden="true">
        <path d="M32 6 54 16v16c0 14-9 23-22 26C19 55 10 46 10 32V16z" fill="#0891b2" />
        <path d="M32 14 46 20.5V32c0 9.2-5.8 15.4-14 17.8C23.8 47.4 18 41.2 18 32V20.5z" fill="#67e8f9" />
        <path d="m27.5 33.5 4.2 4.2 9-10" fill="none" stroke="#062033" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}

export function ResultBanner({
  verdict,
  explanation,
  technical,
}: {
  verdict: string;
  explanation: string;
  technical?: string;
}) {
  const label = resultLabel(verdict);
  const tone = label === "PASS" ? "result-pass" : label === "FAIL" ? "result-fail" : "result-neutral";
  return (
    <div className={tone} role="status">
      <ResultBadge value={verdict} />
      {technical && <p className="mt-2 text-xs text-[var(--cg-faint)]">Technical result: {technical}</p>}
      <p className="mt-2 text-sm leading-6 text-[var(--cg-muted)]">{explanation}</p>
    </div>
  );
}

export function JsonView({ value }: { value: unknown }) {
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return (
    <pre className="mono-block">
      {tokenize(text).map((token, index) => (
        <span key={`${token.kind}-${index}`} className={token.kind === "plain" ? undefined : `json-${token.kind}`}>
          {token.text}
        </span>
      ))}
    </pre>
  );
}

function tokenize(input: string): { kind: string; text: string }[] {
  const tokens: { kind: string; text: string }[] = [];
  const pattern = /"(?:\\.|[^"\\])*"\s*:|"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\b(?:true|false|null)\b/g;
  let last = 0;
  for (const match of input.matchAll(pattern)) {
    const index = match.index ?? 0;
    if (index > last) tokens.push({ kind: "plain", text: input.slice(last, index) });
    const text = match[0];
    let kind = "number";
    if (text.startsWith("\"")) kind = text.trimEnd().endsWith(":") ? "key" : "string";
    else if (text === "true" || text === "false") kind = "bool";
    else if (text === "null") kind = "null";
    tokens.push({ kind, text });
    last = index + text.length;
  }
  if (last < input.length) tokens.push({ kind: "plain", text: input.slice(last) });
  return tokens;
}

export function Steps({ items }: { items: { label: string; detail: string; state: "idle" | "current" | "done" }[] }) {
  return (
    <ol className="steps">
      {items.map((item, index) => (
        <li key={item.label} className={`step ${item.state === "idle" ? "" : item.state === "current" ? "is-current" : "is-done"}`}>
          0{index + 1} {item.label}
          <strong>{item.detail}</strong>
        </li>
      ))}
    </ol>
  );
}
