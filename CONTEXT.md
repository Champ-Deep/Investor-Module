# Investor Platform (Cadence)

The investor intelligence search platform from Champions Infometrics, powered by the LakeB2B Data API. This glossary fixes the language of the product so the schema, filters, and scoring all mean the same thing. Glossary only: no implementation details, no spec content.

## Language

**Firm**:
An institutional source of capital and the atomic entity a user searches for. One result row equals one Firm. A Firm is durable: its ethos and the kinds of deals it makes change slowly.
_Avoid_: Fund (a Firm may run several funds over time), "Investor" when you mean the institution.

**Partner**:
A named decision-maker employed by a Firm and the human a user actually contacts. Partners nest inside a Firm; a Firm may have many. Each Partner carries their own sector lead, stage focus, location, and verified-contact freshness.
_Avoid_: Contact (too generic), rep, "Investor" when you mean a person.

**Investor**:
Umbrella word for any capital source. Deliberately NOT used as a search-unit term because it is ambiguous between Firm and Partner. When precision matters, say Firm or Partner.
_Avoid_: Using "Investor" as the unit of search, ranking, or export.

**Investment Cadence**:
A firm-level score (0 to 100) that is a calibrated PREDICTION of the Readiness label, not a hand-weighted composite. Weights are learned and backtested against historical outcomes using an interpretable model, so the top contributing factors stay explainable. Attaches to the Firm, never to a Partner.
_Avoid_: Attaching Cadence to a person; "activity score" as a synonym; presenting hand-set weights as a prediction.

**Readiness label**:
The observable target Cadence predicts: a Firm makes at least one NEW Deal within the next 90 days, with a sector-conditioned variant for sector queries. The score's reported accuracy is its hit-rate against this label.
_Avoid_: Claiming "readiness" with no observable target to validate against.

**Deployment Urgency**:
The capital-availability core that feeds Investment Cadence (dry powder, deployment pace, time since last check, vintage age, fund status). Firm-level.
_Avoid_: Treating it as a separate user-facing score distinct from Cadence.

**Capital role**:
A facet of a Firm describing how it deploys capital. A Firm carries one or more roles, each unlocking its own field set. The role is how the three personas filter the shared dataset.
_Avoid_: Modelling each role as a separate record or entity type.

**Direct Investor** (capital role):
A Firm that writes checks straight into operating companies (VC, angel, PE, growth equity, family-office direct). Role fields: stage, check size, lead vs follow.
_Avoid_: Conflating with LP/Allocator.

**LP / Allocator** (capital role):
A Firm that commits capital into funds rather than into companies (pension, endowment, SWF, fund-of-funds, family office acting as LP). Role fields: asset-class allocation %, ticket size into funds, prior GP commitments.
_Avoid_: "Investor" alone; "Limited Partner" spelled out repeatedly once LP is established.

**Strategic Acquirer** (capital role):
A Firm or corporate that buys companies outright (the M&A buyer the sell-side persona targets). Role fields: acquisition history, EBITDA/revenue appetite, platform vs add-on.
_Avoid_: "Buyer" without qualifier.

**Active Firm**:
A Firm with at least one qualifying Deal inside the activity window AND at least one open or investing fund. Only Active Firms appear in default search.
_Avoid_: "Live", "current" as loose synonyms.

**Activity window**:
The rolling lookback (default 24 months) used to judge whether a Firm is Active and to compute deal velocity.
_Avoid_: Fixed calendar-year windows.

**Recency decay**:
The ranking mechanism that DEMOTES (never excludes) a Firm when it is stale in the searched sector or has lost the relevant sector-lead Partner. Exclusion is governed only by Active Firm status.
_Avoid_: Using "decay" to mean removal from the index.

**Deal**:
One Firm's participation in a funding event into an operating company. Every Deal is tagged NEW vs FOLLOW-ON and LEAD vs FOLLOW. Counted when announced or closed, never when rumored.
_Avoid_: "Deal" for an entire company-side funding round; "investment" used loosely.

**Deal velocity**:
The count and pace of Deals (new and follow-on) by a Firm inside the activity window. Gates Active Firm status. Distinct from appetite, which weights NEW deals.
_Avoid_: Equating velocity with appetite.

**Lead vs Follow**:
A per-Deal attribute. A Lead sets valuation and terms, writes the largest check, often takes a board seat. A Follow accepts the lead's terms and relies on the lead's diligence.
_Avoid_: Treating lead/follow as a fixed Firm trait rather than a per-Deal one.

**Funding round**:
The company-side capital-raising event a Deal participates in: one operating company raising at a given stage on a given date. Several Firms' Deals can share one round, which is how co-investment is derived. Carries the total round size; a Deal carries the Firm's own check within it.
_Avoid_: Conflating the round (the company-side event) with a Deal (one Firm's participation in it).

**Acquisition**:
A Strategic Acquirer's outright purchase of a company — the M&A event the sell-side persona targets. Distinct from a Deal: it carries enterprise value, a revenue/EBITDA multiple, and platform-vs-add-on, and is never tagged new/follow-on or lead/follow. Acquisition history feeds the Strategic Acquirer role.
_Avoid_: Modelling an acquisition as a Deal, or tagging it new/follow-on or lead/follow.

**Verified**:
A contact state that holds only when BOTH Deliverability and Role currency pass inside the freshness SLA. If only one passes, the partial state is shown explicitly, never as a plain "Verified".
_Avoid_: Using "Verified" to mean deliverability alone.

**Deliverability**:
Whether a contact channel (email or phone) is actually reachable, with catch-all servers explicitly flagged rather than counted as a pass. Carries its own date.
_Avoid_: Treating a catch-all accept as deliverable.

**Role currency**:
Whether a Partner still holds the stated role at the stated Firm, corroborated by a recent source. Carries its own date, separate from Deliverability.
_Avoid_: Inferring role currency from email deliverability.

**Sector taxonomy**:
The single canonical, startup-native, multi-label category set used both to tag companies (and therefore Deals) and to resolve user queries. Companies carry primary and secondary labels.
_Avoid_: GICS/NAICS codes; free tags; maintaining separate vocabularies for tagging and for search.

**Sector profile**:
A Firm's behavioral sector signature: the recency-weighted aggregation of the sector labels of the companies it did NEW Deals into. Drives sector matching and appetite.
_Avoid_: Using website-stated sectors as the Firm's sector profile.

**Thesis tags**:
A controlled, filterable set of structured thesis dimensions not covered by sector/stage/check (e.g. business model, ownership target, technical-risk appetite), derived from Deals where possible. The only thesis data permitted to drive filtering.
_Avoid_: Free-text thesis used as a filter.

**Thesis narrative**:
An LLM-summarized, source-cited, read-only paragraph describing a Firm's stated thesis, shown for pitch-tailoring. Never a filter input.
_Avoid_: Filtering or excluding on narrative content.

**Check size**:
A per-stage distribution of the amounts a Firm writes, derived from its NEW Deals at each stage. A check-size filter always operates within a selected stage.
_Avoid_: A single global Firm-level range; stated/published check size.

**Hard predicate**:
An exact, pass/fail query constraint (investor type, numeric bounds, dates, allocation %, dry powder, deal counts). Filters the full universe first. Never softened or demoted to a ranking nudge.
_Avoid_: Treating a hard predicate as a preference or similarity signal.

**Soft signal**:
A fuzzy constraint (sector fit, thesis tags, "appetite") resolved via taxonomy and behavioral data, used to RANK within the hard-filtered set. Never excludes.
_Avoid_: Letting a soft signal override or bypass a hard predicate.

**Query parse**:
The step that compiles a natural-language query into hard predicates plus soft signals, always surfaced to the user as editable filters.
_Avoid_: Black-box interpretation the user cannot see or correct.

## Flagged ambiguities

- **LLM output is display-only (resolved 2026-06-02):** LLM-extracted content (e.g. Thesis narrative) may inform what a user reads but never drives filtering, ranking-exclusion, or the "unforgeable behavioral" claim. Filters operate only on structured, deal-derived data.

- **"Investor" (resolved 2026-06-02):** was used for Firm, Partner, and LP interchangeably. Resolution: Firm is the searchable unit; Partner is the contactable human nested under it; "Investor" is umbrella-only and never the unit of search/ranking/export.
- **Firm spanning roles (resolved 2026-06-02):** a family office can be both a Direct Investor and an LP/Allocator. Resolution: one Firm record, multiple Capital role facets, not duplicate records. See ADR 0001.

## Example dialogue

Founder: "Show me Series B fintech leads."
Platform: returns Firm rows. Each row shows the Firm's Investment Cadence and surfaces the Partner(s) at that Firm who lead fintech at Series B.
Founder: "Export Sequoia."
Platform: exports one Firm record with the matching fintech Partners attached as contacts. The Cadence score on the export is Sequoia's, not a per-person number.
