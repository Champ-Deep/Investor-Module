import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { Badge, Card, verifiedBadge } from "../../components/ui";
import { getFirm } from "../../lib/api";

function money(v: number | null | undefined): string {
  if (v == null) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${v.toLocaleString()}`;
}

function scoreColor(s: number): string {
  return s >= 70 ? "text-green-600" : s >= 45 ? "text-amber-600" : "text-red-600";
}

export default function FirmProfile() {
  const { slug } = useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["firm", slug],
    queryFn: () => getFirm(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (isError || !data) return <p className="text-sm text-red-600">Firm not found.</p>;
  const f = data.firm;

  return (
    <div className="space-y-4">
      <Link to="/" className="text-sm text-blue-600">
        ← Back to search
      </Link>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{f.name}</h1>
          <div className="mt-1 flex items-center gap-2 text-sm text-slate-500">
            {f.investor_type} · {f.hq_country || "—"}
            {data.is_active ? <Badge color="green">active</Badge> : <Badge>inactive</Badge>}
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {data.roles.map((r) => (
              <Badge key={r} color="blue">
                {r}
              </Badge>
            ))}
          </div>
        </div>
        {data.cadence && (
          <div className="text-right">
            <div className={`text-4xl font-bold ${scoreColor(data.cadence.score)}`}>
              {data.cadence.score}
            </div>
            <div className="text-xs text-slate-500">Investment Cadence</div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {data.cadence && (
          <Card title="Why this Cadence — top contributing factors">
            <ul className="space-y-2">
              {data.cadence.top_factors.map((fac) => (
                <li key={fac.feature}>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600">{fac.feature.replace(/_/g, " ")}</span>
                    <span className="text-slate-400">{Math.round(fac.contribution * 100)} pts</span>
                  </div>
                  <div className="h-1.5 rounded bg-slate-100">
                    <div
                      className="h-1.5 rounded bg-blue-500"
                      style={{ width: `${Math.min(100, fac.value * 100)}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-slate-400">
              {data.cadence.model_version} · predicts a NEW deal within 90 days · backtest hit-rate{" "}
              {data.cadence.readiness_hit_rate != null
                ? `${Math.round(data.cadence.readiness_hit_rate * 100)}%`
                : "n/a"}
            </p>
          </Card>
        )}

        <Card title="Behavioral sector profile">
          {data.sector_profile.length === 0 ? (
            <p className="text-sm text-slate-500">No deal-derived sectors.</p>
          ) : (
            <ul className="space-y-2">
              {data.sector_profile.map((s) => (
                <li key={s.slug}>
                  <div className="flex justify-between text-xs">
                    <span>{s.name}</span>
                    <span className="text-slate-400">{Math.round(s.weight * 100)}%</span>
                  </div>
                  <div className="h-1.5 rounded bg-slate-100">
                    <div
                      className="h-1.5 rounded bg-emerald-500"
                      style={{ width: `${Math.round(s.weight * 100)}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Check size (per stage)">
          {data.check_sizes.length === 0 ? (
            <p className="text-sm text-slate-500">No check data.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400">
                  <th>Stage</th>
                  <th>Min</th>
                  <th>Median</th>
                  <th>Max</th>
                  <th>#</th>
                </tr>
              </thead>
              <tbody>
                {data.check_sizes.map((c) => (
                  <tr key={c.stage_slug} className="border-t border-slate-100">
                    <td>{c.stage_slug}</td>
                    <td>{money(c.min_amount)}</td>
                    <td>{money(c.median_amount)}</td>
                    <td>{money(c.max_amount)}</td>
                    <td>{c.deal_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card title="Identity">
          <dl className="grid grid-cols-2 gap-y-1 text-sm">
            <dt className="text-slate-400">AUM</dt>
            <dd>{money(f.aum)}</dd>
            <dt className="text-slate-400">Dry powder</dt>
            <dd>{money(f.dry_powder)}</dd>
            <dt className="text-slate-400">GPs</dt>
            <dd>{f.gp_count ?? "—"}</dd>
            <dt className="text-slate-400">Website</dt>
            <dd className="truncate">{f.website || "—"}</dd>
          </dl>
        </Card>
      </div>

      <Card title="Partners & verified contacts">
        {data.partners.length === 0 ? (
          <p className="text-sm text-slate-500">
            No partner/contact data for this source. Verified partner contacts are the LakeB2B
            layer — demonstrated on the seeded dataset.
          </p>
        ) : (
          <div className="space-y-3">
            {data.partners.map((p, i) => (
              <div key={i} className="rounded border border-slate-100 p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{p.name}</span>{" "}
                    <span className="text-xs text-slate-500">{p.title}</span>
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
                        <span className="text-slate-500">{c.kind}:</span>
                        <span>{c.value}</span>
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
          <ul className="divide-y divide-slate-100">
            {data.recent_deals.map((d, i) => (
              <li key={i} className="flex items-center gap-2 py-1.5 text-sm">
                <span className="w-24 shrink-0 text-xs tabular-nums text-slate-400">
                  {d.announced_at}
                </span>
                <Badge color="slate">{d.stage_slug.replace(/_/g, " ")}</Badge>
                <Badge color={d.is_new ? "blue" : "slate"}>{d.is_new ? "new" : "follow-on"}</Badge>
                <span className="truncate">{d.company}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
