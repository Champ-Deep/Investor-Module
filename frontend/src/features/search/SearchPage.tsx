import { useState } from "react";

import { Button, Card, Label } from "../../components/ui";
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
    <div className="space-y-6">
      <div className="rounded-2xl border border-line bg-surface p-6 sm:p-7">
        <h1 className="max-w-2xl font-display text-2xl font-medium leading-snug tracking-tight text-ink sm:text-[28px]">
          Find the investors ready to write your next check.
        </h1>
        <p className="mt-2 text-sm text-muted">
          Describe who you're looking for — Cadence parses your intent into editable filters and
          ranks the matches by fit and Investment Cadence.
        </p>

        <div className="mt-5 flex flex-col gap-2 sm:flex-row">
          <input
            className="flex-1 rounded-xl border border-line bg-paper px-4 py-3 text-base text-ink outline-none transition placeholder:text-faint focus:border-accent focus:ring-4 focus:ring-accent/10"
            placeholder="e.g. Series B vertical SaaS leads in the US, $15–25M, led recently"
            value={nl}
            onChange={(e) => setNl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runMagic();
            }}
          />
          <Button onClick={runMagic} disabled={loading} className="px-8 py-3 sm:py-0">
            {loading ? "Searching…" : "Search"}
          </Button>
        </div>

        {(chips.length > 0 || explanation) && (
          <div className="mt-4 flex flex-wrap items-center gap-1.5">
            <Label>Understood</Label>
            {chips.map((c) => (
              <button
                key={c.key}
                onClick={() => refine(c.next)}
                className="group inline-flex items-center gap-1 rounded-full border border-accent/20 bg-accent-tint px-2.5 py-1 text-xs font-medium text-accent transition hover:border-accent/40"
                title="Remove this filter"
              >
                {c.label}
                <span className="text-accent/50 transition group-hover:text-accent">×</span>
              </button>
            ))}
            {chips.length === 0 && (
              <span className="text-xs text-faint">no hard filters — ranking by relevance</span>
            )}
          </div>
        )}

        <button
          onClick={() => setShowFilters((s) => !s)}
          className="mt-5 font-mono text-[11px] uppercase tracking-wider text-faint transition hover:text-ink"
        >
          {showFilters ? "— Hide filters" : "+ Refine filters"}
        </button>
        {showFilters && (
          <div className="mt-4 border-t border-line pt-5">
            <FilterRail key={filterKey} filters={filters} onChange={setFilters} />
            <Button onClick={() => runSearch(filters)} className="mt-5 w-full">
              Apply filters
            </Button>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-negative/20 bg-negative/5 p-4 text-sm text-negative">
          {error}
        </div>
      )}
      {loading && !results && (
        <Card>
          <p className="text-sm text-muted">Searching the full universe…</p>
        </Card>
      )}
      {results && <ResultsList firms={results} onExport={() => exportFirmsCsv(results)} />}
      {!results && !loading && !error && (
        <Card>
          <p className="text-sm text-muted">
            Describe the investors you're looking for and press Search. Hard predicates filter the
            full universe first; semantic fit only ranks within the matches.
          </p>
        </Card>
      )}
    </div>
  );
}
