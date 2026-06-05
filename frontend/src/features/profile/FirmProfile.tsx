import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { Badge, Card, verifiedBadge } from "../../components/ui";
import { getFirm } from "../../lib/api";

function money(v: number | null | undefined): string {
  if (v == null) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${Math.round(v / 1e3)}K`;
  return `$${Math.round(v)}`;
}

function tierText(s: number): string {
  return s >= 70 ? "text-positive" : s >= 45 ? "text-warn" : "text-negative";
}

function Bar({ pct }: { pct: number }) {
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-ink/[0.06]">
      <div className="h-full rounded-full bg-accent" style={{ width: `${Math.max(2, Math.min(100, pct))}%` }} />
    </div>
  );
}

export default function FirmProfile() {
  const { slug } = useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["firm", slug],
    queryFn: () => getFirm(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-sm text-muted">Loading…</p>;
  if (isError || !data) return <p className="text-sm text-negative">Firm not found.</p>;
  const f = data.firm;

  return (
    <div className="space-y-5">
      <Link to="/" className="font-mono text-[11px] uppercase tracking-wider text-muted hover:text-accent">
        ← Back to search
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-medium tracking-tight text-ink">{f.name}</h1>
          <div className="mt-1.5 flex items-center gap-2 font-mono text-xs text-muted">
            <span>{f.investor_type}</span>
            <span className="text-faint">·</span>
            <span>{f.hq_country || "—"}</span>
            {data.is_active ? (
              <Badge color="green">active</Badge>
            ) : (
              <Badge color="slate">inactive</Badge>
            )}
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {data.roles.map((r) => (
              <Badge key={r} color="blue">
                {r.replace(/_/g, " ")}
              </Badge>
            ))}
          </div>
        </div>
        {data.cadence && (
          <div className="text-right">
            <div className={`font-mono text-5xl font-semibold tabular-nums ${tierText(data.cadence.score)}`}>
              {data.cadence.score}
            </div>
            <div className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.14em] text-faint">
              Investment Cadence
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {data.cadence && (
          <Card title="Why this Cadence">
            <ul className="space-y-2.5">
              {data.cadence.top_factors.map((fac) => (
                <li key={fac.feature}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-muted">{fac.feature.replace(/_/g, " ")}</span>
                    <span className="font-mono tabular-nums text-faint">
                      {Math.round(fac.contribution * 100)} pts
                    </span>
                  </div>
                  <Bar pct={fac.value * 100} />
                </li>
              ))}
            </ul>
            <p className="mt-4 text-[11px] leading-relaxed text-faint">
              {data.cadence.model_version} · predicts a NEW deal within 90 days · backtest hit-rate{" "}
              {data.cadence.readiness_hit_rate != null
                ? `${Math.round(data.cadence.readiness_hit_rate * 100)}%`
                : "n/a"}
            </p>
          </Card>
        )}

        <Card title="Behavioral sector profile">
          {data.sector_profile.length === 0 ? (
            <p className="text-sm text-muted">No deal-derived sectors.</p>
          ) : (
            <ul className="space-y-2.5">
              {data.sector_profile.map((s) => (
                <li key={s.slug}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-ink">{s.name}</span>
                    <span className="font-mono tabular-nums text-faint">
                      {Math.round(s.weight * 100)}%
                    </span>
                  </div>
                  <Bar pct={s.weight * 100} />
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Check size (per stage)">
          {data.check_sizes.length === 0 ? (
            <p className="text-sm text-muted">Not available for this source.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left font-mono text-[10px] uppercase tracking-wider text-faint">
                  <th className="pb-2 font-medium">Stage</th>
                  <th className="pb-2 font-medium">Min</th>
                  <th className="pb-2 font-medium">Median</th>
                  <th className="pb-2 font-medium">Max</th>
                  <th className="pb-2 font-medium">#</th>
                </tr>
              </thead>
              <tbody className="font-mono tabular-nums">
                {data.check_sizes.map((c) => (
                  <tr key={c.stage_slug} className="border-t border-line">
                    <td className="py-1.5 font-sans text-ink">{c.stage_slug.replace(/_/g, " ")}</td>
                    <td className="py-1.5 text-muted">{money(c.min_amount)}</td>
                    <td className="py-1.5 text-muted">{money(c.median_amount)}</td>
                    <td className="py-1.5 text-muted">{money(c.max_amount)}</td>
                    <td className="py-1.5 text-faint">{c.deal_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card title="Identity">
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="font-mono text-[11px] uppercase tracking-wider text-faint">AUM</dt>
            <dd className="font-mono tabular-nums text-ink">{money(f.aum)}</dd>
            <dt className="font-mono text-[11px] uppercase tracking-wider text-faint">Dry powder</dt>
            <dd className="font-mono tabular-nums text-ink">{money(f.dry_powder)}</dd>
            <dt className="font-mono text-[11px] uppercase tracking-wider text-faint">GPs</dt>
            <dd className="font-mono tabular-nums text-ink">{f.gp_count ?? "—"}</dd>
            <dt className="font-mono text-[11px] uppercase tracking-wider text-faint">Website</dt>
            <dd className="truncate text-ink">{f.website || "—"}</dd>
          </dl>
        </Card>
      </div>

      <Card title="Partners & verified contacts">
        {data.partners.length === 0 ? (
          <p className="text-sm text-muted">
            No partner/contact data for this source. Verified partner contacts are the LakeB2B
            layer — demonstrated on the seeded dataset.
          </p>
        ) : (
          <div className="space-y-3">
            {data.partners.map((p, i) => (
              <div key={i} className="rounded-lg border border-line p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-ink">{p.name}</span>{" "}
                    <span className="text-xs text-muted">{p.title}</span>
                  </div>
                  <Badge
                    color={
                      p.role_currency_status === "current"
                        ? "green"
                        : p.role_currency_status === "stale"
                          ? "amber"
                          : "slate"
                    }
                  >
                    role {p.role_currency_status}
                  </Badge>
                </div>
                <ul className="mt-2 space-y-1">
                  {p.contacts.map((c, j) => {
                    const vb = verifiedBadge(c.verified_state);
                    return (
                      <li key={j} className="flex items-center gap-2 text-sm">
                        <span className="font-mono text-xs text-faint">{c.kind}</span>
                        <span className="text-ink">{c.value}</span>
                        <Badge color={vb.color}>{vb.label}</Badge>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        )}
      </Card>

      {data.recent_deals && data.recent_deals.length > 0 && (
        <Card
          title={`Recent deals${data.deal_count ? ` · ${data.deal_count.toLocaleString()} total` : ""}`}
        >
          <ul className="divide-y divide-line">
            {data.recent_deals.map((d, i) => (
              <li key={i} className="flex items-center gap-3 py-2 text-sm">
                <span className="w-24 shrink-0 font-mono text-xs tabular-nums text-faint">
                  {d.announced_at}
                </span>
                <Badge color="slate">{d.stage_slug.replace(/_/g, " ")}</Badge>
                <Badge color={d.is_new ? "blue" : "slate"}>{d.is_new ? "new" : "follow-on"}</Badge>
                <span className="truncate text-ink">{d.company}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
