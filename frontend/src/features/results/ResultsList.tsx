import { Link } from "react-router-dom";

import { Badge, Button, Card } from "../../components/ui";
import type { SearchFirm } from "../../types";

function CadencePill({ score }: { score: number }) {
  const tone =
    score >= 70
      ? "text-positive bg-positive/10"
      : score >= 45
        ? "text-warn bg-warn/10"
        : "text-negative bg-negative/10";
  return (
    <span className={`inline-flex shrink-0 items-baseline gap-1 rounded-full px-2.5 py-1 ${tone}`}>
      <span className="font-mono text-sm font-semibold tabular-nums">{score}</span>
      <span className="text-[10px] uppercase tracking-wider opacity-70">cadence</span>
    </span>
  );
}

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
          <span className="font-mono text-sm">
            <span className="font-semibold tabular-nums text-ink">
              {firms.length.toLocaleString()}
            </span>{" "}
            <span className="text-faint">firms · ranked by fit</span>
          </span>
          <Button variant="ghost" onClick={onExport} className="px-3 py-1.5 text-xs">
            Export CSV
          </Button>
        </div>
      }
    >
      {firms.length === 0 && <p className="text-sm text-muted">No firms match these filters.</p>}
      <ul className="-mx-2 divide-y divide-line">
        {firms.slice(0, 50).map((f, i) => (
          <li key={f.slug}>
            <Link
              to={`/firm/${f.slug}`}
              className="flex items-start gap-3 rounded-lg px-2 py-3 transition hover:bg-paper"
            >
              <span className="w-7 shrink-0 pt-0.5 text-right font-mono text-xs tabular-nums text-faint">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate font-medium text-ink">{f.name}</span>
                  {!f.is_active && <Badge color="slate">inactive</Badge>}
                </div>
                <div className="mt-0.5 font-mono text-xs text-muted">
                  {f.investor_type}
                  <span className="text-faint"> · </span>
                  {f.hq_country || "—"}
                  {f.deal_count != null && (
                    <>
                      <span className="text-faint"> · </span>
                      {f.deal_count.toLocaleString()} deals
                    </>
                  )}
                </div>
                {f.top_sectors && f.top_sectors.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {f.top_sectors.map((s) => (
                      <span
                        key={s}
                        className="rounded border border-line px-1.5 py-0.5 text-[10px] text-muted"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {f.cadence_score != null && <CadencePill score={f.cadence_score} />}
            </Link>
          </li>
        ))}
      </ul>
      {firms.length > 50 && (
        <p className="mt-4 text-center font-mono text-[11px] uppercase tracking-wider text-faint">
          Top 50 of {firms.length.toLocaleString()} — export for all
        </p>
      )}
    </Card>
  );
}
