import { useState } from "react";

import { Card } from "../../components/ui";
import { parseQuery, search } from "../../lib/api";
import { exportFirmsCsv } from "../../lib/csv";
import { emptyFilters, type QueryFilters, type SearchFirm } from "../../types";
import ResultsList from "../results/ResultsList";
import FilterRail from "./FilterRail";

function money(v: number | null): string | null {
  if (v == null) return null;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${Math.round(v / 1e6)}M`;
  return `$${v.toLocaleString()}`;
}

type Chip = { key: string; label: string; next: QueryFilters };

// The active filters, rendered as removable chips so refining feels instant.
function activeChips(f: QueryFilters): Chip[] {
  const chips: Chip[] = [];
  const fromArray = (field: keyof QueryFilters, prefix = "") => {
    (f[field] as string[]).forEach((v) =>
      chips.push({
        key: `${field}:${v}`,
        label: `${prefix}${v.replace(/_/g, " ")}`,
        next: { ...f, [field]: (f[field] as string[]).filter((x) => x !== v) },
      }),
    );
  };
  fromArray("capital_roles");
  fromArray("investor_types");
  fromArray("stages");
  fromArray("hq_countries", "HQ ");
  fromArray("soft_sectors");
  if (f.check_min != null || f.check_max != null)
    chips.push({
      key: "check",
      label: `${money(f.check_min) ?? "$0"}–${money(f.check_max) ?? "∞"}`,
      next: { ...f, check_min: null, check_max: null },
    });
  if (f.led_within_months != null)
    chips.push({ key: "led", label: `led ≤ ${f.led_within_months}mo`, next: { ...f, led_within_months: null } });
  if (f.lead_only) chips.push({ key: "lead", label: "leads only", next: { ...f, lead_only: false } });
  if (f.require_verified_contact)
    chips.push({ key: "verified", label: "verified contact", next: { ...f, require_verified_contact: false } });
  if (f.aum_min != null)
    chips.push({ key: "aum", label: `AUM ≥ ${money(f.aum_min)}`, next: { ...f, aum_min: null } });
  return chips;
}

export default function SearchPage() {
  const [nl, setNl] = useState("");
  const [filters, setFilters] = useState<QueryFilters>(emptyFilters());
  const [filterKey, setFilterKey] = useState(0);
  const [explanation, setExplanation] = useState("");
  const [results, setResults] = useState<SearchFirm[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  async function runSearch(f: QueryFilters) {
    setError("");
    setLoading(true);
    try {
      const r = await search(f);
      setResults(r.firms);
    } catch {
      setError("Search failed — is the API reachable?");
    } finally {
      setLoading(false);
    }
  }

  // The magic path: parse the natural-language query into filters AND run the search in one action.
  async function runMagic() {
    if (!nl.trim()) return;
    setError("");
    setLoading(true);
    try {
      const parsed = await parseQuery(nl);
      setFilters(parsed.filters);
      setExplanation(parsed.explanation);
      setFilterKey((k) => k + 1);
      const r = await search(parsed.filters);
      setResults(r.firms);
    } catch {
      setError("Search failed — is the API reachable?");
    } finally {
      setLoading(false);
    }
  }

  function refine(f: QueryFilters) {
    setFilters(f);
    setFilterKey((k) => k + 1);
    runSearch(f);
  }

  const chips = activeChips(filters);

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-base outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="Describe the investors you want — e.g. “Series B vertical SaaS leads in the US, $15–25M, led recently”"
            value={nl}
            onChange={(e) => setNl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runMagic();
            }}
          />
          <button
            onClick={runMagic}
            disabled={loading}
            className="rounded-lg bg-blue-600 px-6 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-60"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>

        {(chips.length > 0 || explanation) && (
          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-xs font-medium text-slate-400">✨ Understood</span>
            {chips.map((c) => (
              <button
                key={c.key}
                onClick={() => refine(c.next)}
                className="group inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 hover:bg-blue-100"
                title="Remove this filter"
              >
                {c.label}
                <span className="text-blue-400 group-hover:text-blue-600">×</span>
              </button>
            ))}
            {chips.length === 0 && (
              <span className="text-xs text-slate-400">no hard filters — ranking by relevance</span>
            )}
          </div>
        )}

        <button
          onClick={() => setShowFilters((s) => !s)}
          className="mt-3 text-xs text-slate-400 hover:text-slate-600"
        >
          {showFilters ? "▾ Hide filters" : "▸ Refine filters"}
        </button>
        {showFilters && (
          <div className="mt-3 border-t border-slate-100 pt-4">
            <FilterRail key={filterKey} filters={filters} onChange={setFilters} />
            <button
              onClick={() => runSearch(filters)}
              className="mt-4 w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500"
            >
              Apply filters
            </button>
          </div>
        )}
      </div>

      {error && <div className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {loading && !results && (
        <Card>
          <p className="text-sm text-slate-500">Searching the full universe…</p>
        </Card>
      )}
      {results && <ResultsList firms={results} onExport={() => exportFirmsCsv(results)} />}
      {!results && !loading && !error && (
        <Card>
          <p className="text-sm text-slate-500">
            Describe the investors you're looking for and hit Search — Cadence parses your intent
            into editable filters, then ranks the matches by fit and Investment Cadence.
          </p>
        </Card>
      )}
    </div>
  );
}
