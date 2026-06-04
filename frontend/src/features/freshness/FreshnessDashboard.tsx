import { useQuery } from "@tanstack/react-query";

import { Card } from "../../components/ui";
import { getFreshness } from "../../lib/api";

function Bucket({ total, w90, w180 }: { total: number; w90: number; w180: number }) {
  return (
    <div className="font-mono text-sm tabular-nums text-muted">
      <div>
        ≤90d: <b className="text-ink">{w90}</b>/{total}
      </div>
      <div>
        ≤180d: <b className="text-ink">{w180}</b>/{total}
      </div>
    </div>
  );
}

export default function FreshnessDashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["freshness"],
    queryFn: getFreshness,
  });

  if (isLoading) return <p className="text-sm text-muted">Loading…</p>;
  if (isError || !data) return <p className="text-sm text-negative">Could not load freshness.</p>;

  const ed = data.email_deliverability;
  const rc = data.role_currency;

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-medium tracking-tight text-ink">Freshness &amp; SLA</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card title="Verified coverage">
          <div className="font-mono text-4xl font-semibold tabular-nums text-ink">
            {data.verified_coverage_pct}%
          </div>
          <p className="mt-1.5 text-xs text-muted">
            {data.firms_with_verified_contact}/{data.total_firms} firms with a Verified contact
            inside the {data.sla_days}-day SLA
          </p>
        </Card>
        <Card title="Email deliverability">
          <Bucket total={ed.total} w90={ed.within_90} w180={ed.within_180} />
          <p className="mt-2 text-xs text-negative">
            {ed.catch_all} catch-all (flagged, never counted as a pass)
          </p>
        </Card>
        <Card title="Role currency">
          <Bucket total={rc.total} w90={rc.within_90} w180={rc.within_180} />
        </Card>
      </div>
      <p className="text-xs leading-relaxed text-faint">
        SLA: 90 days premium tier, 180 days standard tier. Verified = deliverability AND role
        currency, both inside SLA (ADR 0002).
      </p>
    </div>
  );
}
