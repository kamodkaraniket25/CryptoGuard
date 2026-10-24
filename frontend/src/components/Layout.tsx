import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BookOpen,
  Bug,
  Database,
  FileJson,
  FileKey2,
  Fingerprint,
  History,
  KeyRound,
  LayoutDashboard,
  Menu,
  PackageSearch,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  ShieldCheck,
  X,
  type LucideIcon,
} from "lucide-react";
import { Alert, BrandMark } from "./ui";
import { errorMessage, getHealth, getSources } from "../services/api";
import type { HealthResponse, SourceRecord } from "../types";

export type NavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  end: boolean;
  sources?: string[];
};

export const navGroups: { label: string; items: NavItem[] }[] = [
  {
    label: "Platform",
    items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard, end: true }],
  },
  {
    label: "Verification",
    items: [
      { to: "/integrity", label: "Hash Checker", icon: Fingerprint, end: false },
      { to: "/hmac", label: "HMAC Verifier", icon: KeyRound, end: false },
      { to: "/signatures", label: "Digital Signatures", icon: FileKey2, end: false },
    ],
  },
  {
    label: "Records",
    items: [
      { to: "/reports", label: "Reports", icon: History, end: false },
      { to: "/documentation", label: "Documentation", icon: BookOpen, end: false },
    ],
  },
  {
    label: "Supply chain",
    items: [
      { to: "/provenance", label: "Provenance Verification", icon: ShieldCheck, end: false },
      { to: "/dependencies", label: "Dependency Scanner", icon: PackageSearch, end: false, sources: ["osv"] },
      { to: "/sbom", label: "SBOM Generator", icon: FileJson, end: false, sources: ["cyclonedx"] },
      { to: "/vulnerabilities", label: "Vulnerability Intelligence", icon: Bug, end: false, sources: ["osv", "nvd"] },
      { to: "/sources", label: "Datasets & Sources", icon: Database, end: false, sources: ["osv", "nvd", "cyclonedx"] },
    ],
  },
];

export const navItems = navGroups.flatMap((group) => group.items);

function sourceDot(status: string): string {
  if (status === "AVAILABLE") return "bg-[var(--cg-success)]";
  if (status === "DEGRADED") return "bg-[var(--cg-warning)]";
  if (status === "UNAVAILABLE") return "bg-[var(--cg-critical)]";
  return "bg-[var(--cg-faint)]";
}

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthTick, setHealthTick] = useState(0);
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("cg-sidebar");
    if (stored === "collapsed") setCollapsed(true);
  }, []);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((result) => {
        if (active) {
          setHealth(result);
          setHealthError(null);
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        setHealth(null);
        setHealthError(errorMessage(error));
      });
    getSources()
      .then((catalog) => {
        if (active) setSources(catalog.sources);
      })
      .catch(() => {
        if (active) setSources([]);
      });
    return () => {
      active = false;
    };
  }, [location.pathname, healthTick]);

  const path = location.pathname === "/history" ? "/reports" : location.pathname;
  const current = navItems.find((item) => (item.end ? path === item.to : path.startsWith(item.to)));
  const group = navGroups.find((entry) => entry.items.some((item) => item.to === current?.to));
  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return [];
    return navItems.filter((item) => item.label.toLowerCase().includes(needle));
  }, [query]);

  function toggleCollapsed() {
    setCollapsed((value) => {
      window.localStorage.setItem("cg-sidebar", value ? "open" : "collapsed");
      return !value;
    });
  }

  const healthText = health ? `API ${health.status} · database ${health.database}` : healthError ? "Backend unreachable" : "Checking backend";
  const healthDot = health ? "bg-[var(--cg-success)]" : healthError ? "bg-[var(--cg-critical)]" : "bg-[var(--cg-warning)]";

  return (
    <div className="min-h-screen bg-transparent text-[var(--cg-text)]">
      <a className="skip-link" href="#main">Skip to content</a>
      <aside
        className={`${open ? "flex" : "hidden lg:flex"} fixed inset-y-0 left-0 z-30 w-[260px] flex-col border-r border-[var(--cg-line)] bg-[var(--cg-sidebar)] transition-[width] duration-200 ${collapsed ? "lg:w-[76px]" : "lg:w-[260px]"}`}
      >
        <div className="flex items-start justify-between gap-2 px-3.5 pb-3 pt-4">
          <div className="flex min-w-0 items-center gap-2.5">
            <BrandMark size={34} />
            <div className={collapsed ? "lg:sr-only" : ""}>
              <p className="font-[family-name:var(--cg-font-display)] text-[16px] font-semibold tracking-tight">CryptoGuard</p>
              <p className="text-[10px] leading-4 text-[var(--cg-faint)]">Security Verification Platform</p>
            </div>
          </div>
          <button className="btn btn-ghost px-2 lg:hidden" type="button" onClick={() => setOpen(false)} aria-label="Close menu">
            <X size={16} />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto px-2 pb-3" aria-label="Primary">
          {navGroups.map((entry) => (
            <div key={entry.label} className="mb-3">
              <p className={`px-2.5 pb-1 pt-2 text-[10px] font-semibold tracking-[0.14em] text-[var(--cg-faint)] ${collapsed ? "lg:sr-only" : ""}`}>
                {entry.label.toUpperCase()}
              </p>
              <div className="space-y-0.5">
                {entry.items.map((item) => {
                  const Icon = item.icon;
                  const related = (item.sources ?? [])
                    .map((id) => sources.find((source) => source.id === id))
                    .filter((source): source is SourceRecord => Boolean(source));
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      onClick={() => setOpen(false)}
                      title={item.label}
                      className={({ isActive }) =>
                        `group flex h-9 items-center gap-2.5 rounded-md px-2.5 text-[13px] transition-colors ${
                          isActive
                            ? "bg-white/[0.06] text-white shadow-[inset_2px_0_0_var(--cg-cyan)]"
                            : "text-[var(--cg-muted)] hover:bg-white/[0.04] hover:text-[var(--cg-text)]"
                        }`
                      }
                    >
                      <Icon size={16} className="shrink-0" />
                      <span className={`min-w-0 flex-1 truncate ${collapsed ? "lg:sr-only" : ""}`}>{item.label}</span>
                      {related.length > 0 && (
                        <span className={`flex gap-1 ${collapsed ? "lg:hidden" : ""}`} aria-hidden="true">
                          {related.map((source) => (
                            <span key={source.id} title={`${source.name}: ${source.status}`} className={`h-1.5 w-1.5 rounded-full ${sourceDot(source.status)}`} />
                          ))}
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="border-t border-[var(--cg-line)] px-3 py-3">
          <div className={`sidebar-status ${collapsed ? "lg:justify-center lg:px-2" : ""}`} role="status">
            <span className={`mt-1 inline-block h-1.5 w-1.5 shrink-0 rounded-full ${healthDot}`} />
            <div className={collapsed ? "lg:sr-only" : ""}>
              <p className="text-[12px] font-medium text-[var(--cg-text)]">{health ? "Backend connected" : healthError ? "Backend unreachable" : "Checking backend"}</p>
              <p className="text-[11px] leading-4 text-[var(--cg-faint)]">
                {health ? `API ${health.status} · database ${health.database}` : healthError ? "Health check failed" : "Contacting /api/health"}
              </p>
            </div>
          </div>
          <button className="btn btn-ghost mt-2 hidden w-full lg:inline-flex" type="button" onClick={toggleCollapsed}>
            {collapsed ? <PanelLeftOpen size={15} /> : <PanelLeftClose size={15} />}
            <span className={collapsed ? "sr-only" : ""}>{collapsed ? "Expand sidebar" : "Collapse sidebar"}</span>
          </button>
        </div>
      </aside>
      {open && <button className="fixed inset-0 z-20 bg-black/60 lg:hidden" aria-label="Close navigation overlay" onClick={() => setOpen(false)} />}
      <div className={collapsed ? "lg:pl-[76px]" : "lg:pl-[260px]"}>
        <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b border-[var(--cg-line)] bg-[var(--cg-top)] px-4 backdrop-blur md:px-6">
          <button className="btn btn-secondary lg:hidden" type="button" onClick={() => setOpen(true)} aria-expanded={open} aria-label="Open menu">
            <Menu size={16} />
          </button>
          <div className="min-w-0">
            <p className="truncate text-[11px] text-[var(--cg-faint)]">
              CryptoGuard{group ? ` / ${group.label}` : ""}{current ? ` / ${current.label}` : ""}
            </p>
            <p className="truncate font-[family-name:var(--cg-font-display)] text-[15px] font-medium tracking-tight">{current?.label ?? "CryptoGuard"}</p>
          </div>
          <div className="relative ml-auto hidden w-64 md:block">
            <Search size={14} className="pointer-events-none absolute left-2.5 top-2.5 text-[var(--cg-faint)]" />
            <input
              className="field pl-8"
              aria-label="Find a page"
              placeholder="Find a page"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && matches[0]) {
                  navigate(matches[0].to);
                  setQuery("");
                }
              }}
            />
            {query && (
              <div className="absolute right-0 top-11 z-20 w-full rounded-lg border border-[var(--cg-line-strong)] bg-[#121a28] p-1 shadow-panel">
                {matches.length === 0 && <p className="px-2 py-2 text-xs text-[var(--cg-faint)]">No matching page</p>}
                {matches.map((item) => (
                  <button
                    key={item.to}
                    className="btn btn-ghost w-full justify-start"
                    type="button"
                    onClick={() => {
                      navigate(item.to);
                      setQuery("");
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <p className="hidden shrink-0 items-center whitespace-nowrap text-[11px] font-medium uppercase tracking-wide text-[var(--cg-muted)] sm:flex" role="status">
            <span className={`mr-2 inline-block h-1.5 w-1.5 rounded-full ${healthDot}`} />
            {healthText}
          </p>
        </header>
        {healthError && (
          <div className="border-b border-[var(--cg-line)] px-4 py-3 md:px-6">
            <Alert tone="error" onRetry={() => setHealthTick((value) => value + 1)}>{healthError}</Alert>
          </div>
        )}
        <main id="main" className="min-w-0 px-4 py-5 md:px-6">
          <div key={location.pathname} className="page-rise mx-auto max-w-[1180px]">
            <Outlet />
          </div>
        </main>
        <footer className="mx-auto flex max-w-[1180px] items-center justify-between gap-3 px-4 pb-6 text-[11px] leading-5 text-[var(--cg-faint)] md:px-6">
          <p>CryptoGuard{health?.version ? ` ${health.version}` : ""}</p>
          <p className="hidden text-right sm:block">A passed check covers only the evidence that was submitted.</p>
        </footer>
      </div>
    </div>
  );
}
