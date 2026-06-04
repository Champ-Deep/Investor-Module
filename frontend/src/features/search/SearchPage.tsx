import { useState } from "react";

import { Card } from "../../components/ui";
import { parseQuery, search } from "../../lib/api";
import { exportFirmsCsv } from "../../lib/csv";
import { emptyFilters, type QueryFilters, type SearchFirm } from "../../types";
import ResultsList from "../results/ResultsList";
import FilterRail from "./FilterRail";

export default function SearchPage() {
  const [nl, setNl] = useState("");
  const [filters, setFilters] = useState<QueryFilters>(emptyFilters());
  const [parseVersion, setParseVersion] = useState(0);
  const [explanation, setExplanation] = useState("");
  const [results, setResults] = useState<SearchFirm[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onParse() {
    setError("");
    try {
      const parsed = await parseQuery(nl);
      setFilters(parsed.filters);
      setExplanation(parsed.explanation);
      setParseVersion((v) => v + 1); // remount FilterRail to reflect parsed values
    } catch {
      setError("Parse failed — is the API running on :8123?");
    }
  }

  async function onSearch() {
    setError("");
    setLoading(true);
    try {
      const r = await search(filters);
      setResults(r.firms);
    } catch {
      setError("Search failed — is the API running on :8123?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_1fr]">
      <div className="space-y-4">
        <Card title="Natural-language query">
          <textarea
            className="w-full rounded border border-slate-300 p-2 text-sm"
            rows={3}
            placeholder="Series B vertical SaaS leads, $15M–$25M, US, led in last 6 months"
            value={nl}
            onChange={(e) => setNl(e.target.value)}
          />
          <button
            onClick={onParse}
            className="mt-2 rounded bg-slate-800 px-3 py-1.5 text-sm text-white hover:bg-slate-700"
          >
            Parse → filters
          </button>
          {explanation && <p className="mt-2 text-xs text-slate-500">{explanation}</p>}
          <p className="mt-2 text-xs text-slate-400">
            Parsing fills the editable filters below. Hard predicates filter the full universe; sector
            fit only ranks within the matched set (ADR 0004).
          </p>
        </Card>

        <Card title="Filters">
          <FilterRail key={parseVersion} filters={filters} onChange={setFilters} />
          <button
            onClick={onSearch}
            className="mt-4 w-full rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </Card>
      </div>

      <div>
        {error && <div className="mb-3 rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        {results && <ResultsList firms={results} onExport={() => exportFirmsCsv(results)} />}
        {!results && !error && (
          <Card>
            <p className="text-sm text-slate-500">
              Type a natural-language query and Parse, or set filters directly, then Search.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
