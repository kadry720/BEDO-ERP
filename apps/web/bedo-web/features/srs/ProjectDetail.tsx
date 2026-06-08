"use client";

import Link from "next/link";
import type { ComponentType } from "react";
import { useMemo } from "react";
import { Activity, AlertTriangle, Clock3, FolderOpen, UserMinus, Users } from "lucide-react";
import { projectRoute, routeSegment } from "@/lib/route-ids";
import type { BedoProject, TrainerItem, TrainerItemList } from "@/features/srs/types";
import { formatDistance, formatNodeId } from "@/features/srs/workflowPresentation";

type Props = {
  project: BedoProject;
  initialItems: TrainerItemList;
  mode: "gm" | "srs";
};

export function ProjectDetail({ project, initialItems, mode }: Props) {
  const items = initialItems.trainer_items;
  const itemRouteBase = mode === "gm" ? projectRoute("gm", project.name, "/items") : projectRoute("srs", project.name, "/items");
  const stats = useMemo(() => trainerStats(items), [items]);

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">{project.project_code}</div>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-3xl font-black text-slate-950">{project.project_name}</h2>
            <p className="mt-2 text-sm font-medium text-slate-600">End user: {project.end_user} | PO deadline: {project.po_deadline_date}</p>
          </div>
        </div>
      </header>

      <TrainerStatsCards stats={stats} />
      <TrainerItemsTable items={items} itemRouteBase={itemRouteBase} />
    </section>
  );
}

function TrainerStatsCards({ stats }: { stats: ReturnType<typeof trainerStats> }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <Stat icon={FolderOpen} label="Trainers Done" value={stats.done} tone="green" />
      <Stat icon={Activity} label="Trainers In Progress" value={stats.inProgress} tone="amber" />
      <Stat icon={UserMinus} label="Without Owner" value={stats.withoutOwner} tone="slate" />
      <Stat icon={Users} label="Owner Assigned / No Team" value={stats.ownerNoTeam} tone="blue" />
      <Stat icon={AlertTriangle} label="Awaiting GM Approval" value={stats.awaitingGm} tone="blue" />
      <Stat icon={Clock3} label="Awaiting SRS Manager Approval" value={stats.awaitingSrsManager} tone="blue" />
    </div>
  );
}

function Stat({ icon: Icon, label, value, tone }: { icon: ComponentType<{ className?: string }>; label: string; value: number; tone: "green" | "amber" | "blue" | "slate" }) {
  const color = {
    green: "text-emerald-700 bg-emerald-50",
    amber: "text-amber-700 bg-amber-50",
    blue: "text-blue-700 bg-blue-50",
    slate: "text-slate-700 bg-slate-100",
  }[tone];
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</div>
        <div className={`rounded-md p-2 ${color}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3 text-3xl font-black text-slate-950">{value}</div>
    </div>
  );
}

function TrainerItemsTable({ items, itemRouteBase }: { items: TrainerItem[]; itemRouteBase: string }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="border-b border-slate-200 px-5 py-4">
        <h3 className="text-lg font-black text-slate-950">Trainer Items</h3>
        <p className="text-sm font-medium text-slate-500">{items.length} trainer item(s)</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[980px] w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-black uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Trainer Name</th>
              <th className="px-4 py-3">Quantity</th>
              <th className="px-4 py-3">Current SRS Node</th>
              <th className="px-4 py-3">Project Owner</th>
              <th className="px-4 py-3">Deadline Due</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.name} className="hover:bg-slate-50">
                <td className="max-w-[260px] truncate px-4 py-3 font-black text-slate-950" title={item.trainer_item_name}>{item.trainer_item_name}</td>
                <td className="px-4 py-3 text-slate-600">{item.quantity}</td>
                <td className="px-4 py-3 text-slate-600">{formatNodeId(item.workflow?.current_node || item.current_node)}</td>
                <td className="px-4 py-3 text-slate-600">{item.workflow?.project_owner_full_name || item.current_responsible_name || "-"}</td>
                <td className="px-4 py-3"><CountdownBadge startAt={item.deadline?.start_at} dueAt={item.deadline?.due_at} serverNow={item.deadline?.server_now} /></td>
                <td className="px-4 py-3">
                  <span className={`rounded-full border px-2.5 py-1 text-xs font-black ${isDone(item) ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-amber-200 bg-amber-50 text-amber-800"}`}>
                    {isDone(item) ? "Done" : "In Progress"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <Link className="focus-ring inline-flex min-h-9 items-center rounded-md bg-slate-900 px-3 text-xs font-black text-white hover:bg-slate-700" href={`${itemRouteBase}/${routeSegment(item.name)}`}>
                    Open Workflow
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && <div className="m-5 rounded-md border border-dashed border-slate-300 p-8 text-center text-sm font-bold text-slate-500">No trainer items.</div>}
      </div>
    </section>
  );
}

function CountdownBadge({ startAt, dueAt, serverNow }: { startAt?: string; dueAt?: string; serverNow?: string }) {
  const now = new Date(serverNow || Date.now());
  if (!startAt || !dueAt) return <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-black text-slate-600">No active deadline</span>;
  const start = new Date(startAt);
  const due = new Date(dueAt);
  let label = "Due in";
  let seconds = (due.getTime() - now.getTime()) / 1000;
  let className = "border-amber-200 bg-amber-50 text-amber-800";
  if (now < start) {
    label = "Starting in";
    seconds = (start.getTime() - now.getTime()) / 1000;
    className = "border-slate-200 bg-slate-50 text-slate-700";
  } else if (now > due) {
    label = "Overdue by";
    seconds = (now.getTime() - due.getTime()) / 1000;
    className = "border-red-200 bg-red-50 text-red-800";
  }
  return <span className={`rounded-full border px-2.5 py-1 text-xs font-black ${className}`}>{label} {formatDistance(seconds)}</span>;
}

function trainerStats(items: TrainerItem[]) {
  return items.reduce(
    (acc, item) => {
      if (isDone(item)) acc.done += 1;
      else acc.inProgress += 1;
      if (!item.workflow?.project_owner) acc.withoutOwner += 1;
      if (item.workflow?.project_owner && item.workflow.current_node === "MANDATORY_COORDINATION_MEETING") acc.ownerNoTeam += 1;
      if (item.workflow?.current_node === "GM_APPROVAL") acc.awaitingGm += 1;
      if (item.workflow?.current_node === "GATE_1_SRS_MANAGER_APPROVAL") acc.awaitingSrsManager += 1;
      return acc;
    },
    { done: 0, inProgress: 0, withoutOwner: 0, ownerNoTeam: 0, awaitingGm: 0, awaitingSrsManager: 0 }
  );
}

function isDone(item: TrainerItem) {
  return item.status === "SRS_COMPLETE" || item.workflow?.status === "SRS_COMPLETE";
}
