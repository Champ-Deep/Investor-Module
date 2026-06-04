"""Deterministic seed universe (RNG-free where it matters; fixed dates).

Builds firms/partners/funds/companies/rounds/deals/acquisitions that exercise every Tier-1 filter
and plant labelled ground-truth relevants + hard distractors for the PRD Section-17 stress queries.
Each distractor violates exactly ONE predicate, so the regression suite can prove both recall
(filters-first never drops a qualifying firm) and ranking precision.

Ground-truth keys map to PRD Section-17 queries. Values: {"relevant": [...], "distractors": [...]}
of firm slugs — except `comps_marketplaces` (target company slugs) and `conflict_check` (see notes).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from cadence.datasource.models import (
    RawAcquisition,
    RawCompany,
    RawContact,
    RawDeal,
    RawFirm,
    RawFund,
    RawLpAllocation,
    RawLpCommitment,
    RawPartner,
    RawRoleAcquirer,
    RawRoleDirect,
    RawRoleLp,
    RawRound,
)
from cadence.datasource.seed_source import SeedUniverse

TODAY = date(2026, 6, 3)
NOW = datetime(2026, 6, 3, tzinfo=timezone.utc)
FRESH = NOW - timedelta(days=20)  # inside the 90/180-day SLA
STALE = NOW - timedelta(days=420)  # outside the SLA
M = 1_000_000
B = 1_000_000_000


def months_ago(n: float) -> date:
    return TODAY - timedelta(days=round(n * 30.44))


def _email(name: str, domain: str) -> str:
    handle = name.lower().replace(" ", ".").replace("'", "")
    return f"{handle}@{domain}"


def partner(
    name: str,
    title: str,
    domain: str,
    sectors: tuple[str, ...] = (),
    stages: tuple[str, ...] = (),
    role: str = "current",
    role_fresh: bool = True,
    email_status: str = "deliverable",
    email_fresh: bool = True,
) -> RawPartner:
    return RawPartner(
        name=name,
        title=title,
        sector_lead_slugs=list(sectors),
        stage_focus=list(stages),
        role_currency_status=role,
        role_currency_checked_at=(FRESH if role_fresh else STALE) if role != "unknown" else None,
        contacts=[
            RawContact(
                kind="email",
                value=_email(name, domain),
                deliverability_status=email_status,
                deliverability_checked_at=(
                    (FRESH if email_fresh else STALE) if email_status != "unknown" else None
                ),
            )
        ],
    )


def investing_fund(
    name: str, vintage: int = 2023, size: float = 300 * M, dry: float = 120 * M
) -> RawFund:
    return RawFund(name=name, vintage_year=vintage, size=size, status="investing", dry_powder=dry)


class _Builder:
    def __init__(self) -> None:
        self.firms: list[RawFirm] = []
        self.companies: dict[str, RawCompany] = {}
        self.rounds: list[RawRound] = []
        self.deals: list[RawDeal] = []
        self.acqs: list[RawAcquisition] = []
        self.gt: dict[str, dict[str, list[str]]] = {}

    def co(
        self, slug: str, name: str, primary: list[str], secondary: list[str] | None = None
    ) -> str:
        if slug not in self.companies:
            self.companies[slug] = RawCompany(
                slug=slug,
                name=name,
                hq_country="US",
                primary_sectors=primary,
                secondary_sectors=secondary or [],
            )
        return slug

    def firm(self, **kw) -> str:
        f = RawFirm(**kw)
        self.firms.append(f)
        return f.slug

    def deal(
        self,
        firm: str,
        co: str,
        stage: str,
        amount: float | None,
        new: bool = True,
        lead: bool = True,
        months: float = 3,
        round_ref: str | None = None,
    ) -> None:
        self.deals.append(
            RawDeal(
                firm_slug=firm,
                company_slug=co,
                round_ref=round_ref,
                stage=stage,
                check_amount=amount,
                is_new=new,
                is_lead=lead,
                announced_at=months_ago(months),
            )
        )

    def round(self, ref: str, co: str, stage: str, months: float, size: float) -> None:
        self.rounds.append(
            RawRound(
                ref=ref,
                company_slug=co,
                stage=stage,
                announced_at=months_ago(months),
                round_size=size,
            )
        )

    def acq(
        self,
        acquirer: str | None,
        target: str,
        ev: float,
        mult: float | None,
        ebitda: float | None,
        advisor: str,
        kind: str | None,
        months: float,
    ) -> None:
        self.acqs.append(
            RawAcquisition(
                acquirer_firm_slug=acquirer,
                target_company_slug=target,
                ev_amount=ev,
                revenue_multiple=mult,
                ebitda_at_deal=ebitda,
                advisor=advisor,
                deal_kind=kind,
                announced_at=months_ago(months),
            )
        )

    def universe(self) -> SeedUniverse:
        return SeedUniverse(
            firms=self.firms,
            companies=list(self.companies.values()),
            rounds=self.rounds,
            deals=self.deals,
            acquisitions=self.acqs,
            ground_truth=self.gt,
        )


# --- SQ3: Series B leads in vertical SaaS, $15M-$25M check, US, led a deal in last 6 months -----
def _sq3(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(8):
        co = b.co(f"vsaas-{i}", f"VerticalSaaS Co {i}", ["vertical-saas"])
        s = f"sq3-rel-{i}"
        b.firm(
            slug=s,
            name=f"VerticalEdge Capital {i}",
            investor_type="vc",
            roles=["direct_investor"],
            hq_country="US",
            hq_region="North America",
            mandate_geos=["US"],
            gp_count=6,
            aum=400 * M,
            funds=[investing_fund(f"VerticalEdge Fund {i}")],
            role_direct=RawRoleDirect(takes_board_seat=True, co_invest_friendly=True),
            thesis_tag_slugs=["b2b", "sales-led"],
            partners=[
                partner(
                    f"Alex Verda{i}",
                    "Partner",
                    f"verticaledge{i}.vc",
                    ("vertical-saas",),
                    ("series_b",),
                )
            ],
        )
        b.deal(s, co, "series_b", 18 * M + i * M, new=True, lead=True, months=2 + i % 4)
        rel.append(s)
    co = b.co("vsaas-d", "VerticalSaaS Distractor Co", ["vertical-saas"])
    # follows, not leads
    b.firm(
        slug="sq3-dis-follow",
        name="FollowOnly VSaaS Partners",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=8,
        funds=[investing_fund("FollowOnly Fund")],
        partners=[
            partner("Fay Follow", "Partner", "followonly.vc", ("vertical-saas",), ("series_b",))
        ],
    )
    b.deal("sq3-dis-follow", co, "series_b", 20 * M, new=True, lead=False, months=3)
    dis.append("sq3-dis-follow")
    # check too large for series B
    b.firm(
        slug="sq3-dis-bigcheck",
        name="MegaCheck Growth",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=10,
        funds=[investing_fund("MegaCheck Fund")],
        partners=[partner("Bo Big", "Partner", "megacheck.vc", ("vertical-saas",), ("series_b",))],
    )
    b.deal("sq3-dis-bigcheck", co, "series_b", 45 * M, new=True, lead=True, months=3)
    dis.append("sq3-dis-bigcheck")
    # wrong stage (series A)
    b.firm(
        slug="sq3-dis-stage",
        name="SeedStage VSaaS",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=5,
        funds=[investing_fund("SeedStage Fund")],
        partners=[
            partner("Sam Seed", "Partner", "seedstage.vc", ("vertical-saas",), ("series_a",))
        ],
    )
    b.deal("sq3-dis-stage", co, "series_a", 20 * M, new=True, lead=True, months=3)
    dis.append("sq3-dis-stage")
    # wrong sector (horizontal SaaS)
    hco = b.co("hsaas-d", "HorizontalSaaS Co", ["horizontal-saas"])
    b.firm(
        slug="sq3-dis-sector",
        name="Horizontal Partners",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=7,
        funds=[investing_fund("Horizontal Fund")],
        partners=[
            partner("Hera Horiz", "Partner", "horizontal.vc", ("horizontal-saas",), ("series_b",))
        ],
    )
    b.deal("sq3-dis-sector", hco, "series_b", 20 * M, new=True, lead=True, months=3)
    dis.append("sq3-dis-sector")
    # non-US HQ + mandate
    b.firm(
        slug="sq3-dis-geo",
        name="EuroVertical Capital",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="DE",
        hq_region="Europe",
        mandate_geos=["EU"],
        gp_count=6,
        funds=[investing_fund("EuroVertical Fund")],
        partners=[
            partner("Erik Euro", "Partner", "eurovertical.vc", ("vertical-saas",), ("series_b",))
        ],
    )
    b.deal("sq3-dis-geo", co, "series_b", 20 * M, new=True, lead=True, months=3)
    dis.append("sq3-dis-geo")
    # led but 14 months ago (not last 6 months)
    b.firm(
        slug="sq3-dis-stale",
        name="Dormant Vertical",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=6,
        funds=[investing_fund("Dormant Fund")],
        partners=[partner("Dot Dorm", "Partner", "dormant.vc", ("vertical-saas",), ("series_b",))],
    )
    b.deal("sq3-dis-stale", co, "series_b", 20 * M, new=True, lead=True, months=14)
    dis.append("sq3-dis-stale")
    b.gt["raise_vsaas_b"] = {"relevant": rel, "distractors": dis}


# --- SQ4: Climate-tech growth, European LP base, $25M-$50M Series C checks --------------------
def _sq4(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(6):
        co = b.co(f"climate-{i}", f"Climate Co {i}", ["climate-tech"])
        s = f"sq4-rel-{i}"
        b.firm(
            slug=s,
            name=f"GreenGrowth Partners {i}",
            investor_type="growth_equity",
            roles=["direct_investor"],
            hq_country="US",
            mandate_geos=["US", "EU"],
            lp_base_geos=["EU"],
            gp_count=12,
            aum=2 * B,
            funds=[investing_fund(f"GreenGrowth Fund {i}", size=1 * B, dry=400 * M)],
            role_direct=RawRoleDirect(takes_board_seat=True, co_invest_friendly=True),
            partners=[
                partner(
                    f"Gail Green{i}",
                    "Partner",
                    f"greengrowth{i}.vc",
                    ("climate-tech",),
                    ("series_c",),
                )
            ],
        )
        b.deal(s, co, "series_c", 30 * M + i * 2 * M, new=True, lead=True, months=4 + i)
        rel.append(s)
    co = b.co("climate-d", "Climate Distractor Co", ["climate-tech"])
    # US LP base (not European)
    b.firm(
        slug="sq4-dis-uslp",
        name="USOnly Climate Growth",
        investor_type="growth_equity",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        lp_base_geos=["US"],
        gp_count=10,
        aum=1 * B,
        funds=[investing_fund("USOnly Fund")],
        partners=[partner("Uma US", "Partner", "usonly.vc", ("climate-tech",), ("series_c",))],
    )
    b.deal("sq4-dis-uslp", co, "series_c", 30 * M, new=True, lead=True, months=4)
    dis.append("sq4-dis-uslp")
    # check too small
    b.firm(
        slug="sq4-dis-smallcheck",
        name="SmallCheck Climate",
        investor_type="growth_equity",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["EU"],
        lp_base_geos=["EU"],
        gp_count=8,
        funds=[investing_fund("SmallCheck Fund")],
        partners=[
            partner("Tim Tiny", "Partner", "smallcheck.vc", ("climate-tech",), ("series_c",))
        ],
    )
    b.deal("sq4-dis-smallcheck", co, "series_c", 8 * M, new=True, lead=True, months=4)
    dis.append("sq4-dis-smallcheck")
    # wrong sector
    fco = b.co("fin-d4", "Fin Distractor Co", ["payments"])
    b.firm(
        slug="sq4-dis-sector",
        name="FinGrowth EU",
        investor_type="growth_equity",
        roles=["direct_investor"],
        hq_country="UK",
        mandate_geos=["EU"],
        lp_base_geos=["EU"],
        gp_count=9,
        funds=[investing_fund("FinGrowth Fund")],
        partners=[partner("Fred Fin", "Partner", "fingrowth.vc", ("payments",), ("series_c",))],
    )
    b.deal("sq4-dis-sector", fco, "series_c", 30 * M, new=True, lead=True, months=4)
    dis.append("sq4-dis-sector")
    b.gt["raise_climate_growth"] = {"relevant": rel, "distractors": dis}


# --- SQ5: Solo capitalists / small partner-led funds (<=3 GPs), pre-seed AI infrastructure, US ---
def _sq5(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(7):
        co = b.co(f"aiinfra-{i}", f"AI Infra Co {i}", ["ai-infrastructure"])
        s = f"sq5-rel-{i}"
        itype = "solo_gp" if i % 2 == 0 else "vc"
        b.firm(
            slug=s,
            name=f"Atom Capital {i}",
            investor_type=itype,
            roles=["direct_investor"],
            hq_country="US",
            mandate_geos=["US"],
            gp_count=1 + (i % 3),
            funds=[investing_fund(f"Atom Fund {i}", size=30 * M, dry=15 * M)],
            partners=[
                partner(
                    f"Ada Atom{i}",
                    "General Partner",
                    f"atom{i}.vc",
                    ("ai-infrastructure",),
                    ("pre_seed",),
                )
            ],
        )
        b.deal(s, co, "pre_seed", 0.5 * M + i * 0.1 * M, new=True, lead=True, months=3 + i)
        rel.append(s)
    co = b.co("aiinfra-d", "AI Infra Distractor Co", ["ai-infrastructure"])
    # large fund (10 GPs)
    b.firm(
        slug="sq5-dis-bigfund",
        name="Megafund Ventures",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=14,
        funds=[investing_fund("Megafund X", size=2 * B)],
        partners=[
            partner("Max Mega", "Partner", "megafund.vc", ("ai-infrastructure",), ("pre_seed",))
        ],
    )
    b.deal("sq5-dis-bigfund", co, "pre_seed", 0.6 * M, new=True, lead=True, months=3)
    dis.append("sq5-dis-bigfund")
    # not AI infra (applied-ai)
    aco = b.co("appliedai-d", "Applied AI Co", ["applied-ai"])
    b.firm(
        slug="sq5-dis-sector",
        name="AppliedSolo",
        investor_type="solo_gp",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=1,
        funds=[investing_fund("AppliedSolo Fund", size=20 * M)],
        partners=[partner("Ann Applied", "GP", "appliedsolo.vc", ("applied-ai",), ("pre_seed",))],
    )
    b.deal("sq5-dis-sector", aco, "pre_seed", 0.5 * M, new=True, lead=True, months=3)
    dis.append("sq5-dis-sector")
    # not US
    b.firm(
        slug="sq5-dis-geo",
        name="London Angel Solo",
        investor_type="solo_gp",
        roles=["direct_investor"],
        hq_country="UK",
        mandate_geos=["UK"],
        gp_count=1,
        funds=[investing_fund("London Solo Fund", size=15 * M)],
        partners=[
            partner("Liv London", "GP", "londonsolo.vc", ("ai-infrastructure",), ("pre_seed",))
        ],
    )
    b.deal("sq5-dis-geo", co, "pre_seed", 0.5 * M, new=True, lead=True, months=3)
    dis.append("sq5-dis-geo")
    # wrong stage (series_a)
    b.firm(
        slug="sq5-dis-stage",
        name="GrowthSolo",
        investor_type="solo_gp",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=2,
        funds=[investing_fund("GrowthSolo Fund", size=40 * M)],
        partners=[
            partner("Gus Growth", "GP", "growthsolo.vc", ("ai-infrastructure",), ("series_a",))
        ],
    )
    b.deal("sq5-dis-stage", co, "series_a", 5 * M, new=True, lead=True, months=3)
    dis.append("sq5-dis-stage")
    b.gt["raise_solo_preseed_ai"] = {"relevant": rel, "distractors": dis}


# --- SQ1: Strategic acquirers in US cybersecurity, >=2 acquisitions in last 24mo, $50M-$300M EV --
def _sq1(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(6):
        s = f"sq1-rel-{i}"
        b.firm(
            slug=s,
            name=f"CyberCorp {i}",
            investor_type="corporate_venture",
            roles=["strategic_acquirer"],
            hq_country="US",
            mandate_geos=["US"],
            role_acquirer=RawRoleAcquirer(buyer_kind="strategic", platform_or_addon="both"),
            partners=[
                partner(
                    f"Cory Cyber{i}", "Head of Corp Dev", f"cybercorp{i}.com", ("cybersecurity",)
                )
            ],
        )
        for j in range(2):
            tco = b.co(f"cyber-target-{i}-{j}", f"Cyber Target {i}-{j}", ["cybersecurity"])
            b.acq(
                s,
                tco,
                ev=(80 + i * 20 + j * 10) * M,
                mult=6.0,
                ebitda=12 * M,
                advisor="Goldman",
                kind="addon",
                months=6 + j * 6,
            )
        rel.append(s)
    # only 1 acquisition
    tco = b.co("cyber-target-d0", "Cyber Target D0", ["cybersecurity"])
    b.firm(
        slug="sq1-dis-one",
        name="OneShot Security",
        investor_type="corporate_venture",
        roles=["strategic_acquirer"],
        hq_country="US",
        mandate_geos=["US"],
        role_acquirer=RawRoleAcquirer(buyer_kind="strategic"),
        partners=[partner("Ole One", "Corp Dev", "oneshot.com", ("cybersecurity",))],
    )
    b.acq(
        "sq1-dis-one",
        tco,
        ev=120 * M,
        mult=5.0,
        ebitda=10 * M,
        advisor="Evercore",
        kind="addon",
        months=6,
    )
    dis.append("sq1-dis-one")
    # EV too high
    b.firm(
        slug="sq1-dis-ev",
        name="BigEV Security",
        investor_type="corporate_venture",
        roles=["strategic_acquirer"],
        hq_country="US",
        mandate_geos=["US"],
        role_acquirer=RawRoleAcquirer(buyer_kind="strategic"),
        partners=[partner("Eve EV", "Corp Dev", "bigev.com", ("cybersecurity",))],
    )
    for j in range(2):
        tco = b.co(f"cyber-target-ev-{j}", f"Cyber Big {j}", ["cybersecurity"])
        b.acq(
            "sq1-dis-ev",
            tco,
            ev=600 * M,
            mult=8.0,
            ebitda=40 * M,
            advisor="JPM",
            kind="platform",
            months=8,
        )
    dis.append("sq1-dis-ev")
    # not cybersecurity
    b.firm(
        slug="sq1-dis-sector",
        name="Fintech Acquirer",
        investor_type="corporate_venture",
        roles=["strategic_acquirer"],
        hq_country="US",
        mandate_geos=["US"],
        role_acquirer=RawRoleAcquirer(buyer_kind="strategic"),
        partners=[partner("Phil Fin", "Corp Dev", "fintechacq.com", ("payments",))],
    )
    for j in range(2):
        tco = b.co(f"fin-target-{j}", f"Fin Target {j}", ["payments"])
        b.acq(
            "sq1-dis-sector",
            tco,
            ev=150 * M,
            mult=5.0,
            ebitda=15 * M,
            advisor="Lazard",
            kind="addon",
            months=7,
        )
    dis.append("sq1-dis-sector")
    # acquisitions too old (>24 months)
    b.firm(
        slug="sq1-dis-old",
        name="Stale Security Buyer",
        investor_type="corporate_venture",
        roles=["strategic_acquirer"],
        hq_country="US",
        mandate_geos=["US"],
        role_acquirer=RawRoleAcquirer(buyer_kind="strategic"),
        partners=[partner("Stan Stale", "Corp Dev", "stalesec.com", ("cybersecurity",))],
    )
    for j in range(2):
        tco = b.co(f"cyber-old-{j}", f"Cyber Old {j}", ["cybersecurity"])
        b.acq(
            "sq1-dis-old",
            tco,
            ev=150 * M,
            mult=5.0,
            ebitda=15 * M,
            advisor="MS",
            kind="addon",
            months=30 + j * 4,
        )
    dis.append("sq1-dis-old")
    b.gt["sell_side_cyber"] = {"relevant": rel, "distractors": dis}


# --- SQ2: lower-mid-market PE, healthcare-services, EBITDA $5M-$15M, dry powder ---
def _sq2(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(6):
        s = f"sq2-rel-{i}"
        b.firm(
            slug=s,
            name=f"HealthBuyout Partners {i}",
            investor_type="pe",
            roles=["strategic_acquirer"],
            hq_country="US",
            mandate_geos=["US"],
            dry_powder=250 * M,
            aum=1 * B,
            funds=[investing_fund(f"HealthBuyout Fund {i}", size=800 * M, dry=250 * M)],
            role_acquirer=RawRoleAcquirer(
                buyer_kind="financial_pe",
                platform_or_addon="platform",
                ebitda_min=4 * M,
                ebitda_max=18 * M,
            ),
            thesis_tag_slugs=["full-buyout", "majority-control"],
            partners=[
                partner(
                    f"Hal Health{i}",
                    "Managing Director",
                    f"healthbuyout{i}.com",
                    ("healthcare-services",),
                )
            ],
        )
        tco = b.co(f"health-plat-{i}", f"Health Platform {i}", ["healthcare-services"])
        b.acq(
            s,
            tco,
            ev=120 * M,
            mult=2.5,
            ebitda=10 * M,
            advisor="Houlihan",
            kind="platform",
            months=8 + i,
        )
        rel.append(s)
    # EBITDA band too large (upper-market)
    b.firm(
        slug="sq2-dis-ebitda",
        name="LargeCap Health PE",
        investor_type="pe",
        roles=["strategic_acquirer"],
        hq_country="US",
        mandate_geos=["US"],
        dry_powder=2 * B,
        funds=[investing_fund("LargeCap Fund", size=5 * B, dry=2 * B)],
        role_acquirer=RawRoleAcquirer(
            buyer_kind="financial_pe",
            platform_or_addon="platform",
            ebitda_min=50 * M,
            ebitda_max=200 * M,
        ),
        partners=[partner("Lou Large", "MD", "largecap.com", ("healthcare-services",))],
    )
    tco = b.co("health-large", "Health Large Platform", ["healthcare-services"])
    b.acq(
        "sq2-dis-ebitda",
        tco,
        ev=900 * M,
        mult=4.0,
        ebitda=120 * M,
        advisor="GS",
        kind="platform",
        months=8,
    )
    dis.append("sq2-dis-ebitda")
    # no dry powder
    b.firm(
        slug="sq2-dis-nodry",
        name="Tapped Out Health PE",
        investor_type="pe",
        roles=["strategic_acquirer"],
        hq_country="US",
        mandate_geos=["US"],
        dry_powder=0,
        funds=[
            RawFund(
                name="Tapped Fund",
                vintage_year=2015,
                size=400 * M,
                status="wound_down",
                dry_powder=0,
            )
        ],
        role_acquirer=RawRoleAcquirer(
            buyer_kind="financial_pe",
            platform_or_addon="platform",
            ebitda_min=5 * M,
            ebitda_max=15 * M,
        ),
        partners=[partner("Ted Tapped", "MD", "tapped.com", ("healthcare-services",))],
    )
    tco = b.co("health-tapped", "Health Tapped Platform", ["healthcare-services"])
    b.acq(
        "sq2-dis-nodry",
        tco,
        ev=100 * M,
        mult=2.0,
        ebitda=9 * M,
        advisor="HL",
        kind="platform",
        months=10,
    )
    dis.append("sq2-dis-nodry")
    # wrong sector (industrials)
    b.firm(
        slug="sq2-dis-sector",
        name="Industrial Buyout",
        investor_type="pe",
        roles=["strategic_acquirer"],
        hq_country="US",
        mandate_geos=["US"],
        dry_powder=300 * M,
        funds=[investing_fund("Industrial Fund", size=700 * M, dry=300 * M)],
        role_acquirer=RawRoleAcquirer(
            buyer_kind="financial_pe",
            platform_or_addon="platform",
            ebitda_min=5 * M,
            ebitda_max=15 * M,
        ),
        partners=[partner("Ian Indu", "MD", "industrialbuyout.com", ("manufacturing-tech",))],
    )
    tco = b.co("indu-plat", "Industrial Platform", ["manufacturing-tech"])
    b.acq(
        "sq2-dis-sector",
        tco,
        ev=110 * M,
        mult=2.0,
        ebitda=11 * M,
        advisor="BofA",
        kind="platform",
        months=9,
    )
    dis.append("sq2-dis-sector")
    b.gt["sell_side_pe_health"] = {"relevant": rel, "distractors": dis}


# --- SQ6: pensions, PE allocation >=8%, AUM >=$20B, first-time commitment last 24mo ---
def _sq6(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(5):
        s = f"sq6-rel-{i}"
        b.firm(
            slug=s,
            name=f"State Pension {i}",
            investor_type="pension",
            roles=["lp_allocator"],
            hq_country="US",
            mandate_geos=["US", "EU"],
            aum=(25 + i * 5) * B,
            role_lp=RawRoleLp(
                ticket_min=20 * M,
                ticket_max=150 * M,
                allocations=[
                    RawLpAllocation(asset_class="pe", pct=10 + i),
                    RawLpAllocation(asset_class="public_equity", pct=50),
                ],
                commitments=[
                    RawLpCommitment(
                        target_gp_name=f"NewGP {i}",
                        first_time_fund=True,
                        amount=40 * M,
                        committed_at=months_ago(8 + i),
                    )
                ],
            ),
            partners=[partner(f"Pat Pension{i}", "Head of Private Markets", f"pension{i}.gov")],
        )
        rel.append(s)
    # PE allocation too low
    b.firm(
        slug="sq6-dis-alloc",
        name="LowPE Pension",
        investor_type="pension",
        roles=["lp_allocator"],
        hq_country="US",
        aum=30 * B,
        role_lp=RawRoleLp(
            allocations=[RawLpAllocation(asset_class="pe", pct=2)],
            commitments=[
                RawLpCommitment(
                    target_gp_name="NewGP L",
                    first_time_fund=True,
                    amount=20 * M,
                    committed_at=months_ago(6),
                )
            ],
        ),
        partners=[partner("Len Low", "CIO", "lowpe.gov")],
    )
    dis.append("sq6-dis-alloc")
    # AUM too small
    b.firm(
        slug="sq6-dis-aum",
        name="SmallFund Pension",
        investor_type="pension",
        roles=["lp_allocator"],
        hq_country="US",
        aum=5 * B,
        role_lp=RawRoleLp(
            allocations=[RawLpAllocation(asset_class="pe", pct=12)],
            commitments=[
                RawLpCommitment(
                    target_gp_name="NewGP S",
                    first_time_fund=True,
                    amount=10 * M,
                    committed_at=months_ago(6),
                )
            ],
        ),
        partners=[partner("Sue Small", "CIO", "smallpension.gov")],
    )
    dis.append("sq6-dis-aum")
    # only established-manager commitments (no first-time)
    b.firm(
        slug="sq6-dis-established",
        name="Establishment Pension",
        investor_type="pension",
        roles=["lp_allocator"],
        hq_country="US",
        aum=40 * B,
        role_lp=RawRoleLp(
            allocations=[RawLpAllocation(asset_class="pe", pct=15)],
            commitments=[
                RawLpCommitment(
                    target_gp_name="Blackstone",
                    first_time_fund=False,
                    amount=200 * M,
                    committed_at=months_ago(6),
                )
            ],
        ),
        partners=[partner("Ed Est", "CIO", "establishment.gov")],
    )
    dis.append("sq6-dis-established")
    # first-time commitment too old
    b.firm(
        slug="sq6-dis-old",
        name="Stale Pension",
        investor_type="pension",
        roles=["lp_allocator"],
        hq_country="US",
        aum=35 * B,
        role_lp=RawRoleLp(
            allocations=[RawLpAllocation(asset_class="pe", pct=11)],
            commitments=[
                RawLpCommitment(
                    target_gp_name="NewGP Old",
                    first_time_fund=True,
                    amount=30 * M,
                    committed_at=months_ago(40),
                )
            ],
        ),
        partners=[partner("Ola Old", "CIO", "stalepension.gov")],
    )
    dis.append("sq6-dis-old")
    b.gt["placement_pension_pe"] = {"relevant": rel, "distractors": dis}


# --- SQ7: Family offices with direct VC in fintech + >=1 fund commitment in 2025 -----------------
def _sq7(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(5):
        s = f"sq7-rel-{i}"
        fco = b.co(f"fintech-{i}", f"Fintech Co {i}", ["payments", "banking-infrastructure"])
        b.firm(
            slug=s,
            name=f"Heritage Family Office {i}",
            investor_type="family_office",
            roles=["direct_investor", "lp_allocator"],
            hq_country="US",
            mandate_geos=["US"],
            role_direct=RawRoleDirect(takes_board_seat=False, co_invest_friendly=True),
            role_lp=RawRoleLp(
                commitments=[
                    RawLpCommitment(
                        target_gp_name=f"VC Fund {i}",
                        first_time_fund=False,
                        amount=15 * M,
                        committed_at=date(2025, 3 + i % 6, 10),
                    )
                ]
            ),
            funds=[investing_fund(f"Heritage Direct {i}", size=200 * M, dry=80 * M)],
            partners=[partner(f"Fin Family{i}", "Principal", f"heritage{i}.com", ("payments",))],
        )
        b.deal(s, fco, "series_a", 5 * M, new=True, lead=False, months=5 + i)
        rel.append(s)
    # family office but no direct fintech deals (LP only)
    b.firm(
        slug="sq7-dis-lponly",
        name="PassiveFO",
        investor_type="family_office",
        roles=["lp_allocator"],
        hq_country="US",
        role_lp=RawRoleLp(
            commitments=[
                RawLpCommitment(
                    target_gp_name="VC Fund P",
                    first_time_fund=False,
                    amount=10 * M,
                    committed_at=date(2025, 5, 1),
                )
            ]
        ),
        partners=[partner("Pam Passive", "Principal", "passivefo.com")],
    )
    dis.append("sq7-dis-lponly")
    # direct fintech but no 2025 commitment
    fco = b.co("fintech-d", "Fintech D Co", ["payments"])
    b.firm(
        slug="sq7-dis-nocommit",
        name="NoCommit FO",
        investor_type="family_office",
        roles=["direct_investor", "lp_allocator"],
        hq_country="US",
        role_lp=RawRoleLp(
            commitments=[
                RawLpCommitment(
                    target_gp_name="VC Fund N",
                    first_time_fund=False,
                    amount=10 * M,
                    committed_at=date(2023, 6, 1),
                )
            ]
        ),
        funds=[investing_fund("NoCommit Direct", size=150 * M)],
        partners=[partner("Nina No", "Principal", "nocommit.com", ("payments",))],
    )
    b.deal("sq7-dis-nocommit", fco, "series_a", 4 * M, new=True, lead=False, months=6)
    dis.append("sq7-dis-nocommit")
    # not a family office (a VC)
    b.firm(
        slug="sq7-dis-type",
        name="PlainVC Fintech",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        funds=[investing_fund("PlainVC Fund")],
        partners=[partner("Vic VC", "Partner", "plainvc.vc", ("payments",))],
    )
    b.deal("sq7-dis-type", fco, "series_a", 5 * M, new=True, lead=True, months=4)
    dis.append("sq7-dis-type")
    b.gt["placement_fo_fintech"] = {"relevant": rel, "distractors": dis}


# --- SQ8: VCs who co-invested with Lightspeed in healthtech in last 3 years ----------------------
def _sq8(b: _Builder) -> None:
    rel, dis = [], []
    # Lightspeed itself (the named lead in the query).
    b.firm(
        slug="lightspeed",
        name="Lightspeed Venture Partners",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        mandate_geos=["US"],
        gp_count=20,
        funds=[investing_fund("Lightspeed Fund", size=2 * B)],
        partners=[
            partner("Lee Speed", "Partner", "lightspeed.vc", ("digital-health",), ("series_a",))
        ],
    )
    for i in range(5):
        hco = b.co(f"healthco-{i}", f"HealthTech Co {i}", ["digital-health"])
        ref = f"round-h-{i}"
        b.round(ref, hco, "series_a", months=10 + i, size=40 * M)
        b.deal(
            "lightspeed", hco, "series_a", 15 * M, new=True, lead=True, months=10 + i, round_ref=ref
        )
        s = f"sq8-rel-{i}"
        b.firm(
            slug=s,
            name=f"CoInvest Health VC {i}",
            investor_type="vc",
            roles=["direct_investor"],
            hq_country="US",
            mandate_geos=["US"],
            gp_count=8,
            funds=[investing_fund(f"CoInvest Fund {i}")],
            partners=[
                partner(
                    f"Cole Co{i}", "Partner", f"coinvest{i}.vc", ("digital-health",), ("series_a",)
                )
            ],
        )
        b.deal(s, hco, "series_a", 8 * M, new=True, lead=False, months=10 + i, round_ref=ref)
        rel.append(s)
    # co-invested with Lightspeed but in fintech (not healthtech)
    fco = b.co("ls-fintech", "LS Fintech Co", ["payments"])
    b.round("round-f", fco, "series_a", months=12, size=30 * M)
    b.deal(
        "lightspeed", fco, "series_a", 10 * M, new=True, lead=True, months=12, round_ref="round-f"
    )
    b.firm(
        slug="sq8-dis-sector",
        name="FintechCo VC",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        funds=[investing_fund("FintechCo Fund")],
        partners=[partner("Finn Co", "Partner", "fintechco.vc", ("payments",), ("series_a",))],
    )
    b.deal(
        "sq8-dis-sector",
        fco,
        "series_a",
        6 * M,
        new=True,
        lead=False,
        months=12,
        round_ref="round-f",
    )
    dis.append("sq8-dis-sector")
    # healthtech co-investor but NOT with Lightspeed (different round)
    hco = b.co("health-solo", "Health Solo Co", ["digital-health"])
    b.round("round-h-solo", hco, "series_a", months=9, size=25 * M)
    b.firm(
        slug="sq8-dis-notlightspeed",
        name="OtherLead Health VC",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        funds=[investing_fund("OtherLead Fund")],
        partners=[
            partner("Otto Other", "Partner", "otherlead.vc", ("digital-health",), ("series_a",))
        ],
    )
    b.deal(
        "sq8-dis-notlightspeed",
        hco,
        "series_a",
        9 * M,
        new=True,
        lead=True,
        months=9,
        round_ref="round-h-solo",
    )
    dis.append("sq8-dis-notlightspeed")
    # co-invested with Lightspeed in healthtech but >3 years ago
    hco = b.co("health-old", "Health Old Co", ["digital-health"])
    b.round("round-h-old", hco, "series_a", months=48, size=30 * M)
    b.deal(
        "lightspeed",
        hco,
        "series_a",
        12 * M,
        new=True,
        lead=True,
        months=48,
        round_ref="round-h-old",
    )
    b.firm(
        slug="sq8-dis-old",
        name="Ancient CoInvest VC",
        investor_type="vc",
        roles=["direct_investor"],
        hq_country="US",
        funds=[investing_fund("Ancient Fund")],
        partners=[
            partner("Andy Ancient", "Partner", "ancient.vc", ("digital-health",), ("series_a",))
        ],
    )
    b.deal(
        "sq8-dis-old",
        hco,
        "series_a",
        7 * M,
        new=True,
        lead=False,
        months=48,
        round_ref="round-h-old",
    )
    dis.append("sq8-dis-old")
    b.gt["warm_intro_lightspeed"] = {"relevant": rel, "distractors": dis}


# --- SQ9: Last N acquisitions in marketplaces, $100M-$500M EV (comps; returns acquisitions) -------
def _sq9(b: _Builder) -> None:
    rel, dis = [], []
    for i in range(10):
        tco = b.co(f"mkt-target-{i}", f"Marketplace Target {i}", ["marketplaces"])
        b.acq(
            None,
            tco,
            ev=(120 + i * 30) * M,
            mult=4.0 + i * 0.2,
            ebitda=20 * M,
            advisor=["Qatalyst", "GS", "MS"][i % 3],
            kind=None,
            months=2 + i,
        )
        rel.append(tco)
    # EV out of range (too small)
    tco = b.co("mkt-small", "Marketplace Small", ["marketplaces"])
    b.acq(None, tco, ev=40 * M, mult=3.0, ebitda=8 * M, advisor="Lazard", kind=None, months=3)
    dis.append(tco)
    # not a marketplace
    tco = b.co("saas-comp", "SaaS Comp Target", ["horizontal-saas"])
    b.acq(None, tco, ev=200 * M, mult=6.0, ebitda=15 * M, advisor="Evercore", kind=None, months=3)
    dis.append(tco)
    b.gt["comps_marketplaces"] = {"relevant": rel, "distractors": dis}


# --- SQ10: Conflict check — which target investors back any named competitor --------------------
def _sq10(b: _Builder) -> None:
    competitors = [b.co(f"competitor-{i}", f"Competitor {i}", ["marketplaces"]) for i in range(3)]
    targets, conflicted = [], []
    for i in range(6):
        s = f"sq10-target-{i}"
        b.firm(
            slug=s,
            name=f"Target Investor {i}",
            investor_type="vc",
            roles=["direct_investor"],
            hq_country="US",
            funds=[investing_fund(f"Target Fund {i}")],
            partners=[partner(f"Tom Target{i}", "Partner", f"target{i}.vc", ("marketplaces",))],
        )
        targets.append(s)
        if i % 2 == 0:  # half back a competitor
            b.deal(s, competitors[i % 3], "series_b", 10 * M, new=True, lead=False, months=6)
            conflicted.append(s)
        else:
            clean = b.co(f"clean-co-{i}", f"Clean Co {i}", ["marketplaces"])
            b.deal(s, clean, "series_b", 10 * M, new=True, lead=False, months=6)
    # inputs (targets, competitors) recorded alongside the expected conflicted set.
    b.gt["conflict_check"] = {
        "relevant": conflicted,
        "distractors": [t for t in targets if t not in conflicted],
        "targets": targets,
        "competitors": competitors,
    }


# --- Background population: variety across types/roles/states, active and inactive ---------------
def _background(b: _Builder) -> None:
    types = [
        "vc",
        "angel",
        "pe",
        "growth_equity",
        "family_office",
        "corporate_venture",
        "sovereign_wealth",
        "endowment",
        "fund_of_funds",
        "accelerator",
    ]
    sectors = [
        "fintech",
        "ai-infrastructure",
        "marketplaces",
        "cybersecurity",
        "digital-health",
        "climate-tech",
        "vertical-saas",
        "gaming",
        "proptech",
        "edtech",
    ]
    for i in range(30):
        s = f"bg-{i}"
        t = types[i % len(types)]
        sec = sectors[i % len(sectors)]
        # sec may be a group slug ("fintech"); tag company with a concrete leaf where needed.
        leaf = {"fintech": "payments"}.get(sec, sec)
        co = b.co(f"bg-co-{i}", f"Background Co {i}", [leaf])
        wound = i % 7 == 0  # some wound-down/inactive firms to test the Active-Firm gate
        fund = (
            RawFund(
                name=f"BG Fund {i}",
                vintage_year=2014,
                size=200 * M,
                status="wound_down",
                dry_powder=0,
            )
            if wound
            else investing_fund(f"BG Fund {i}")
        )
        # mix verification states across background partners
        email_status = ["deliverable", "catch_all", "undeliverable", "unknown"][i % 4]
        role_state = ["current", "stale", "current", "unknown"][i % 4]
        b.firm(
            slug=s,
            name=f"Background Capital {i}",
            investor_type=t,
            roles=["direct_investor"],
            hq_country=["US", "UK", "DE", "SG"][i % 4],
            mandate_geos=[["US", "UK", "EU", "APAC"][i % 4]],
            gp_count=3 + i % 12,
            aum=(i + 1) * 100 * M,
            dry_powder=(i % 5) * 50 * M,
            funds=[fund],
            partners=[
                partner(
                    f"BG Person {i}",
                    "Partner",
                    f"bg{i}.vc",
                    (leaf,),
                    ("seed", "series_a"),
                    role=role_state,
                    email_status=email_status,
                )
            ],
        )
        # inactive firms get only an old deal; active ones a recent deal
        b.deal(
            s,
            co,
            "series_a",
            (2 + i % 8) * M,
            new=True,
            lead=(i % 2 == 0),
            months=40 if wound else (2 + i % 10),
        )


def build_universe() -> SeedUniverse:
    b = _Builder()
    _sq3(b)
    _sq4(b)
    _sq5(b)
    _sq1(b)
    _sq2(b)
    _sq6(b)
    _sq7(b)
    _sq8(b)
    _sq9(b)
    _sq10(b)
    _background(b)
    return b.universe()
