import { useQuery } from "@tanstack/react-query";

import { Card } from "../../components/ui";
import { getFreshness } from "../../lib/api";

function Bucket({ total, w90, w180 }: { total: number; w90: number; w180: number }) {
  return (
    <div className="text-sm">
      <div>
        ≤90d: <b>{w90}</b>/{total}
      </div>
      <div>
        ≤180d: <b>{w180}</b>/{total}
      </div>
    </div>
  );
}

export default function FreshnessDashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["freshness"],
    queryFn: getFreshness,
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (isError || !data) return <p className="text-sm text-red-600">Could not load freshness.</p>;

  const ed = data.email_deliverability;
  const rc = data.role_currency;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Freshness &amp; SLA</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card title="Verified coverage">
          <div className="text-3xl font-bold text-blue-600">{data.verified_coverage_pct}%</div>
          <p className="mt-1 text-xs text-slate-500">
            {data.firms_with_verified_contact}/{data.total_firms} firms with a Verified contact
            inside the {data.sla_days}-day SLA
          </p>
        </Card>
        <Card title="Email deliverability">
          <Bucket total={ed.total} w90={ed.within_90} w180={ed.within_180} />
          <p className="mt-2 text-xs text-red-600">
            {ed.catch_all} catch-all (flagged, never counted as a pass)
          </p>
        </Card>
        <Card title="Role currency">
          <Bucket total={rc.total} w90={rc.within_90} w180={rc.within_180} />
        </Card>
      </div>
      <p className="text-xs text-slate-400">
        SLA: 90 days premium tier, 180 days standard tier. Verified = deliverability AND role
        currency, both inside SLA (ADR 0002).
      </p>
    </div>
  );
}
