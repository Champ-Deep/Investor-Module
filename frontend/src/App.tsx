import { type ReactNode, useEffect, useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";

import FreshnessDashboard from "./features/freshness/FreshnessDashboard";
import FirmProfile from "./features/profile/FirmProfile";
import SearchPage from "./features/search/SearchPage";
import { getStatus, type AppStatus } from "./lib/api";

function StatusBadge() {
  const [s, setS] = useState<AppStatus | null>(null);
  useEffect(() => {
    getStatus()
      .then(setS)
      .catch(() => {});
  }, []);
  if (!s) return null;
  const chip = (label: string, on: boolean) => (
    <span
      className={`hidden items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider md:inline-flex ${
        on ? "bg-positive/10 text-positive" : "bg-ink/[0.05] text-faint"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${on ? "bg-positive" : "bg-faint"}`} />
      {label}
    </span>
  );
  return (
    <div className="flex items-center gap-1.5">
      {chip(
        s.llm_parse === "openrouter" ? `LLM ${s.llm_model ?? ""}`.trim() : "LLM heuristic",
        s.llm_parse === "openrouter",
      )}
      {chip(
        s.data_source === "crunchbase"
          ? "Crunchbase 2015"
          : s.data_source === "lakeb2b"
            ? "LakeB2B"
            : "Seed data",
        s.data_source !== "seed",
      )}
    </div>
  );
}

function NavItem({ to, children }: { to: string; children: ReactNode }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `text-sm transition-colors ${isActive ? "font-medium text-ink" : "text-muted hover:text-accent"}`
      }
    >
      {children}
    </NavLink>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-line bg-paper/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-5 py-3.5">
          <Link to="/" className="flex items-baseline gap-2.5">
            <span className="font-display text-xl font-semibold tracking-tight text-ink">
              Cadence
            </span>
            <span className="hidden text-[11px] uppercase tracking-[0.14em] text-faint sm:inline">
              Champions Infometrics
            </span>
          </Link>
          <div className="ml-auto flex items-center gap-4">
            <StatusBadge />
            <nav className="flex items-center gap-4">
              <NavItem to="/">Search</NavItem>
              <NavItem to="/freshness">Freshness</NavItem>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/firm/:slug" element={<FirmProfile />} />
          <Route path="/freshness" element={<FreshnessDashboard />} />
        </Routes>
      </main>

      <footer className="mx-auto w-full max-w-6xl px-5 pb-10 pt-4 text-xs leading-relaxed text-faint">
        Champions Infometrics · Cadence — demo. Investor data: Crunchbase (Oct 2015 snapshot,
        CC&nbsp;BY-NC) for testing only; verified-contact data is the LakeB2B layer.
      </footer>
    </div>
  );
}
