import type { QueryFilters } from "../../types";

const ROLES = ["direct_investor", "lp_allocator", "strategic_acquirer"];
const STAGES = [
  "pre_seed", "seed", "series_a", "series_b", "series_c",
  "series_d_plus", "growth", "late_stage", "public",
];

const inputCls = "mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm";
const labelCls = "text-xs font-medium text-slate-500";

function CsvField(props: {
  label: string;
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className={labelCls}>{props.label}</span>
      <input
        className={inputCls}
        defaultValue={props.value.join(", ")}
        placeholder={props.placeholder}
        onBlur={(e) =>
          props.onChange(e.target.value.split(",").map((x) => x.trim()).filter(Boolean))
        }
      />
    </label>
  );
}

function NumField(props: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className={labelCls}>{props.label}</span>
      <input
        type="number"
        className={inputCls}
        defaultValue={props.value ?? ""}
        placeholder={props.placeholder}
        onBlur={(e) => props.onChange(e.target.value.trim() === "" ? null : Number(e.target.value))}
      />
    </label>
  );
}

function TextField(props: {
  label: string;
  value: string | null;
  onChange: (v: string | null) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className={labelCls}>{props.label}</span>
      <input
        className={inputCls}
        defaultValue={props.value ?? ""}
        placeholder={props.placeholder}
        onBlur={(e) => props.onChange(e.target.value.trim() || null)}
      />
    </label>
  );
}

function CheckField(props: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-600">
      <input type="checkbox" checked={props.value} onChange={(e) => props.onChange(e.target.checked)} />
      {props.label}
    </label>
  );
}

function MultiCheck(props: {
  label: string;
  options: string[];
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const toggle = (opt: string) =>
    props.onChange(
      props.value.includes(opt) ? props.value.filter((x) => x !== opt) : [...props.value, opt],
    );
  return (
    <div>
      <span className={labelCls}>{props.label}</span>
      <div className="mt-1 flex flex-wrap gap-1">
        {props.options.map((opt) => (
          <button
            key={opt}
            type="button"
            onClick={() => toggle(opt)}
            className={`rounded-full border px-2 py-0.5 text-xs ${
              props.value.includes(opt)
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-slate-300 text-slate-500"
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function FilterRail({
  filters,
  onChange,
}: {
  filters: QueryFilters;
  onChange: (f: QueryFilters) => void;
}) {
  const set = <K extends keyof QueryFilters>(k: K, v: QueryFilters[K]) =>
    onChange({ ...filters, [k]: v });

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <CsvField label="Investor type" value={filters.investor_types}
          onChange={(v) => set("investor_types", v)} placeholder="vc, pe, family_office" />
        <CsvField label="HQ country" value={filters.hq_countries}
          onChange={(v) => set("hq_countries", v)} placeholder="US, UK" />
        <CsvField label="Mandate geo" value={filters.mandate_geos}
          onChange={(v) => set("mandate_geos", v)} placeholder="US, EU" />
        <CsvField label="LP-base geo" value={filters.lp_base_geos}
          onChange={(v) => set("lp_base_geos", v)} placeholder="EU" />
      </div>

      <MultiCheck label="Capital role" options={ROLES} value={filters.capital_roles}
        onChange={(v) => set("capital_roles", v)} />
      <MultiCheck label="Stage" options={STAGES} value={filters.stages}
        onChange={(v) => set("stages", v)} />

      <div className="grid grid-cols-2 gap-3">
        <NumField label="Check min (USD)" value={filters.check_min}
          onChange={(v) => set("check_min", v)} placeholder="15000000" />
        <NumField label="Check max (USD)" value={filters.check_max}
          onChange={(v) => set("check_max", v)} placeholder="25000000" />
        <NumField label="Led within (months)" value={filters.led_within_months}
          onChange={(v) => set("led_within_months", v)} />
        <NumField label="GP count ≤" value={filters.gp_count_max}
          onChange={(v) => set("gp_count_max", v)} />
        <NumField label="AUM min (USD)" value={filters.aum_min}
          onChange={(v) => set("aum_min", v)} />
        <NumField label="Dry powder min (USD)" value={filters.dry_powder_min}
          onChange={(v) => set("dry_powder_min", v)} />
      </div>

      <CsvField label="Sector fit (soft — ranks, never excludes)" value={filters.soft_sectors}
        onChange={(v) => set("soft_sectors", v)} placeholder="vertical-saas, climate-tech" />
      <CsvField label="Thesis tags" value={filters.thesis_tags}
        onChange={(v) => set("thesis_tags", v)} placeholder="b2b, full-buyout" />

      <div className="flex flex-wrap gap-4">
        <CheckField label="Lead deals only" value={filters.lead_only}
          onChange={(v) => set("lead_only", v)} />
        <CheckField label="New deals only" value={filters.new_only}
          onChange={(v) => set("new_only", v)} />
        <CheckField label="Verified contact" value={filters.require_verified_contact}
          onChange={(v) => set("require_verified_contact", v)} />
        <CheckField label="Include inactive" value={filters.include_inactive}
          onChange={(v) => set("include_inactive", v)} />
      </div>

      <details className="rounded-lg border border-slate-200 p-3">
        <summary className="cursor-pointer text-xs font-semibold text-slate-600">
          Advanced — acquirer &amp; LP predicates
        </summary>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <TextField label="Acq. buyer kind" value={filters.acq_buyer_kind}
            onChange={(v) => set("acq_buyer_kind", v)} placeholder="strategic / financial_pe" />
          <TextField label="Acq. sector" value={filters.acq_sector}
            onChange={(v) => set("acq_sector", v)} placeholder="cybersecurity" />
          <NumField label="Acq. min count" value={filters.acq_min_count}
            onChange={(v) => set("acq_min_count", v)} />
          <NumField label="Acq. within (months)" value={filters.acq_within_months}
            onChange={(v) => set("acq_within_months", v)} />
          <NumField label="EV min (USD)" value={filters.ev_min}
            onChange={(v) => set("ev_min", v)} />
          <NumField label="EV max (USD)" value={filters.ev_max}
            onChange={(v) => set("ev_max", v)} />
          <NumField label="EBITDA min (USD)" value={filters.ebitda_min}
            onChange={(v) => set("ebitda_min", v)} />
          <NumField label="EBITDA max (USD)" value={filters.ebitda_max}
            onChange={(v) => set("ebitda_max", v)} />
          <TextField label="LP asset class" value={filters.asset_class}
            onChange={(v) => set("asset_class", v)} placeholder="pe" />
          <NumField label="Allocation ≥ (%)" value={filters.allocation_min_pct}
            onChange={(v) => set("allocation_min_pct", v)} />
          <NumField label="Committed within (months)" value={filters.committed_within_months}
            onChange={(v) => set("committed_within_months", v)} />
        </div>
        <div className="mt-3 flex gap-4">
          <CheckField label="Platform appetite" value={filters.acq_platform}
            onChange={(v) => set("acq_platform", v)} />
          <CheckField label="First-time commitments only" value={filters.committed_first_time_only}
            onChange={(v) => set("committed_first_time_only", v)} />
        </div>
      </details>
    </div>
  );
}
