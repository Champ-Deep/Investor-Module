import type { SearchFirm } from "../types";
import { getFirm } from "./api";

function download(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function esc(value: unknown): string {
  const s = value == null ? "" : String(value);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

// Ranked CSV with the best verified deal-team contact attached per firm (PRD export requirement).
export async function exportFirmsCsv(firms: SearchFirm[]) {
  const headers = [
    "rank", "firm", "investor_type", "hq", "cadence", "partner", "title", "email", "verified",
  ];
  const profiles = await Promise.all(
    firms.slice(0, 100).map((f) => getFirm(f.slug).catch(() => null)),
  );
  const rows = profiles.map((p, i) => {
    const f = firms[i];
    let partner = "", title = "", email = "", verified = "";
    if (p) {
      const best =
        p.partners.find((pt) => pt.contacts.some((c) => c.verified_state === "verified")) ||
        p.partners[0];
      if (best) {
        partner = best.name;
        title = best.title || "";
        const contact = best.contacts.find((c) => c.kind === "email");
        email = contact?.value || "";
        verified = contact?.verified_state || "";
      }
    }
    return [
      String(i + 1), f.name, f.investor_type, f.hq_country || "",
      f.cadence_score == null ? "" : String(f.cadence_score), partner, title, email, verified,
    ];
  });
  const csv = [headers, ...rows].map((r) => r.map(esc).join(",")).join("\n");
  download("cadence-export.csv", csv);
}
