# Verification is two independent signals, not one

"Verified" on a contact means BOTH of two independently dated checks pass inside the freshness SLA: Deliverability (the channel is reachable, with catch-all servers flagged rather than counted as a pass) and Role currency (the person still holds the role, corroborated by a recent source). When only one passes, the partial state is shown explicitly.

Why: the platform's structural advantage over PitchBook is verified contact data. A single deliverability check is defeated by corporate catch-all servers, which keep accepting mail for departed employees, so a naive "Verified" badge would routinely point users at people who have left the firm. Splitting the signal is what makes the badge honest and the moat real. The rejected single-flag model was cleaner in the UI but reintroduced exactly that liability.

Status: accepted. This standard shapes the contact-data pipelines and the freshness SLA instrumentation.
