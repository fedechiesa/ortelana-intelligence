import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  BarChart3,
  ChevronRight,
  GitBranch,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Play,
  Settings,
  ShieldCheck,
  Sun,
  UsersRound,
  X,
} from "lucide-react";
import { api, hasToken, setToken } from "./services/api";
import type {
  Analytics,
  Collection,
  Dataset,
  Execution,
  Indicators,
} from "./types";
import { ErrorPanel, Loading } from "./components/ui";
import { RunAnalysis } from "./components/RunAnalysis";
import { ExecutionDetail } from "./components/ExecutionDetail";
import { Overview } from "./pages/Overview";
import { Sales } from "./pages/Sales";
import { Executions } from "./pages/Executions";
import { Reviews } from "./pages/Reviews";
import { Monitoring } from "./pages/Monitoring";
import { SettingsPage } from "./pages/Settings";

const pages = [
  {
    id: "overview",
    name: "Overview",
    icon: LayoutDashboard,
    subtitle:
      "A clear view of your business. Every decision, backed by evidence.",
  },
  {
    id: "sales",
    name: "Sales analytics",
    icon: BarChart3,
    subtitle:
      "Explore reporting-year sales and compare what is truly comparable.",
  },
  {
    id: "executions",
    name: "Agent executions",
    icon: GitBranch,
    subtitle:
      "Follow every analysis from its first node to a persisted result.",
  },
  {
    id: "reviews",
    name: "Human review",
    icon: UsersRound,
    subtitle: "Turn commercial evidence into accountable human decisions.",
  },
  {
    id: "monitoring",
    name: "System monitoring",
    icon: Activity,
    subtitle:
      "Real processing metrics, service readiness and technical failures.",
  },
  {
    id: "settings",
    name: "Settings",
    icon: Settings,
    subtitle:
      "Manage versioned policies, data provenance and workspace preferences.",
  },
];
function Mark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 36 36">
        <path
          d="M9 8v20M15 8v20M21 8v20M27 8v20M8 12h20M8 18h20M8 24h20"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path d="M8 28 28 8" stroke="currentColor" strokeWidth="2" />
      </svg>
    </span>
  );
}

function SignIn({ onLogin }: { onLogin: () => void }) {
  const [value, setValue] = useState("demo-operator-local"),
    [error, setError] = useState<Error | null>(null),
    [pending, setPending] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    setToken(value);
    try {
      await api("/auth/me");
      onLogin();
    } catch (error) {
      setError(error as Error);
      setToken("");
    } finally {
      setPending(false);
    }
  }
  return (
    <main className="login">
      <div className="login-story">
        <div className="login-brand">
          <Mark />
          <span>
            ortelana<span>INTELLIGENCE</span>
          </span>
        </div>
        <div>
          <span className="eyebrow">BUSINESS INSIGHT. HUMAN OVERSIGHT.</span>
          <h1>
            Clarity in the data.
            <br />
            Confidence in
            <br />
            <em>the decision.</em>
          </h1>
          <p>
            A connected workspace for commercial intelligence, deterministic
            agents and accountable human review.
          </p>
          <div className="login-proof">
            <ShieldCheck size={19} /> Evidence first. Human authority, always.
          </div>
        </div>
        <small>Academic origins · Independent portfolio implementation</small>
        <div className="woven-pattern" />
      </div>
      <section className="login-form">
        <span className="eyebrow">YOUR INTELLIGENCE WORKSPACE</span>
        <h2>Welcome to Ortelana</h2>
        <p>Sign in with your local access token.</p>
        <form onSubmit={(e) => void submit(e)}>
          <label>
            Access token
            <input
              type="password"
              autoComplete="off"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              required
              minLength={16}
            />
          </label>
          {error && <ErrorPanel error={error} />}
          <button className="button primary" disabled={pending}>
            {pending ? "Connecting…" : "Open workspace"}
            <ArrowRight size={17} />
          </button>
        </form>
        <div className="demo-access">
          <span>LOCAL DEMONSTRATION ACCESS</span>
          <p>Use the included demo credentials on localhost.</p>
          <div>
            <button onClick={() => setValue("demo-operator-local")}>
              Operator · read & analyse
            </button>
            <button onClick={() => setValue("demo-supervisor-local")}>
              Supervisor · review & decide
            </button>
          </div>
          <small>
            Custom tokens can be configured in your local environment.
          </small>
        </div>
      </section>
    </main>
  );
}

export default function App() {
  const [signedIn, setSignedIn] = useState(hasToken),
    [page, setPage] = useState(location.hash.slice(1) || "overview"),
    [menu, setMenu] = useState(false);
  const [dark, setDark] = useState(
    () => localStorage.getItem("ortelana-theme") === "dark",
  );
  const [run, setRun] = useState(false),
    [detail, setDetail] = useState<string | null>(null),
    [notice, setNotice] = useState("");
  const client = useQueryClient();
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("ortelana-theme", dark ? "dark" : "light");
  }, [dark]);
  useEffect(() => {
    const listener = () => setPage(location.hash.slice(1) || "overview");
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  useEffect(() => {
    if (notice) {
      const timer = setTimeout(() => setNotice(""), 5000);
      return () => clearTimeout(timer);
    }
  }, [notice]);
  const me = useQuery({
    queryKey: ["me", signedIn],
    queryFn: () => api<{ name: string; role: string }>("/auth/me"),
    enabled: signedIn,
    retry: false,
  });
  const dataset = useQuery({
    queryKey: ["dataset"],
    queryFn: () => api<Dataset>("/dataset"),
    enabled: !!me.data,
  });
  const indicators = useQuery({
    queryKey: ["indicators"],
    queryFn: () => api<Indicators>("/indicators"),
    enabled: !!me.data,
    refetchInterval: 10000,
  });
  const recent = useQuery({
    queryKey: ["recent"],
    queryFn: () => api<Collection<Execution>>("/executions?page_size=5"),
    enabled: !!me.data,
    refetchInterval: 10000,
  });
  const analytics = useQuery({
    queryKey: ["overview-analytics", dataset.data?.id],
    queryFn: () =>
      api<Analytics>(
        `/analytics?anio_base=${dataset.data!.years.at(-2)}&anio_actual=${dataset.data!.years.at(-1)}`,
      ),
    enabled: !!dataset.data,
  });
  const ready = useQuery({
    queryKey: ["ready"],
    queryFn: () => api<{ status: string }>("/health/ready"),
    enabled: !!me.data,
    refetchInterval: 15000,
  });
  function navigate(id: string) {
    location.hash = id;
    setPage(id);
    setMenu(false);
  }
  function logout() {
    setToken("");
    setSignedIn(false);
    client.clear();
  }
  if (!signedIn || me.error)
    return (
      <SignIn
        onLogin={() => {
          client.clear();
          setSignedIn(true);
          void me.refetch();
        }}
      />
    );
  const current = pages.find((p) => p.id === page) || pages[0];
  const failure =
    dataset.error || indicators.error || recent.error || analytics.error;
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      {menu && <div className="sidebar-scrim" onClick={() => setMenu(false)} />}
      <aside className={`sidebar ${menu ? "open" : ""}`}>
        <div className="brand">
          <Mark />
          <div>
            ortelana<span>INTELLIGENCE</span>
          </div>
          <button
            className="icon-button mobile-close"
            aria-label="Close menu"
            onClick={() => setMenu(false)}
          >
            <X size={18} />
          </button>
        </div>
        <div className="workspace-label">
          <span className="workspace-avatar">OT</span>
          <div>
            Commercial workspace<small>Ortelana Textil</small>
          </div>
          <ChevronRight size={14} />
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {pages.slice(0, 5).map((p) => (
            <button
              key={p.id}
              className={current.id === p.id ? "active" : ""}
              onClick={() => navigate(p.id)}
              aria-current={current.id === p.id ? "page" : undefined}
            >
              <p.icon size={18} />
              <span>{p.name}</span>
              {p.id === "reviews" && !!indicators.data?.pending_reviews && (
                <b>{indicators.data.pending_reviews}</b>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="governance-note">
            <ShieldCheck size={20} />
            <strong>Built for accountable decisions.</strong>
            <p>
              Deterministic analysis.
              <br />
              Human oversight. Full traceability.
            </p>
          </div>
          <nav>
            <button
              className={page === "settings" ? "active" : ""}
              onClick={() => navigate("settings")}
            >
              <Settings size={18} />
              <span>Settings</span>
            </button>
          </nav>
          <div className="user">
            <span className="user-avatar">
              {me.data?.role === "supervisor" ? "S" : "O"}
            </span>
            <div>
              {me.data?.role === "supervisor"
                ? "Local supervisor"
                : "Local operator"}
              <small>Authenticated workspace</small>
            </div>
            <button
              aria-label="Sign out"
              className="icon-button"
              onClick={logout}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            <button
              className="icon-button mobile-menu"
              aria-label="Open menu"
              onClick={() => setMenu(true)}
            >
              <Menu size={20} />
            </button>
            <span className="breadcrumb">
              Workspace <ChevronRight size={13} />{" "}
              <strong>{current.name}</strong>
            </span>
          </div>
          <div>
            <button
              className={`connection ${ready.isSuccess ? "connected" : ""}`}
              onClick={() => navigate("monitoring")}
            >
              <i />
              {ready.isSuccess ? "System connected" : "Checking service"}
            </button>
            <span className="topbar-divider" />
            <button
              className="icon-button"
              aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
              onClick={() => setDark(!dark)}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>
        <main id="main-content" className="main-content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                ORTELANA INTELLIGENCE /{" "}
                {current.id === "overview"
                  ? "COMMAND CENTER"
                  : current.id.toUpperCase()}
              </span>
              <h1>
                {current.name === "Overview"
                  ? "Business overview"
                  : current.name}
              </h1>
              <p>{current.subtitle}</p>
            </div>
            <button
              className="button primary run-button"
              disabled={!dataset.data}
              onClick={() => setRun(true)}
            >
              <Play size={15} fill="currentColor" />
              Run analysis
            </button>
          </div>
          {dataset.data && (
            <div className={`dataset-banner ${dataset.data.mode}`}>
              <span>
                <i />
                {dataset.data.mode === "demo"
                  ? "SYNTHETIC DEMO"
                  : "HISTORICAL DATA"}
              </span>
              <p>
                {dataset.data.mode === "demo"
                  ? "Independent simulated data. All commercial actions are demonstrations."
                  : "Original 2016–2025 history. Reporting-year totals; all commercial actions are simulated."}
              </p>
              <strong>
                {dataset.data.years[0]} — {dataset.data.years.at(-1)}
              </strong>
            </div>
          )}
          {failure ? (
            <ErrorPanel
              error={failure}
              retry={() => void client.invalidateQueries()}
            />
          ) : !dataset.data ||
            !indicators.data ||
            !recent.data ||
            !analytics.data ||
            !me.data ? (
            <Loading />
          ) : (
            <>
              {current.id === "overview" && (
                <Overview
                  analytics={analytics.data}
                  indicators={indicators.data}
                  executions={recent.data}
                  onDetail={setDetail}
                  onReview={() => navigate("reviews")}
                  onSales={() => navigate("sales")}
                />
              )}
              {current.id === "sales" && <Sales dataset={dataset.data} />}
              {current.id === "executions" && (
                <Executions onDetail={setDetail} />
              )}
              {current.id === "reviews" && (
                <Reviews role={me.data.role} onDetail={setDetail} />
              )}
              {current.id === "monitoring" && (
                <Monitoring indicators={indicators.data} onDetail={setDetail} />
              )}
              {current.id === "settings" && (
                <SettingsPage
                  dataset={dataset.data}
                  role={me.data.role}
                  dark={dark}
                  onTheme={() => setDark(!dark)}
                />
              )}
            </>
          )}
          <footer className="app-footer">
            <span>Ortelana Intelligence</span>
            <span>Evidence-led analysis · Human-supervised decisions</span>
            <span>Local portfolio environment</span>
          </footer>
        </main>
      </div>
      {run && dataset.data && (
        <RunAnalysis
          dataset={dataset.data}
          onClose={() => setRun(false)}
          onSuccess={(id) => {
            setRun(false);
            setDetail(id);
            setNotice(
              "Analysis persisted. Open its evidence to review the result.",
            );
          }}
        />
      )}
      {detail && (
        <ExecutionDetail id={detail} onClose={() => setDetail(null)} />
      )}
      {notice && (
        <div className="toast" role="status">
          <ShieldCheck size={18} />
          {notice}
        </div>
      )}
    </div>
  );
}
