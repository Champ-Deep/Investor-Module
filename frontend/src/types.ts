export interface QueryFilters {
  investor_types: string[];
  capital_roles: string[];
  hq_countries: string[];
  mandate_geos: string[];
  lp_base_geos: string[];
  stages: string[];
  check_min: number | null;
  check_max: number | null;
  new_only: boolean;
  lead_only: boolean;
  led_within_months: number | null;
  gp_count_max: number | null;
  aum_min: number | null;
  aum_max: number | null;
  dry_powder_min: number | null;
  fund_size_min: number | null;
  fund_size_max: number | null;
  min_new_deals_window: number | null;
  thesis_tags: string[];
  acq_buyer_kind: string | null;
  acq_platform: boolean;
  ebitda_min: number | null;
  ebitda_max: number | null;
  acq_sector: string | null;
  acq_min_count: number | null;
  acq_within_months: number | null;
  ev_min: number | null;
  ev_max: number | null;
  asset_class: string | null;
  allocation_min_pct: number | null;
  committed_within_months: number | null;
  committed_first_time_only: boolean;
  require_verified_contact: boolean;
  include_inactive: boolean;
  soft_sectors: string[];
  soft_text: string | null;
}

export function emptyFilters(): QueryFilters {
  return {
    investor_types: [], capital_roles: [], hq_countries: [], mandate_geos: [], lp_base_geos: [],
    stages: [], check_min: null, check_max: null, new_only: true, lead_only: false,
    led_within_months: null, gp_count_max: null, aum_min: null, aum_max: null, dry_powder_min: null,
    fund_size_min: null, fund_size_max: null, min_new_deals_window: null, thesis_tags: [],
    acq_buyer_kind: null, acq_platform: false, ebitda_min: null, ebitda_max: null, acq_sector: null,
    acq_min_count: null, acq_within_months: null, ev_min: null, ev_max: null, asset_class: null,
    allocation_min_pct: null, committed_within_months: null, committed_first_time_only: false,
    require_verified_contact: false, include_inactive: false, soft_sectors: [], soft_text: null,
  };
}

export interface SearchFirm {
  id: string;
  slug: string;
  name: string;
  investor_type: string;
  hq_country: string | null;
  is_active: boolean;
  cadence_score: number | null;
  rank_score: number | null;
  top_sectors?: string[];
  deal_count?: number;
}

export interface FirmDeal {
  company: string;
  stage_slug: string;
  is_new: boolean;
  is_lead: boolean;
  announced_at: string;
}

export interface SearchResponse {
  count: number;
  firms: SearchFirm[];
}

export interface ParsedQuery {
  filters: QueryFilters;
  explanation: string;
}

export interface CadenceFactor {
  feature: string;
  value: number;
  weight: number;
  contribution: number;
}

export interface Cadence {
  score: number;
  model_version: string;
  readiness_hit_rate: number | null;
  top_factors: CadenceFactor[];
}

export interface Contact {
  kind: string;
  value: string;
  deliverability_status: string;
  deliverability_checked_at: string | null;
  verified_state: string;
}

export interface Partner {
  name: string;
  title: string | null;
  location: string | null;
  role_currency_status: string;
  role_currency_checked_at: string | null;
  contacts: Contact[];
}

export interface FirmProfile {
  firm: Record<string, unknown> & {
    slug: string;
    name: string;
    investor_type: string;
    hq_country: string | null;
    website: string | null;
    aum: number | null;
    dry_powder: number | null;
    gp_count: number | null;
    description: string | null;
  };
  roles: string[];
  is_active: boolean;
  cadence: Cadence | null;
  sector_profile: { slug: string; name: string; weight: number }[];
  check_sizes: {
    stage_slug: string;
    min_amount: number | null;
    median_amount: number | null;
    max_amount: number | null;
    deal_count: number;
  }[];
  partners: Partner[];
  recent_deals: FirmDeal[];
  deal_count?: number;
}

export interface Freshness {
  sla_days: number;
  email_deliverability: Record<string, number>;
  role_currency: Record<string, number>;
  firms_with_verified_contact: number;
  total_firms: number;
  verified_coverage_pct: number;
}
