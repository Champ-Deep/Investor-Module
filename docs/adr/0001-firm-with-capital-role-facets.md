# One Firm record with multiple capital-role facets

A Firm can act as a Direct Investor, an LP/Allocator, and a Strategic Acquirer at the same time (e.g. a family office that both writes Series A checks and commits to VC funds). We decided to model this as a single Firm record carrying one or more Capital role facets, each unlocking role-specific fields, rather than as separate entity types per role.

Why: the three personas (founder, sell-side banker, placement agent) then query one shared dataset filtered by role, cross-role intelligence is preserved (an LP that also angel-invests is visible as both), and we avoid duplicating and re-syncing the same institution across records. The rejected alternative, separate entity types, was cleaner per-schema but fragmented the institution and lost cross-role signal.

Considered options: (1) one Firm, multiple role facets (chosen); (2) separate Direct-Investor and LP entity types; (3) single-role MVP, defer multi-role.
