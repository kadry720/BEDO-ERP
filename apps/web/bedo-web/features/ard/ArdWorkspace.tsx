"use client";

import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { CalendarClock, CheckCircle2, ClipboardCheck, Copy, Loader2, Users } from "lucide-react";
import { Button } from "@/components/Button";
import type { ArdFlowchartDefinition, ArdWorkspaceData } from "@/features/ard/types";
import { formatNodeId, formatStatus, statusBadgeClass } from "@/features/srs/workflowPresentation";

export function ArdWorkspace({
  initialWorkspace,
  flowchart,
}: {
  initialWorkspace: ArdWorkspaceData;
  flowchart: ArdFlowchartDefinition;
}) {
  const [workspace, setWorkspace] = useState(initialWorkspace);
  const [activeNode, setActiveNode] = useState(workspace.workflow.current_node);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const states = useMemo(() => new Map(workspace.node_states.map((state) => [state.node_id, state])), [workspace.node_states]);
  const availability = useMemo(() => new Map(workspace.node_availability.map((row) => [row.nodeId, row])), [workspace.node_availability]);
  const activeState = states.get(activeNode);
  const activeAvailability = availability.get(activeNode);

  async function submit(action: string, payload: Record<string, unknown> = {}) {
    setLoading(action);
    setError("");
    const response = await fetch("/api/ard/workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, trainer_item: workspace.trainer_item.name, ...payload }),
    });
    const data = await response.json().catch(() => ({}));
    setLoading("");
    if (!response.ok) {
      setError(data?.error || "ARD workflow action failed.");
      return;
    }
    setWorkspace(data);
    setActiveNode(data.workflow?.current_node || activeNode);
  }

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">{workspace.project.project_code}</div>
            <h1 className="mt-2 text-3xl font-black text-slate-950">{workspace.trainer_item.trainer_item_name}</h1>
            <p className="mt-2 text-sm font-semibold text-slate-600">
              ARD workflow generation {workspace.workflow.generation} | Current step: {formatNodeId(workspace.workflow.current_node)}
            </p>
          </div>
          <StatusBadge status={workspace.workflow.status} />
        </div>
      </header>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <section className="rounded-md border border-slate-200 bg-white shadow-panel">
          <div className="border-b border-slate-200 px-5 py-4">
            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500">
              <ClipboardCheck className="h-4 w-4" />
              ARD Flowchart
            </div>
          </div>
          <div className="grid gap-3 p-5 md:grid-cols-2 2xl:grid-cols-3">
            {flowchart.nodes.map((node) => {
              const state = states.get(node.id);
              const row = availability.get(node.id);
              const active = activeNode === node.id;
              return (
                <button
                  key={node.id}
                  type="button"
                  disabled={!row?.canOpen}
                  onClick={() => setActiveNode(node.id)}
                  className={`focus-ring min-h-28 rounded-md border p-4 text-left transition ${
                    active ? "border-slate-950 bg-slate-950 text-white" : nodeCardClass(state?.status, row?.canOpen)
                  } ${!row?.canOpen ? "cursor-not-allowed opacity-80" : ""}`}
                >
                  <div className="text-[11px] font-black uppercase tracking-wide opacity-80">{node.column}</div>
                  <div className="mt-2 text-base font-black">{node.label}</div>
                  <div className="mt-3">
                    <StatusBadge status={state?.status || "LOCKED"} />
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        <aside className="space-y-5">
          <NodePanel
            nodeId={activeNode}
            state={activeState}
            availability={activeAvailability}
            workspace={workspace}
            loading={loading}
            onSubmit={submit}
          />
          <MeetingsPanel workspace={workspace} />
          <TeamPanel workspace={workspace} />
        </aside>
      </div>
    </section>
  );
}

function NodePanel({
  nodeId,
  state,
  availability,
  workspace,
  loading,
  onSubmit,
}: {
  nodeId: string;
  state: ArdWorkspaceData["node_states"][number] | undefined;
  availability: ArdWorkspaceData["node_availability"][number] | undefined;
  workspace: ArdWorkspaceData;
  loading: string;
  onSubmit: (action: string, payload?: Record<string, unknown>) => void;
}) {
  const canAct = Boolean(availability?.canAct);
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-black uppercase tracking-wide text-slate-500">Selected Node</div>
          <h2 className="mt-1 text-xl font-black text-slate-950">{formatNodeId(nodeId)}</h2>
        </div>
        <StatusBadge status={state?.status || "LOCKED"} />
      </div>
      {!canAct && availability?.disabledReason && <p className="mt-3 text-sm font-semibold text-slate-600">{availability.disabledReason}</p>}
      <div className="mt-5">
        {nodeId === "INTERNAL_ARD_SYNC_MEETING" && (
          <InternalSyncForm disabled={!canAct} loading={loading} users={workspace.ard_users} onSubmit={onSubmit} canComplete={state?.status === "IN_PROGRESS"} />
        )}
        {nodeId === "ARD_PROJECT_OWNER_ASSIGNMENT" && (
          <OwnerForm disabled={!canAct} loading={loading} users={workspace.ard_users} onSubmit={onSubmit} />
        )}
        {nodeId === "ARD_TEAM_SELECTION" && (
          <TeamSelectionForm disabled={!canAct} loading={loading} users={workspace.ard_users.filter((user) => user.user !== workspace.workflow.project_owner)} onSubmit={onSubmit} />
        )}
        {nodeId === "PROGRESS_REVIEW_MEETING" && (
          <ProgressReviewForm disabled={!canAct} loading={loading} onSubmit={onSubmit} />
        )}
        {nodeId === "SCMDP_SUBMISSION" && (
          <ScmdpForm disabled={!canAct} loading={loading} onSubmit={onSubmit} />
        )}
        {state?.status === "COMPLETED" && <CompletedOutput displayData={state.display_data || {}} />}
      </div>
    </section>
  );
}

function InternalSyncForm({
  disabled,
  loading,
  users,
  canComplete,
  onSubmit,
}: {
  disabled: boolean;
  loading: string;
  users: ArdWorkspaceData["ard_users"];
  canComplete: boolean;
  onSubmit: (action: string, payload?: Record<string, unknown>) => void;
}) {
  const [scheduledAt, setScheduledAt] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  return (
    <div className="space-y-4">
      <label className="block">
        <span className="text-sm font-black text-slate-800">Meeting date and time</span>
        <input className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type="datetime-local" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} disabled={disabled} />
      </label>
      <UserCheckboxes users={users} selected={selected} setSelected={setSelected} disabled={disabled} />
      <div className="flex flex-wrap gap-2">
        <ActionButton loading={loading === "schedule_internal_sync"} disabled={disabled || !scheduledAt} onClick={() => onSubmit("schedule_internal_sync", { scheduled_at: scheduledAt, participants: selected })}>
          Schedule Internal Sync
        </ActionButton>
        <ActionButton loading={loading === "complete_internal_sync"} disabled={disabled || !canComplete} onClick={() => onSubmit("complete_internal_sync")}>
          Complete Meeting
        </ActionButton>
      </div>
    </div>
  );
}

function OwnerForm({ disabled, loading, users, onSubmit }: { disabled: boolean; loading: string; users: ArdWorkspaceData["ard_users"]; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  const [owner, setOwner] = useState("");
  return (
    <div className="space-y-4">
      <select className="focus-ring w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm" value={owner} disabled={disabled} onChange={(event) => setOwner(event.target.value)}>
        <option value="">Select ARD project owner</option>
        {users.map((user) => <option key={user.user} value={user.user}>{user.full_name} | {user.business_role}</option>)}
      </select>
      <ActionButton loading={loading === "assign_owner"} disabled={disabled || !owner} onClick={() => onSubmit("assign_owner", { project_owner: owner })}>
        Assign Project Owner
      </ActionButton>
    </div>
  );
}

function TeamSelectionForm({ disabled, loading, users, onSubmit }: { disabled: boolean; loading: string; users: ArdWorkspaceData["ard_users"]; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  const [selected, setSelected] = useState<string[]>([]);
  return (
    <div className="space-y-4">
      <UserCheckboxes users={users} selected={selected} setSelected={setSelected} disabled={disabled} />
      <ActionButton loading={loading === "select_team"} disabled={disabled || !selected.length} onClick={() => onSubmit("select_team", { users: selected })}>
        Save ARD Team
      </ActionButton>
    </div>
  );
}

function ProgressReviewForm({ disabled, loading, onSubmit }: { disabled: boolean; loading: string; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-semibold text-slate-600">The on-plan path unlocks SCMDP. Interruption requests are handled in the next ARD interruption slice.</p>
      <ActionButton loading={loading === "progress_review"} disabled={disabled} onClick={() => onSubmit("progress_review", { outcome: "ON_PLAN" })}>
        Mark On Plan
      </ActionButton>
    </div>
  );
}

function ScmdpForm({ disabled, loading, onSubmit }: { disabled: boolean; loading: string; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  const [path, setPath] = useState("");
  const [checked, setChecked] = useState(false);
  return (
    <div className="space-y-4">
      <label className="block">
        <span className="text-sm font-black text-slate-800">SCMDP path</span>
        <input className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={path} disabled={disabled} onChange={(event) => setPath(event.target.value)} placeholder="Paste the shared SCMDP path" />
      </label>
      <label className="flex items-start gap-2 text-sm font-semibold text-slate-700">
        <input className="mt-1 accent-slate-950" type="checkbox" checked={checked} disabled={disabled} onChange={(event) => setChecked(event.target.checked)} />
        Mandatory SCMDP checklist is complete.
      </label>
      <ActionButton loading={loading === "submit_scmdp"} disabled={disabled || !path || !checked} onClick={() => onSubmit("submit_scmdp", { scmdp_path: path, checklist_confirmed: checked })}>
        Submit SCMDP
      </ActionButton>
    </div>
  );
}

function UserCheckboxes({ users, selected, setSelected, disabled }: { users: ArdWorkspaceData["ard_users"]; selected: string[]; setSelected: (users: string[]) => void; disabled: boolean }) {
  return (
    <div className="grid max-h-56 gap-2 overflow-y-auto pr-1">
      {users.map((user) => (
        <label key={user.user} className="flex cursor-pointer items-start gap-3 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
          <input
            className="mt-1 accent-slate-950"
            type="checkbox"
            disabled={disabled}
            checked={selected.includes(user.user)}
            onChange={(event) => setSelected(event.target.checked ? [...selected, user.user] : selected.filter((value) => value !== user.user))}
          />
          <span className="min-w-0">
            <span className="block truncate font-black text-slate-950">{user.full_name}</span>
            <span className="block truncate text-xs font-semibold text-slate-500">{user.business_role}</span>
          </span>
        </label>
      ))}
    </div>
  );
}

function MeetingsPanel({ workspace }: { workspace: ArdWorkspaceData }) {
  const meetings = [workspace.meetings.internal_sync, workspace.meetings.progress_review].filter(Boolean);
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500">
        <CalendarClock className="h-4 w-4" />
        Meetings
      </div>
      <div className="mt-4 space-y-3">
        {meetings.map((meeting) => meeting && (
          <div key={meeting.name} className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <div className="font-black text-slate-950">{meeting.title}</div>
            <div className="mt-1 text-xs font-semibold text-slate-500">{formatTimestamp(meeting.scheduled_at)} | {formatStatus(meeting.status)}</div>
            <div className="mt-2 text-xs font-semibold text-slate-600">{meeting.participants?.length || 0} participant(s)</div>
          </div>
        ))}
        {!meetings.length && <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm font-semibold text-slate-500">No ARD meetings yet.</div>}
      </div>
    </section>
  );
}

function TeamPanel({ workspace }: { workspace: ArdWorkspaceData }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500">
        <Users className="h-4 w-4" />
        ARD Team
      </div>
      <div className="mt-4 space-y-2">
        {workspace.team_members.map((member) => (
          <div key={member.user} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
            <div className="text-sm font-black text-slate-950">{member.full_name}</div>
            <div className="text-xs font-semibold text-slate-500">{member.is_project_owner ? "Project Owner" : member.business_role}</div>
          </div>
        ))}
        {!workspace.team_members.length && <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm font-semibold text-slate-500">No ARD team selected yet.</div>}
      </div>
    </section>
  );
}

function CompletedOutput({ displayData }: { displayData: Record<string, string | number> }) {
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "failed">("idle");
  const rows = Object.entries(displayData);

  async function copyPath(value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("failed");
    }
  }

  if (!rows.length) return null;
  return (
    <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3">
      <div className="flex items-center gap-2 text-sm font-black text-emerald-800">
        <CheckCircle2 className="h-4 w-4" />
        Completed output
      </div>
      {rows.map(([label, value]) => (
        <div key={label} className="mt-2 flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm">
          <span className="font-black text-slate-600">{label}</span>
          <span className="min-w-0 flex-1 truncate text-slate-950">{String(value)}</span>
          {label.toLowerCase().includes("path") && (
            <button className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-300" type="button" aria-label="Copy path" onClick={() => void copyPath(String(value))}>
              <Copy className="h-4 w-4" />
            </button>
          )}
        </div>
      ))}
      {copyStatus !== "idle" && (
        <div className={`mt-2 text-xs font-black ${copyStatus === "copied" ? "text-emerald-700" : "text-red-700"}`}>
          {copyStatus === "copied" ? "Copied" : "Copy failed"}
        </div>
      )}
    </div>
  );
}

function ActionButton({ children, disabled, loading, onClick }: { children: ReactNode; disabled?: boolean; loading?: boolean; onClick: () => void }) {
  return (
    <Button type="button" disabled={disabled || loading} onClick={onClick}>
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </Button>
  );
}

function StatusBadge({ status }: { status?: string | null }) {
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-bold ${statusBadgeClass(status)}`}>{formatStatus(status)}</span>;
}

function nodeCardClass(status?: string | null, canOpen = false) {
  const label = formatStatus(status);
  if (label === "Complete") return "border-green-300 bg-green-50 text-green-900";
  if (label.includes("Progress") || label === "In Progress") return "border-amber-300 bg-amber-50 text-amber-900";
  if (label === "Inactive Path") return "border-slate-950 bg-slate-950 text-white";
  if (canOpen) return "border-slate-300 bg-white text-slate-950 hover:bg-slate-50";
  return "border-slate-200 bg-slate-100 text-slate-500";
}

function formatTimestamp(value?: string) {
  if (!value) return "Not scheduled";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", {
    timeZone: "Africa/Cairo",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
