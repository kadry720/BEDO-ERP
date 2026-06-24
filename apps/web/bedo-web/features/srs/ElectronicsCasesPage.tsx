"use client";

import { useEffect, useMemo, useState } from "react";
import { Cpu, RefreshCw, Save, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/Button";

type ElectronicsCaseRow = {
  workflow_instance: string;
  project: string;
  project_code: string;
  project_name: string;
  end_user: string;
  trainer_item: string;
  trainer_item_name: string;
  quantity: number;
  ard_status: string;
  current_node: string;
  electronics_status: string;
  electronics_subcase: string;
  responsible_user: string;
  started_at: string;
  completed_at: string;
};

const subcaseOptions = [
  ["INVENTORY_STOCK", "Inventory stock available"],
  ["DESIGN_COMPLETE_NO_INVENTORY", "Design complete, no inventory"],
  ["NEW_DESIGN", "New electronics design"],
] as const;

export function ElectronicsCasesPage() {
  const [cases, setCases] = useState<ElectronicsCaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");

  async function refresh() {
    setLoading(true);
    setError("");
    const response = await fetch("/api/srs/ard-electronics-cases", { cache: "no-store" });
    const data = await response.json().catch(() => ({}));
    setLoading(false);
    if (!response.ok) {
      setError(data.error || "Electronics cases could not be loaded.");
      return;
    }
    setCases(Array.isArray(data.cases) ? data.cases : []);
  }

  async function submitAction(trainerItem: string, payload: Record<string, unknown>) {
    setPending(`${trainerItem}:${payload.action}`);
    setError("");
    const response = await fetch("/api/ard/workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trainer_item: trainerItem, ...payload }),
    });
    const data = await response.json().catch(() => ({}));
    setPending("");
    if (!response.ok) {
      setError(data.error || "Electronics action failed.");
      return;
    }
    await refresh();
  }

  useEffect(() => {
    void refresh();
  }, []);

  const activeCount = useMemo(() => cases.filter((row) => row.electronics_status !== "COMPLETED").length, [cases]);

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500">
              <Cpu className="h-4 w-4" />
              SRS Electronics Section Head
            </div>
            <h1 className="mt-2 text-3xl font-black text-slate-950">ARD Electronics Cases</h1>
            <p className="mt-2 text-sm font-semibold text-slate-600">Trainer-level ARD interruption cases requiring Electronics classification or completion.</p>
          </div>
          <Button variant="secondary" type="button" onClick={() => refresh()} disabled={loading}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <Stat label="Active Cases" value={activeCount} />
        <Stat label="Loaded Trainers" value={cases.length} />
        <Stat label="Completed In Queue" value={cases.length - activeCount} />
      </div>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-lg font-black text-slate-950">Electronics Trainer Queue</h2>
          <p className="text-sm font-semibold text-slate-500">{loading ? "Loading cases..." : `${cases.length} trainer case(s)`}</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-black uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Project</th>
                <th className="px-4 py-3">Trainer Item</th>
                <th className="px-4 py-3">ARD Status</th>
                <th className="px-4 py-3">Electronics State</th>
                <th className="px-4 py-3">Started</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cases.map((row) => (
                <ElectronicsCaseTableRow key={`${row.workflow_instance}:${row.trainer_item}`} row={row} pending={pending} onSubmit={submitAction} />
              ))}
            </tbody>
          </table>
          {!loading && !cases.length && (
            <div className="m-5 rounded-md border border-dashed border-slate-300 p-8 text-center text-sm font-bold text-slate-500">No ARD electronics cases are waiting for SRS Electronics.</div>
          )}
        </div>
      </section>
    </section>
  );
}

function ElectronicsCaseTableRow({
  row,
  pending,
  onSubmit,
}: {
  row: ElectronicsCaseRow;
  pending: string;
  onSubmit: (trainerItem: string, payload: Record<string, unknown>) => Promise<void>;
}) {
  const [subcase, setSubcase] = useState(row.electronics_subcase || "INVENTORY_STOCK");
  const [deadlineDays, setDeadlineDays] = useState("1");
  const needsDeadline = subcase !== "INVENTORY_STOCK";
  const saving = pending === `${row.trainer_item}:choose_electronics_subcase`;
  const completing = pending === `${row.trainer_item}:complete_electronics`;

  return (
    <tr className="align-top hover:bg-slate-50">
      <td className="px-4 py-4">
        <div className="font-black text-slate-950">{row.project_code}</div>
        <div className="mt-1 max-w-[240px] truncate text-slate-600" title={row.project_name}>{row.project_name}</div>
        <div className="mt-1 text-xs font-semibold text-slate-500">{row.end_user}</div>
      </td>
      <td className="px-4 py-4">
        <div className="font-black text-slate-950">{row.trainer_item_name}</div>
        <div className="mt-1 text-xs font-semibold text-slate-500">Qty {row.quantity}</div>
      </td>
      <td className="px-4 py-4">
        <StatusPill value={row.ard_status} />
      </td>
      <td className="px-4 py-4">
        <StatusPill value={row.electronics_status} />
        {row.electronics_subcase && <div className="mt-2 text-xs font-bold text-slate-500">{formatValue(row.electronics_subcase)}</div>}
      </td>
      <td className="px-4 py-4 text-xs font-semibold text-slate-600">{row.started_at || "Not started"}</td>
      <td className="px-4 py-4">
        <div className="grid min-w-[300px] gap-2">
          <label className="text-xs font-black uppercase tracking-wide text-slate-500" htmlFor={`subcase-${row.trainer_item}`}>Electronics subcase</label>
          <select id={`subcase-${row.trainer_item}`} className="focus-ring rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" value={subcase} onChange={(event) => setSubcase(event.target.value)}>
            {subcaseOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          {needsDeadline && (
            <input
              className="focus-ring rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold"
              type="number"
              min={1}
              step={1}
              aria-label="Supplier deadline days"
              value={deadlineDays}
              onChange={(event) => setDeadlineDays(event.target.value)}
            />
          )}
          <div className="flex flex-wrap gap-2">
            <Button type="button" disabled={saving || (needsDeadline && !deadlineDays)} onClick={() => onSubmit(row.trainer_item, { action: "choose_electronics_subcase", subcase, supplier_deadline_days: deadlineDays })}>
              <Save className="h-4 w-4" />
              {saving ? "Saving..." : "Save subcase"}
            </Button>
            <Button variant="secondary" type="button" disabled={completing} onClick={() => onSubmit(row.trainer_item, { action: "complete_electronics" })}>
              <CheckCircle2 className="h-4 w-4" />
              {completing ? "Completing..." : "Complete"}
            </Button>
          </div>
        </div>
      </td>
    </tr>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-3xl font-black text-slate-950">{value}</div>
    </div>
  );
}

function StatusPill({ value }: { value: string }) {
  return <span className="whitespace-nowrap rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-black text-amber-800">{formatValue(value)}</span>;
}

function formatValue(value: string) {
  return value ? value.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Unknown";
}
