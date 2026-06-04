import type { ReactNode } from "react";

const BADGE_COLORS: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  green: "bg-green-100 text-green-700",
  amber: "bg-amber-100 text-amber-800",
  red: "bg-red-100 text-red-700",
  blue: "bg-blue-100 text-blue-700",
};

export function Card({
  title,
  children,
  className = "",
}: {
  title?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      {title && <div className="mb-3 text-sm font-semibold text-slate-700">{title}</div>}
      {children}
    </div>
  );
}

export function Badge({ children, color = "slate" }: { children: ReactNode; color?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        BADGE_COLORS[color] || BADGE_COLORS.slate
      }`}
    >
      {children}
    </span>
  );
}

export function cadenceColor(score: number): string {
  return score >= 70 ? "green" : score >= 45 ? "amber" : "red";
}

export function verifiedBadge(state: string): { color: string; label: string } {
  const map: Record<string, [string, string]> = {
    verified: ["green", "Verified"],
    catch_all: ["red", "Catch-all (not verified)"],
    deliverable_only: ["amber", "Email only"],
    role_current_only: ["amber", "Role only"],
    unverified: ["slate", "Unverified"],
  };
  const [color, label] = map[state] || ["slate", state];
  return { color, label };
}
