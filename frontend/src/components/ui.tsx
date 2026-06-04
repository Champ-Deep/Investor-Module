import type { ButtonHTMLAttributes, ReactNode } from "react";

// Color keys are kept stable (callers pass green/amber/red/blue/slate) but restyled to the palette.
const BADGE_TONES: Record<string, string> = {
  slate: "bg-ink/[0.05] text-muted",
  green: "bg-positive/10 text-positive",
  amber: "bg-warn/10 text-warn",
  red: "bg-negative/10 text-negative",
  blue: "bg-accent-tint text-accent",
};

export function Label({ children }: { children: ReactNode }) {
  return (
    <span className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-faint">
      {children}
    </span>
  );
}

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
    <section className={`rounded-xl border border-line bg-surface p-5 ${className}`}>
      {title && (
        <div className="mb-4">{typeof title === "string" ? <Label>{title}</Label> : title}</div>
      )}
      {children}
    </section>
  );
}

export function Badge({ children, color = "slate" }: { children: ReactNode; color?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${
        BADGE_TONES[color] || BADGE_TONES.slate
      }`}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  variant = "primary",
  className = "",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50";
  const tone =
    variant === "primary"
      ? "bg-accent text-white hover:bg-accent/90"
      : "border border-line text-ink hover:bg-ink/[0.04]";
  return (
    <button className={`${base} ${tone} ${className}`} {...rest}>
      {children}
    </button>
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
