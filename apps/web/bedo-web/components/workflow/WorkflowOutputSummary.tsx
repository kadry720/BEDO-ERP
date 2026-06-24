"use client";

import { useState } from "react";
import { CheckCircle2, Copy } from "lucide-react";
import type { WorkflowOutputRow } from "./workflow-types";

export function WorkflowOutputSummary({ rows, title = "Step complete", description = "Recorded workflow output is shown below." }: { rows: WorkflowOutputRow[]; title?: string; description?: string }) {
  return (
    <div className="space-y-4">
      <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-black text-emerald-800">
          <CheckCircle2 className="h-4 w-4" />
          {title}
        </div>
        <p className="mt-1 text-sm font-medium text-emerald-900/80">{description}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {rows.map((row) => <WorkflowOutputCard key={row.label} row={row} />)}
      </div>
    </div>
  );
}

export function WorkflowOutputCard({ row }: { row: WorkflowOutputRow }) {
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "failed">("idle");

  async function copyPath(value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("failed");
    }
  }

  if (row.list) {
    return (
      <div className="rounded-md border border-slate-200 bg-white p-4">
        <div className="text-[11px] font-black uppercase tracking-wide text-slate-500">{row.label}</div>
        {row.list.length ? (
          <ul className="mt-3 grid gap-2">
            {row.list.map((member) => (
              <li key={member} className="flex items-center gap-2 rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-950">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-slate-500" />
                <span className="min-w-0 truncate">{member}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="mt-1 text-sm font-semibold text-slate-950">-</div>
        )}
      </div>
    );
  }

  if (row.copyable) {
    return (
      <div className="rounded-md border border-slate-200 bg-white p-4 sm:col-span-2">
        <div className="text-[11px] font-black uppercase tracking-wide text-slate-500">{row.label}</div>
        <div className="mt-2 flex min-w-0 items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
          <span className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-950" title={row.value || "-"}>
            {row.value || "-"}
          </span>
          <button
            className="focus-ring inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-100"
            type="button"
            onClick={() => {
              if (row.value) void copyPath(row.value);
            }}
            title="Copy path"
            aria-label="Copy path"
          >
            <Copy className="h-4 w-4" />
          </button>
        </div>
        {copyStatus !== "idle" && (
          <div className={`mt-2 text-xs font-black ${copyStatus === "copied" ? "text-emerald-700" : "text-red-700"}`}>
            {copyStatus === "copied" ? "Copied" : "Copy failed"}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="text-[11px] font-black uppercase tracking-wide text-slate-500">{row.label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-slate-950">{row.value || "-"}</div>
    </div>
  );
}
