# Startup-native multi-label sector taxonomy over GICS/NAICS

We use a single canonical startup-native sector taxonomy (Crunchbase/Dealroom-style categories), multi-label with primary/secondary, for both tagging companies and resolving user queries. We explicitly rejected GICS/NAICS.

Why: the headline use cases are phrased in startup-ecosystem language ("vertical SaaS", "climate-tech", "fintech infrastructure") that GICS and NAICS, built for public-market classification, represent poorly. Forcing those codes would degrade exactly the stress-test queries the product must win. Multi-label is required because cross-sector companies are common and single-label would corrupt the behavioral sector aggregation. A finance-trained reader will expect GICS, so this deliberate deviation is recorded to prevent a future "let us standardize on GICS" reversal.

Considered options: (1) startup-native multi-label (chosen); (2) GICS/NAICS; (3) free-tag folksonomy. Consequence: re-tagging the corpus later would be expensive, so the taxonomy choice is treated as hard to reverse.
