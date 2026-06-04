import { Link } from "react-router-dom";

import { Badge, cadenceColor, Card } from "../../components/ui";
import type { SearchFirm } from "../../types";

export default function ResultsList({
  firms,
  onExport,
}: {
  firms: SearchFirm[];
  onExport: () => void;
}) {
  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <span>{firms.length.toLocaleString()} firms · ranked by fit</span>
          <button
            onClick={onExport}
            className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            Export CSV
          </button>
        </div>
      }
    >
      {firms.length === 0 && <p className="text-sm text-slate-500">No firms match these filters.</p>}
      <ul className="space-y-2">
        {firms.slice(0, 50).map((f, i) => (
          <li key={f.slug}>
            <Link
              to={`/firm/${f.slug}`}
              className="block rounded-lg border border-slate-100 p-3 transition hover:border-blue-200 hover:bg-blue-50/40"
            >
              <div className="flex items-start gap-3">
                <span className="w-6 pt-0.5 text-right text-xs tabular-nums text-slate-400">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium text-slate-800">{f.name}</span>
                    {!f.is_active && <Badge color="slate">inactive</Badge>}
                  </div>
                  <div className="mt-0.5 text-xs text-slate-500">
                    {f.investor_type} · {f.hq_country || "—"}
                    {f.deal_count != null && <> · {f.deal_count.toLocaleString()} deals</>}
                  </div>
                  {f.top_sectors && f.top_sectors.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {f.top_sectors.map((s) => (
                        <span
                          key={s}
                          className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {f.cadence_score != null && (
                  <Badge color={cadenceColor(f.cadence_score)}>Cadence {f.cadence_score}</Badge>
                )}
              </div>
            </Link>
          </li>
        ))}
      </ul>
      {firms.length > 50 && (
        <p className="mt-3 text-center text-xs text-slate-400">
          Showing top 50 of {firms.length.toLocaleString()} — export CSV for the full ranked list.
        </p>
      )}
    </Card>
  );
}
