import { Link } from "react-router-dom";

import { Badge, Button, Card } from "../../components/ui";
import type { SearchFirm } from "../../types";

const TYPE_LABEL: Record<string, string> = {
  vc: "VC",
  pe: "PE",
  angel: "Angel",
  growth_equity: "Growth",
  family_office: "Family Office",
  corporate_venture: "CVC",
  pension: "Pension",
  endowment: "Endowment",
  fund_of_funds: "Fund of Funds",
  sovereign_wealth: "SWF",
  solo_gp: "Solo GP",
  accelerator: "Accelerator",
  bank: "Bank",
  insurance: "Insurance",
  hedge_fund: "Hedge Fund",
  foundation: "Foundation",
  other: "Investor",
};

function money(v?: number | null): string | null {
  if (v == null) return null;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${Math.round(v / 1e6)}M`;
  if (v >= 1e3) return `$${Math.round(v / 1e3)}K`;
  return `$${v}`;
}

function fmtStage(slug: string): string {
  return slug
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function stageRange(stages?: string[]): string | null {
  if (!stages || stages.length === 0) return null;
  const a = fmtStage(stages[0]);
  const b = fmtStage(stages[stages.length - 1]);
  return a === b ? a : `${a}–${b}`;
}

function tier(score: number) {
  if (score >= 70) return { word: "High", text: "text-positive", bar: "bg-positive" };
  if (score >= 45) return { word: "Moderate", text: "text-warn", bar: "bg-warn" };
  return { word: "Low", text: "text-negative", bar: "bg-negative" };
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
      <ul className="space-y-2.5">
        {firms.slice(0, 50).map((f, i) => {
          const t = f.cadence_score != null ? tier(f.cadence_score) : null;
          const lo = f.check_lo ?? null;
          const hi = f.check_hi ?? null;
          const check =
            lo != null && hi != null
              ? lo === hi
                ? money(lo)
                : `${money(lo)}–${money(hi)}`
              : null;
          const stg = stageRange(f.stages);
          const year = f.last_deal_at ? f.last_deal_at.slice(0, 4) : null;
          return (
            <li key={f.slug}>
              <Link
                to={`/firm/${f.slug}`}
                className="group block rounded-xl border border-line bg-surface p-4 transition hover:border-accent/40 hover:bg-paper/40"
              >
                <div className="flex items-start gap-3">
                  <span className="w-6 shrink-0 pt-1 text-right font-mono text-xs tabular-nums text-faint">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-ink transition-colors group-hover:text-accent">
                        {f.name}
                      </span>
                      <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-muted">
                        {TYPE_LABEL[f.investor_type] ?? f.investor_type}
                      </span>
                      {!f.is_active && <Badge color="slate">inactive</Badge>}
                    </div>
                    <div className="mt-1 font-mono text-xs text-muted">
                      {f.hq_country || "—"}
                      {year && (
                        <>
                          <span className="text-faint"> · </span>active {year}
                        </>
                      )}
                      {f.deal_count != null && (
                        <>
                          <span className="text-faint"> · </span>
                          {f.deal_count.toLocaleString()} deals
                        </>
                      )}
                    </div>
                    {f.top_sectors && f.top_sectors.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
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
                  {t && (
                    <div className="shrink-0 text-right">
                      <div
                        className={`font-mono text-2xl font-semibold leading-none tabular-nums ${t.text}`}
                      >
                        {f.cadence_score}
                      </div>
                      <div className={`mt-0.5 font-mono text-[10px] uppercase tracking-wider ${t.text} opacity-80`}>
                        {t.word} cadence
                      </div>
                      <div className="ml-auto mt-1 h-1 w-14 overflow-hidden rounded-full bg-ink/[0.06]">
                        <div
                          className={`h-full rounded-full ${t.bar}`}
                          style={{ width: `${f.cadence_score}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                {(stg || check) && (
                  <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 border-t border-line pt-2.5 font-mono text-[11px] text-muted">
                    {stg && (
                      <span>
                        <span className="text-faint">stage </span>
                        {stg}
                      </span>
                    )}
                    {check && (
                      <span>
                        <span className="text-faint">check </span>
                        {check}
                      </span>
                    )}
                  </div>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
      {firms.length > 50 && (
        <p className="mt-4 text-center font-mono text-[11px] uppercase tracking-wider text-faint">
          Top 50 of {firms.length.toLocaleString()} — export for all
        </p>
      )}
    </Card>
  );
}
