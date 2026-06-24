"use client";

import Link from "next/link";
import type { ComponentType } from "react";
import { useMemo } from "react";
import { Activity, CheckCircle2, ClipboardCheck, Clock3, UserCheck, Users } from "lucide-react";
import type { ArdProjectDetailData, ArdProjectTrainerItem } from "@/features/ard/types";
import { formatNodeId, formatStatus, statusBadgeClass } from "@/features/srs/workflowPresentation";
import { projectWorkflowRoute, routeSegment } from "@/lib/route-ids";

type Props = {
  detail: ArdProjectDetailData;
};

export function ArdProjectDetail({ detail }: Props) {
  const items = detail.trainer_items;
  const stats = useMemo(() => ardStats(items), [items]);
  const itemRouteBase = projectWorkflowRoute("ard", detail.project.name, "/items");

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500">
              <ClipboardCheck className="h-4 w-4" />
              ARD Project
            </div>
            <h2 className="mt-2 text-3xl font-black text-slate-950">{detail.project.project_name}</h2>
            <p className="mt-2 text-sm font-medium text-slate-600">
              {detail.project.project_code} | End user: {detail.project.end_user} | PO deadline: {detail.project.po_deadline_date}
            </p>
          </div>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Stat icon={Activity} label="Active ARD Workflows" value={stats.active} tone="amber" />
        <Stat icon={UserCheck} label="ARD Owner Assigned" value={stats.ownerAssigned} tone="blue" />
        <Stat icon={Users} label="ARD Team Selected" value={stats.teamSelected} tone="slate" />
        <Stat icon={CheckCircle2} label="SCMDP Complete" value={stats.complete} tone="green" />
      </div>

      <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
        <div className="border-b border-slate-200 px-5 py-4">
          <h3 className="text-lg font-black text-slate-950">ARD Trainer Workflows</h3>
          <p className="text-sm font-medium text-slate-500">{items.length} trainer workflow(s)</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-black uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Trainer Name</th>
                <th className="px-4 py-3">Quantity</th>
                <th className="px-4 py-3">ARD Project Owner</th>
                <th className="px-4 py-3">Deadline Due</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => (
                <tr key={item.name} className="hover:bg-slate-50">
                  <td className="max-w-[260px] truncate px-4 py-3 font-black text-slate-950" title={item.trainer_item_name}>
                    {item.trainer_item_name}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{item.quantity}</td>
                  <td className="px-4 py-3 text-slate-600" title={`ARD Team: ${teamSummary(item)}`}>{ownerName(item)}</td>
                  <td className="px-4 py-3">
                    <DeadlineBadge startAt={item.deadline?.start_at} dueAt={item.deadline?.due_at} serverNow={item.deadline?.server_now} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-black ${statusBadgeClass(item.ard_workflow.status)}`} title={`Current ARD Step: ${formatNodeId(item.ard_workflow.current_node)}`}>
                      {ardStatusLabel(item.ard_workflow.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link className="focus-ring inline-flex min-h-9 items-center whitespace-nowrap rounded-md bg-slate-900 px-3 text-xs font-black text-white hover:bg-slate-700" href={`${itemRouteBase}/${routeSegment(item.name)}`}>
                      Open Workflow
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!items.length && <div className="m-5 rounded-md border border-dashed border-slate-300 p-8 text-center text-sm font-bold text-slate-500">No ARD trainer workflows.</div>}
        </div>
      </section>
    </section>
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

function DeadlineBadge({ startAt, dueAt, serverNow }: { startAt?: string; dueAt?: string; serverNow?: string }) {
  if (!startAt || !dueAt) {
    return <span className="whitespace-nowrap rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-black text-slate-600">No active deadline</span>;
  }
  const now = new Date(serverNow || Date.now());
  const start = new Date(startAt);
  const due = new Date(dueAt);
  const active = now >= start && now <= due;
  const overdue = now > due;
  const label = overdue ? "Overdue" : active ? "Active" : "Scheduled";
  const className = overdue ? "border-red-200 bg-red-50 text-red-800" : active ? "border-amber-200 bg-amber-50 text-amber-800" : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-black ${className}`}>
      <Clock3 className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}

function ownerName(item: ArdProjectTrainerItem) {
  const owner = item.team_members.find((member) => member.is_project_owner);
  return owner?.full_name || item.ard_workflow.project_owner || "Not assigned";
}

function teamSummary(item: ArdProjectTrainerItem) {
  const members = item.team_members.filter((member) => !member.is_project_owner);
  if (!members.length) return "No team selected";
  return members.length === 1 ? members[0].full_name : `${members.length} members`;
}

function ardStatusLabel(status: string) {
  return formatStatus(status).replace(/^ARD /, "");
}

function ardStats(items: ArdProjectTrainerItem[]) {
  return items.reduce(
    (acc, item) => {
      if (item.ard_workflow.status === "ARD_COMPLETE") acc.complete += 1;
      else acc.active += 1;
      if (item.ard_workflow.project_owner) acc.ownerAssigned += 1;
      if (item.team_members.some((member) => !member.is_project_owner)) acc.teamSelected += 1;
      return acc;
    },
    { active: 0, ownerAssigned: 0, teamSelected: 0, complete: 0 }
  );
}
