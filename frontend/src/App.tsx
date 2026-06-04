import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

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
      className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
        on ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
      }`}
      title={on ? "Live (API key set)" : "Offline default — add a key in .env to enable"}
    >
      {label}
    </span>
  );
  return (
    <div className="hidden items-center gap-1 md:flex">
      {chip(
        s.llm_parse === "openrouter" ? `LLM · ${s.llm_model ?? "openrouter"}` : "LLM · heuristic",
        s.llm_parse === "openrouter",
      )}
      {chip(
        s.data_source === "crunchbase"
          ? "Data · Crunchbase 2015"
          : s.data_source === "lakeb2b"
            ? "Data · LakeB2B"
            : "Data · seed",
        s.data_source !== "seed",
      )}
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
          <Link to="/" className="text-lg font-semibold tracking-tight">
            Cadence
          </Link>
          <span className="hidden text-xs text-slate-400 sm:inline">
            Champions Infometrics · powered by the LakeB2B Data API
          </span>
          <nav className="ml-auto flex items-center gap-4 text-sm">
            <StatusBadge />
            <Link to="/" className="text-slate-600 hover:text-blue-600">
              Search
            </Link>
            <Link to="/freshness" className="text-slate-600 hover:text-blue-600">
              Freshness
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/firm/:slug" element={<FirmProfile />} />
          <Route path="/freshness" element={<FreshnessDashboard />} />
        </Routes>
      </main>
      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-slate-400">
        Champions Infometrics · Cadence — demo. Investor data: Crunchbase (Oct 2015 snapshot,
        CC BY-NC) for testing only; verified-contact data is the LakeB2B layer.
      </footer>
    </div>
  );
}
