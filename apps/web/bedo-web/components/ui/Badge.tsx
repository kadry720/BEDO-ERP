import { clsx } from "clsx";
import type { HTMLAttributes } from "react";

type BadgeTone = "slate" | "blue" | "green" | "amber" | "red" | "dark";

const toneClass: Record<BadgeTone, string> = {
  slate: "border-slate-200 bg-slate-100 text-slate-700",
  blue: "border-blue-200 bg-blue-50 text-blue-800",
  green: "border-emerald-200 bg-emerald-50 text-emerald-800",
  amber: "border-amber-200 bg-amber-50 text-amber-800",
  red: "border-red-200 bg-red-50 text-red-800",
  dark: "border-slate-950 bg-slate-950 text-white",
};

export function Badge({ className, tone = "slate", ...props }: HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return <span className={clsx("inline-flex w-fit items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-black", toneClass[tone], className)} {...props} />;
}
