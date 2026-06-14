"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState, type CSSProperties, type ComponentType } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  Copy,
  Cpu,
  DatabaseZap,
  DoorOpen,
  FileInput,
  GitBranch,
  Loader2,
  Lock,
  PackageCheck,
  Route,
  ShieldCheck,
  Stamp,
  Users,
  X,
} from "lucide-react";
import { Button } from "@/components/Button";
import type { SafeUser, SrsFlowchartDefinition, SrsNodeDefinition, SrsNodeState, TrainerWorkspace as TrainerWorkspaceData } from "@/features/srs/types";
import {
  DEADLINE_BANDS,
  FLOWCHART_DIMENSIONS,
  LANE_BANDS,
  CONNECTOR_ROUTES,
  anchorPoint,
  formatDistance,
  formatNodeId,
  formatStatus,
  nodePosition,
  statusBadgeClass,
  statusTone,
} from "@/features/srs/workflowPresentation";

type NodeAvailability = TrainerWorkspaceData["node_availability"][number];
type FlowIcon = ComponentType<{ className?: string; style?: CSSProperties }>;

const placeholderText = "This workflow will be implemented in a later phase.";
const neverOpenNodeIds = new Set([
  "CASES_1_2",
  "CASES_3_4",
  "GM_APPROVAL",
  "GATE_1_SRS_MANAGER_APPROVAL",
  "DUAL_GATE_APPROVAL",
  "PMDP_DUAL_GATE_APPROVAL",
  "EXTENSION_DEADLINE",
  "SRS_DIRECTOR_APPROVAL",
  "FINAL_GM_APPROVAL",
  "ACTION_PATHS",
  "DEADLINE_LOCKED_IN_ERP",
  "CASE_1",
  "CASE_2",
  "CASE_3",
  "CASE_4",
]);

export function TrainerWorkspace({
  initialWorkspace,
  flowchart
}: {
  session: unknown;
  initialWorkspace: TrainerWorkspaceData;
  flowchart: SrsFlowchartDefinition;
}) {
  const [workspace, setWorkspace] = useState(initialWorkspace);
  const [activeTab, setActiveTab] = useState(initialWorkspace.tabs[0] || "SRS");
  const [activeNode, setActiveNode] = useState<string | null>(null);

  const states = useMemo(() => {
    return new Map(workspace.node_states.map((state) => [state.node_id, state]));
  }, [workspace.node_states]);

  const activeDeadline = workspace.node_states.find((state) => isActiveDeadlineState(state));
  const currentStage = currentStageLabel(workspace);

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-bold uppercase text-muted">{workspace.project.project_code}</div>
            <h1 className="mt-2 text-3xl font-bold text-ink">{workspace.trainer_item.trainer_item_name}</h1>
            <p className="mt-2 text-sm text-muted">
              Quantity {workspace.trainer_item.quantity} | Current step: {currentStage}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <StatusBadge status={workspace.trainer_item.status} />
            {activeDeadline && (
              <CountdownBadge startAt={activeDeadline.deadline_start_at} dueAt={activeDeadline.deadline_due_at} serverNow={workspace.server_now} />
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        {workspace.tabs.map((tab) => (
          <button
            key={tab}
            className={`focus-ring inline-flex items-center gap-2 rounded-t-lg border px-4 py-2 text-sm font-black transition ${
              activeTab === tab ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
            type="button"
            onClick={() => setActiveTab(tab)}
          >
            <span className={`h-2 w-2 rounded-full ${activeTab === tab ? "bg-amber-400" : "bg-slate-300"}`} />
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Overview" && <Overview workspace={workspace} />}
      {activeTab === "Audit Log" && <AuditLog workspace={workspace} />}
      {activeTab === "SRS" && (
        <SrsFlowchart
          workspace={workspace}
          setWorkspace={setWorkspace}
          flowchart={flowchart}
          states={states}
          activeNode={activeNode}
          setActiveNode={setActiveNode}
        />
      )}
      {activeTab !== "Overview" && activeTab !== "SRS" && activeTab !== "Audit Log" && (
        <div className="rounded-md border border-gray-200 bg-white p-8 text-sm font-semibold text-muted shadow-panel">{placeholderText}</div>
      )}
    </section>
  );
}

function currentStageLabel(workspace: TrainerWorkspaceData) {
  const status = workspace.workflow?.status || workspace.trainer_item.status;
  if (status === "SRS_COMPLETE" || status === "COMPLETED" || status === "COMPLETE") return "Completed";
  return formatNodeId(workspace.workflow?.current_node || workspace.trainer_item.current_node);
}

function Overview({ workspace }: { workspace: TrainerWorkspaceData }) {
  const projectOwner = workspace.team_members.find((member) => member.is_project_owner);
  const selectedTeam = workspace.team_members.filter((member) => !member.is_project_owner);
  const activeDeadline = workspace.deadlines.find((deadline) => deadline.status === "ACTIVE");
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <InfoCard
        title="Project"
        rows={[
          ["Code", workspace.project.project_code],
          ["Name", workspace.project.project_name],
          ["End User", workspace.project.end_user],
          ["PO Deadline", workspace.project.po_deadline_date],
          ["Status", formatStatus(workspace.project.status)],
        ]}
      />
      <InfoCard
        title="SRS Summary"
        rows={[
          ["Name", workspace.trainer_item.trainer_item_name],
          ["Quantity", String(workspace.trainer_item.quantity)],
          ["Project Owner", projectOwner?.full_name || workspace.workflow?.project_owner || "-"],
          ["Selected Team", selectedTeam.length ? `${selectedTeam.length} member(s)` : "-"],
          ["Current Node", formatNodeId(workspace.workflow?.current_node || workspace.trainer_item.current_node)],
          ["Current Deadline", activeDeadline?.due_at || "No active deadline"],
          ["Status", formatStatus(workspace.trainer_item.status)],
        ]}
      />
      <InfoCard
        title="Recent Activity"
        rows={(workspace.audit_events.slice(0, 5).map((event) => [
          formatStatus(event.event_type),
          [event.message, event.created_at].filter(Boolean).join(" | ") || "-",
        ]) as Array<[string, string]>).concat(workspace.audit_events.length ? [] : [["Activity", "No audit events yet."]])}
      />
    </div>
  );
}

function InfoCard({ title, rows }: { title: string; rows: Array<[string, string]> }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
      <h2 className="text-lg font-bold text-ink">{title}</h2>
      <dl className="mt-4 grid gap-3">
        {rows.map(([label, value]) => (
          <div key={label} className="grid grid-cols-[140px_1fr] gap-3 text-sm">
            <dt className="font-semibold text-muted">{label}</dt>
            <dd className="text-ink">{value || "-"}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function AuditLog({ workspace }: { workspace: TrainerWorkspaceData }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
      <h2 className="text-lg font-bold text-ink">Audit Log</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-muted">
            <tr>
              <th className="rounded-l-md px-3 py-3">Event</th>
              <th className="px-3 py-3">Actor</th>
              <th className="px-3 py-3">Node</th>
              <th className="px-3 py-3">Message</th>
              <th className="rounded-r-md px-3 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {workspace.audit_events.map((event) => (
              <tr key={`${event.event_type}-${event.created_at}`} className="border-b border-gray-100">
                <td className="px-3 py-3 font-medium text-ink">{formatStatus(event.event_type)}</td>
                <td className="px-3 py-3 text-muted">{event.user}</td>
                <td className="px-3 py-3">{formatNodeId(event.node_id)}</td>
                <td className="px-3 py-3 text-muted">{event.message || "-"}</td>
                <td className="px-3 py-3 text-muted">{event.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!workspace.audit_events.length && <div className="rounded-md border border-dashed border-gray-300 p-6 text-sm text-muted">No audit events yet.</div>}
      </div>
    </div>
  );
}

function SrsFlowchart({
  workspace,
  setWorkspace,
  flowchart,
  states,
  activeNode,
  setActiveNode
}: {
  workspace: TrainerWorkspaceData;
  setWorkspace: (workspace: TrainerWorkspaceData) => void;
  flowchart: SrsFlowchartDefinition;
  states: Map<string, SrsNodeState>;
  activeNode: string | null;
  setActiveNode: (node: string | null) => void;
}) {
  const now = useServerClock(workspace.server_now);
  const frameRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const availability = useMemo(() => new Map(workspace.node_availability.map((node) => [node.nodeId, node])), [workspace.node_availability]);
  const flowchartNodeIds = useMemo(() => new Set(flowchart.nodes.map((node) => node.id)), [flowchart.nodes]);
  const diagramWidth = FLOWCHART_DIMENSIONS.laneLabelWidth + FLOWCHART_DIMENSIONS.canvasWidth;
  const diagramHeight = FLOWCHART_DIMENSIONS.deadlineHeaderHeight + FLOWCHART_DIMENSIONS.canvasHeight;
  const deadlineColumnMeta = useMemo(() => new Map(flowchart.deadline_columns.map((column) => [column.id, column])), [flowchart.deadline_columns]);
  const notApplicableNodeIds = new Set(workspace.node_states.filter((state) => state.status === "NOT_APPLICABLE").map((state) => state.node_id));
  const applicableNodeCount = flowchart.nodes.filter((node) => !notApplicableNodeIds.has(node.id)).length;
  const completeCount = workspace.node_states.filter((state) => flowchartNodeIds.has(state.node_id) && state.status === "COMPLETED" && !notApplicableNodeIds.has(state.node_id)).length;
  const progress = applicableNodeCount ? Math.round((completeCount / applicableNodeCount) * 100) : 0;
  const activeDeadlineState = workspace.node_states.find((state) => flowchartNodeIds.has(state.node_id) && isActiveDeadlineState(state));

  useLayoutEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const availableWidth = frame.clientWidth;
      setScale(Math.min(1, availableWidth / diagramWidth));
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [diagramWidth]);

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4 shadow-panel md:p-5">
      <div className="mb-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-900 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">SRS Workflow</p>
            <h2 className="mt-1 text-lg font-bold text-white">{workspace.trainer_item.trainer_item_name}</h2>
            <p className="text-xs text-slate-300">{workspace.project.project_code} | {workspace.project.end_user}</p>
          </div>
          {activeDeadlineState ? (
            <CountdownBadge startAt={activeDeadlineState.deadline_start_at} dueAt={activeDeadlineState.deadline_due_at} serverNow={workspace.server_now} now={now} />
          ) : (
            <StatusBadge status={workspace.workflow?.status || workspace.trainer_item.status} />
          )}
        </div>

        <div className="grid grid-cols-2 gap-px bg-slate-100 lg:grid-cols-4">
          <HeaderStat label="Trainer Item" value={workspace.trainer_item.trainer_item_name} />
          <HeaderStat label="Current Stage" value={currentStageLabel(workspace)} />
          <HeaderStat label="Status" value={formatStatus(workspace.workflow?.status || workspace.trainer_item.status)} tone={statusTone(workspace.workflow?.status || workspace.trainer_item.status)} />
          <HeaderStatProgress label="SRS Progress" value={progress} />
        </div>
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border border-slate-200 bg-white px-4 py-3">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Legend</span>
        {(["complete", "in-progress", "pending", "awaiting-approval", "locked", "not-applicable", "overdue"] as const).map((tone) => (
          <span key={tone} className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: TONE_STYLES[tone].dot }} />
            <span className="text-xs font-medium text-slate-600">{TONE_STYLES[tone].label}</span>
          </span>
        ))}
      </div>

      <div
        ref={frameRef}
        className="overflow-hidden rounded-md border border-slate-200 bg-white"
        style={{
          backgroundColor: "#f8fafc",
          backgroundImage:
            "linear-gradient(to right, rgba(148,163,184,0.10) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.10) 1px, transparent 1px)",
          backgroundSize: `${32 * scale}px ${32 * scale}px`,
        }}
      >
        <div style={{ minWidth: diagramWidth * scale, width: "100%", height: diagramHeight * scale }}>
          <div style={{ width: diagramWidth, transform: `scale(${scale})`, transformOrigin: "top left" }}>
            <div className="flex border-b border-slate-200 bg-slate-100">
              <div className="shrink-0 border-r border-slate-200" style={{ width: FLOWCHART_DIMENSIONS.laneLabelWidth }} />
              <div className="relative" style={{ width: FLOWCHART_DIMENSIONS.canvasWidth, height: FLOWCHART_DIMENSIONS.deadlineHeaderHeight }}>
                {DEADLINE_BANDS.map((column, index) => (
                  <div
                    key={column.id}
                    className={`absolute top-0 h-full ${index > 0 ? "border-l border-slate-300" : ""}`}
                    style={{ left: column.x, width: column.w }}
                  >
                    <DeadlineHeader label={deadlineColumnMeta.get(column.id)?.label || column.label} detail={deadlineColumnMeta.get(column.id)?.detail || column.detail} />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex">
              <div className="relative shrink-0 border-r border-slate-200" style={{ width: FLOWCHART_DIMENSIONS.laneLabelWidth, height: FLOWCHART_DIMENSIONS.canvasHeight }}>
                {LANE_BANDS.map((lane, index) => (
                  <div
                    key={lane.id}
                    className={`absolute left-0 flex w-full items-center justify-center px-4 text-center ${index > 0 ? "border-t border-slate-700/40" : ""}`}
                    style={{ top: lane.y, height: lane.h, backgroundColor: index % 2 === 0 ? "#1e293b" : "#0f172a" }}
                  >
                    <span className="text-[13px] font-semibold uppercase tracking-wide text-slate-100">{lane.label}</span>
                  </div>
                ))}
              </div>

              <div
                className="relative"
                style={{
                  width: FLOWCHART_DIMENSIONS.canvasWidth,
                  height: FLOWCHART_DIMENSIONS.canvasHeight,
                  backgroundColor: "#f8fafc",
                  backgroundImage:
                    "linear-gradient(to right, rgba(148,163,184,0.10) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.10) 1px, transparent 1px)",
                  backgroundSize: "32px 32px",
                }}
              >
                {LANE_BANDS.map((lane, index) => (
                  <div
                    key={lane.id}
                    className="absolute left-0 w-full"
                    style={{
                      top: lane.y,
                      height: lane.h,
                      backgroundColor: index % 2 === 1 ? "rgba(148,163,184,0.05)" : "transparent",
                      borderTop: index > 0 ? "1px dashed rgba(148,163,184,0.45)" : "none",
                    }}
                  />
                ))}

                {DEADLINE_BANDS.map((column, index) => (
                  <div
                    key={column.id}
                    className={`absolute top-0 h-full ${index > 0 ? "border-l border-dashed border-slate-300" : ""}`}
                    style={{
                      left: column.x,
                      width: column.w,
                      backgroundColor: index % 2 === 0 ? "rgba(241,245,249,0.55)" : "rgba(255,255,255,0.44)",
                    }}
                  />
                ))}

                <svg className="pointer-events-none absolute inset-0" width={FLOWCHART_DIMENSIONS.canvasWidth} height={FLOWCHART_DIMENSIONS.canvasHeight}>
                  <defs>
                    <marker id="srs-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
                    </marker>
                  </defs>
                  {flowchart.edges.map((edge) => {
                    const path = edgePath(edge.from, edge.to);
                    const sourceStatus = states.get(edge.from)?.status;
                    const targetStatus = states.get(edge.to)?.status;
                    const notApplicable = sourceStatus === "NOT_APPLICABLE" || targetStatus === "NOT_APPLICABLE";
                    const active = sourceStatus === "COMPLETED" && !notApplicable;
                    return (
                      <path
                        key={`${edge.from}-${edge.to}`}
                        d={path}
                        fill="none"
                        markerEnd="url(#srs-arrow)"
                        stroke={notApplicable ? "#020617" : active ? "#16a34a" : "#94a3b8"}
                        strokeDasharray={notApplicable ? "2 7" : undefined}
                        opacity={notApplicable ? 0.5 : 1}
                        strokeLinecap="round"
                        strokeWidth={active ? 2.5 : 1.75}
                      />
                    );
                  })}
                </svg>

                {activeDeadlineState && (
                  <div className="absolute" style={countdownPosition(activeDeadlineState.node_id)}>
                    <CountdownBadge
                      startAt={activeDeadlineState.deadline_start_at}
                      dueAt={activeDeadlineState.deadline_due_at}
                      serverNow={workspace.server_now}
                      now={now}
                      compact
                    />
                  </div>
                )}

                {flowchart.nodes.map((node) => {
                  const state = states.get(node.id);
                  const available = availability.get(node.id);
                  return (
                    <FlowNode
                      key={node.id}
                      node={node}
                      state={state}
                      availability={available}
                      now={now}
                      onOpen={() => {
                        if (canOpenNodeModal(node, state, available)) setActiveNode(node.id);
                      }}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {activeNode && (
        <NodeModal
          nodeId={activeNode}
          workspace={workspace}
          flowchart={flowchart}
          state={states.get(activeNode)}
          availability={availability.get(activeNode)}
          onClose={() => setActiveNode(null)}
          onUpdated={(next) => {
            setWorkspace(next);
            setActiveNode(null);
          }}
        />
      )}
    </div>
  );
}

function HeaderStat({ label, value, tone }: { label: string; value: string; tone?: ReturnType<typeof statusTone> }) {
  return (
    <div className="bg-white px-5 py-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-0.5 truncate text-sm font-semibold" style={{ color: tone ? TONE_STYLES[tone].chipText : "#1e293b" }}>
        {value || "-"}
      </p>
    </div>
  );
}

function HeaderStatProgress({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white px-5 py-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</p>
        <span className="text-xs font-bold text-slate-700">{value}%</span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-slate-800" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
    </div>
  );
}

function DeadlineHeader({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-0.5 px-3 text-center">
      <span className="text-[13px] font-bold uppercase tracking-wide text-slate-700">{label}</span>
      <span className="text-[11px] font-medium text-slate-500">{detail}</span>
    </div>
  );
}

const TONE_STYLES: Record<ReturnType<typeof statusTone>, { label: string; dot: string; chipBg: string; chipText: string; border: string; bg: string; accent: string; title: string }> = {
  complete: {
    label: "Complete",
    dot: "#16a34a",
    chipBg: "rgba(22,163,74,0.12)",
    chipText: "#15803d",
    border: "#16a34a",
    bg: "#f0fdf4",
    accent: "#16a34a",
    title: "#14532d",
  },
  "in-progress": {
    label: "In Progress",
    dot: "#d97706",
    chipBg: "rgba(217,119,6,0.14)",
    chipText: "#b45309",
    border: "#d97706",
    bg: "#fffbeb",
    accent: "#d97706",
    title: "#7c2d12",
  },
  pending: {
    label: "Pending",
    dot: "#64748b",
    chipBg: "rgba(100,116,139,0.14)",
    chipText: "#475569",
    border: "#cbd5e1",
    bg: "#f8fafc",
    accent: "#94a3b8",
    title: "#475569",
  },
  "awaiting-approval": {
    label: "Awaiting Approval",
    dot: "#2563eb",
    chipBg: "rgba(37,99,235,0.12)",
    chipText: "#1d4ed8",
    border: "#2563eb",
    bg: "#eff6ff",
    accent: "#2563eb",
    title: "#1e3a8a",
  },
  locked: {
    label: "Locked",
    dot: "#94a3b8",
    chipBg: "rgba(148,163,184,0.16)",
    chipText: "#64748b",
    border: "#cbd5e1",
    bg: "#f8fafc",
    accent: "#94a3b8",
    title: "#475569",
  },
  "not-applicable": {
    label: "Inactive Path",
    dot: "#020617",
    chipBg: "rgba(15,23,42,0.78)",
    chipText: "#e2e8f0",
    border: "#020617",
    bg: "#020617",
    accent: "#64748b",
    title: "#cbd5e1",
  },
  overdue: {
    label: "Overdue",
    dot: "#dc2626",
    chipBg: "rgba(220,38,38,0.12)",
    chipText: "#b91c1c",
    border: "#dc2626",
    bg: "#fef2f2",
    accent: "#dc2626",
    title: "#7f1d1d",
  },
};

const STATUS_ICONS: Record<ReturnType<typeof statusTone>, FlowIcon> = {
  complete: CheckCircle2,
  "in-progress": Loader2,
  pending: Clock3,
  "awaiting-approval": ShieldCheck,
  locked: Lock,
  "not-applicable": X,
  overdue: AlertTriangle,
};

const NODE_ICONS: Record<string, FlowIcon> = {
  PRODUCT_DIGITAL_RELEASE: PackageCheck,
  SRS_GATEWAY: DoorOpen,
  MANDATORY_COORDINATION_MEETING: Users,
  DELIVERABLES_MATRIX: ClipboardList,
  DUAL_GATE_APPROVAL: ShieldCheck,
  CASES_1_2: GitBranch,
  CASES_3_4: GitBranch,
  GM_APPROVAL: Stamp,
  GATE_1_SRS_MANAGER_APPROVAL: ShieldCheck,
  DEADLINE_LOCKED_IN_ERP: DatabaseZap,
  ACTION_PATHS: Route,
  CASE_1: GitBranch,
  CASE_2: GitBranch,
  CASE_3: GitBranch,
  CASE_4: GitBranch,
  GATE_2_PMDP: FileInput,
  PMDP_DUAL_GATE_APPROVAL: ShieldCheck,
  PHYSICAL_BUILD_TEST: Cpu,
  EXTENSION_DEADLINE: Clock3,
  SRS_DIRECTOR_APPROVAL: ShieldCheck,
  PMDP: FileInput,
  BMDP: Cpu,
  COMMAND_CENTER_APPROVAL: ClipboardCheck,
  FINAL_GM_APPROVAL: Stamp,
};

const NODE_SUBTITLES: Record<string, string> = {
  SRS_GATEWAY: "Assign Project Owner via ERP",
  MANDATORY_COORDINATION_MEETING: "SRS team selection",
  DELIVERABLES_MATRIX: "Case classification + deadline proposal",
  DUAL_GATE_APPROVAL: "SRS Manager first, GM only when required",
  CASE_1: "Legacy Validation",
  CASE_2: "Standard Innovation",
  CASE_3: "Experimental Prototyping",
  CASE_4: "Vanguard Manufacturing",
  GATE_2_PMDP: "Submit Gate 2 PMDP path",
  PMDP_DUAL_GATE_APPROVAL: "SRS + Pillar 4 approval",
  PHYSICAL_BUILD_TEST: "Request extension if needed",
  EXTENSION_DEADLINE: "Extension request",
  SRS_DIRECTOR_APPROVAL: "SRS extension approval",
  PMDP: "Submit PMDP path",
  BMDP: "Submit BMDP path",
  COMMAND_CENTER_APPROVAL: "Command Center case + deadline",
  FINAL_GM_APPROVAL: "Final SRS completion approval",
};

function edgePath(fromId: string, toId: string) {
  const route = CONNECTOR_ROUTES[`${fromId}->${toId}`] || { fromSide: "right" as const, toSide: "left" as const };
  const start = anchorPoint(fromId, route.fromSide);
  const end = anchorPoint(toId, route.toSide);
  const points = route.points || defaultOrthogonalPoints(start, end, route.fromSide, route.toSide);
  return [`M ${start.x} ${start.y}`, ...points.map((point) => `L ${point.x} ${point.y}`), `L ${end.x} ${end.y}`].join(" ");
}

function defaultOrthogonalPoints(start: { x: number; y: number }, end: { x: number; y: number }, fromSide: string, toSide: string) {
  if (start.x === end.x || start.y === end.y) return [];
  if ((fromSide === "left" || fromSide === "right") && (toSide === "left" || toSide === "right")) {
    const midX = Math.round((start.x + end.x) / 2);
    return [{ x: midX, y: start.y }, { x: midX, y: end.y }];
  }
  if ((fromSide === "top" || fromSide === "bottom") && (toSide === "top" || toSide === "bottom")) {
    const midY = Math.round((start.y + end.y) / 2);
    return [{ x: start.x, y: midY }, { x: end.x, y: midY }];
  }
  return [{ x: end.x, y: start.y }];
}

function countdownPosition(nodeId: string) {
  const position = nodePosition({ id: nodeId } as SrsNodeDefinition);
  return { left: position.x, top: Math.max(8, position.y - 36) };
}

function canOpenNodeModal(node: SrsNodeDefinition, state?: SrsNodeState, availability?: NodeAvailability) {
  if (neverOpenNodeIds.has(node.id)) return false;
  if (state?.status === "NOT_APPLICABLE") return false;
  if (state?.status === "COMPLETED") return true;
  return Boolean(node.clickable && availability?.canOpen);
}

function FlowNode({
  node,
  state,
  availability,
  now,
  onOpen,
}: {
  node: SrsNodeDefinition;
  state?: SrsNodeState;
  availability?: NodeAvailability;
  now: Date;
  onOpen: () => void;
}) {
  const position = nodePosition(node);
  const overdue = isDeadlineOverdue(state, now);
  const status = overdue ? "OVERDUE" : state?.status || "LOCKED";
  const isComplete = status === "COMPLETED";
  const isInactivePath = status === "NOT_APPLICABLE";
  const canOpen = canOpenNodeModal(node, state, availability);
  const canAct = Boolean(availability?.canOpen) && !isComplete && !isInactivePath;
  const tone = statusTone(status);
  const style = TONE_STYLES[tone];
  const StatusIcon = STATUS_ICONS[tone];
  const NodeIcon = NODE_ICONS[node.id] || Route;
  const subtitle = NODE_SUBTITLES[node.id];
  const showSubtitle = Boolean(subtitle && !isComplete && !isInactivePath);
  const summary = nodeCardSummary(node.id, state);
  const content = (
    <>
      <span className="absolute bottom-2 left-0 top-2 w-1 rounded-full" style={{ backgroundColor: style.accent }} />
      <div className={`flex items-start gap-2 pl-1.5 ${isInactivePath ? "opacity-30 blur-[1.2px]" : ""}`}>
        <NodeIcon className="mt-0.5 h-4 w-4 shrink-0" style={{ color: style.accent }} />
        <div className="min-w-0">
          <div className="whitespace-normal break-words text-[12.5px] font-semibold leading-snug" style={{ color: style.title }}>
          {node.label}
          </div>
          {showSubtitle && <div className="mt-0.5 whitespace-normal break-words text-[10.5px] leading-snug text-slate-500">{subtitle}</div>}
          {summary && <div className="mt-1 truncate text-[10.5px] font-bold leading-snug text-slate-700" title={summary}>{summary}</div>}
        </div>
      </div>
      <div className={`mt-1.5 pl-1.5 ${isInactivePath ? "opacity-30 blur-[1.2px]" : ""}`}>
        <span className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium leading-none" style={{ backgroundColor: style.chipBg, color: style.chipText }}>
          <StatusIcon className={`h-3 w-3 ${tone === "in-progress" ? "animate-spin" : ""}`} />
          {formatStatus(status)}
        </span>
      </div>
      {isInactivePath && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-slate-950/70">
          <span className="rounded-full border border-white/15 bg-white/10 px-2.5 py-1 text-[10px] font-black uppercase tracking-wide text-slate-200">Inactive path</span>
        </div>
      )}
      {!canOpen && availability?.disabledReason && node.clickable && !isInactivePath && (
        <div className="mt-1.5 whitespace-normal break-words pl-1.5 text-[11px] font-medium leading-tight text-slate-500">{availability.disabledReason}</div>
      )}
    </>
  );

  const className = `absolute flex flex-col justify-center rounded-xl border px-3 py-2 text-left transition-all ${
    canOpen ? "cursor-pointer hover:-translate-y-0.5 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-amber-400" : "cursor-default"
  }`;
  const styleProps = {
    left: position.x,
    top: position.y,
    width: position.w,
    height: position.h,
    borderColor: style.border,
    backgroundColor: style.bg,
    boxShadow: isInactivePath
      ? "inset 0 0 0 1px rgba(255,255,255,0.08), 0 8px 18px rgba(2,6,23,0.25)"
      : tone === "in-progress" || tone === "awaiting-approval"
        ? "0 4px 14px rgba(217,119,6,0.20)"
        : "0 1px 3px rgba(15,23,42,0.08)",
    filter: isInactivePath ? "grayscale(1)" : undefined,
  };

  if (canOpen) {
    return (
      <button
        className={className}
        style={styleProps}
        type="button"
        onClick={onOpen}
        title={canAct ? node.label : `${node.label} output`}
      >
        {content}
      </button>
    );
  }

  return (
    <div
      className={className}
      style={styleProps}
      title={availability?.disabledReason || "Display-only step"}
    >
      {content}
    </div>
  );
}

function nodeCardSummary(nodeId: string, state?: SrsNodeState) {
  if (state?.status === "COMPLETED") return "";
  if (nodeId === "DEADLINE_LOCKED_IN_ERP") {
    const value = state?.display_data?.["Locked Deadline"];
    return value ? `Deadline: ${String(value)}` : "";
  }
  return "";
}

function NodeModal({
  nodeId,
  workspace,
  flowchart,
  state,
  availability,
  onClose,
  onUpdated
}: {
  nodeId: string;
  workspace: TrainerWorkspaceData;
  flowchart: SrsFlowchartDefinition;
  state?: SrsNodeState;
  availability?: NodeAvailability;
  onClose: () => void;
  onUpdated: (workspace: TrainerWorkspaceData) => void;
}) {
  const [owners, setOwners] = useState<Record<string, SafeUser[]> | null>(null);
  const [teamMembers, setTeamMembers] = useState<SafeUser[]>([]);
  const [error, setError] = useState("");
  const node = flowchart.nodes.find((candidate) => candidate.id === nodeId);
  const readOnly = state?.status === "COMPLETED";
  const modalDeadlineState = state && isActiveDeadlineState(state) ? state : undefined;

  async function loadOwners() {
    if (owners) return;
    const response = await fetch("/api/srs/project-owners");
    if (response.ok) setOwners((await response.json()).groups);
  }

  async function loadTeamMembers() {
    if (teamMembers.length) return;
    const response = await fetch("/api/srs/team-members");
    if (response.ok) setTeamMembers((await response.json()).users || []);
  }

  async function submit(action: string, payload: Record<string, unknown>) {
    setError("");
    const response = await fetch("/api/srs/workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, trainer_item: workspace.trainer_item.name, ...payload })
    });
    if (!response.ok) {
      const message = await response.json().catch(() => null);
      setError(message?.error || "Action could not be completed. Check permissions and workflow state.");
      return;
    }
    onUpdated(await response.json());
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4">
      <div className="flex max-h-[88vh] w-full max-w-3xl flex-col rounded-md bg-white shadow-xl">
        <div className="border-b border-gray-200 px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs font-bold uppercase text-muted">{readOnly ? "Workflow Output" : "SRS Action"}</div>
              <h3 className="mt-1 text-xl font-bold text-ink">{node?.label || nodeId}</h3>
            </div>
            <button className="focus-ring rounded-md p-2 hover:bg-gray-100" type="button" onClick={onClose} aria-label="Close">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="mt-4 grid gap-3 rounded-md border border-gray-200 bg-panel p-3 text-sm sm:grid-cols-3">
            <div>
              <div className="text-xs font-bold uppercase text-muted">Project</div>
              <div className="mt-1 font-semibold text-ink">{workspace.project.project_code}</div>
            </div>
            <div>
              <div className="text-xs font-bold uppercase text-muted">Trainer Item</div>
              <div className="mt-1 font-semibold text-ink">{workspace.trainer_item.trainer_item_name}</div>
            </div>
            <div>
              <div className="text-xs font-bold uppercase text-muted">Status</div>
              <div className="mt-1">
                <StatusBadge status={state?.status || workspace.workflow?.status} />
              </div>
            </div>
          </div>
          {modalDeadlineState && (
            <div className="mt-3">
              <CountdownBadge startAt={modalDeadlineState.deadline_start_at} dueAt={modalDeadlineState.deadline_due_at} serverNow={workspace.server_now} />
            </div>
          )}
        </div>
        <div className="min-h-0 overflow-y-auto px-6 py-5">
          {error && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">{error}</div>}
          {readOnly ? (
            <NodeOutputSummary nodeId={nodeId} state={state} workspace={workspace} />
          ) : availability?.canOpen ? (
            <>
              {nodeId === "SRS_GATEWAY" && (
            <OwnerForm owners={owners} loadOwners={loadOwners} onSubmit={(project_owner) => submit("assign_owner", { project_owner })} />
              )}
              {nodeId === "MANDATORY_COORDINATION_MEETING" && (
            <TeamForm
              teamMembers={teamMembers}
              loadTeamMembers={loadTeamMembers}
              onSubmit={(users) => submit("select_team", { users })}
            />
              )}
              {nodeId === "DELIVERABLES_MATRIX" && (
            <DeliverablesForm cases={flowchart.case_classifications} onSubmit={(payload) => submit("submit_deliverables", payload)} />
              )}
              {nodeId === "GATE_2_PMDP" && <PathSubmissionForm label="Gate 2 PMDP Path" submitLabel="Submit Gate 2 PMDP Path" fieldName="pmdp_path" onSubmit={(pmdp_path) => submit("submit_pmdp_gate", { pmdp_path })} />}
              {nodeId === "PHYSICAL_BUILD_TEST" && <ExtensionRequestForm unitLabel={workspace.deadline_unit_label || "minutes"} onSubmit={(payload) => submit("request_pmdp_extension", payload)} />}
              {nodeId === "PMDP" && <PathSubmissionForm label="PMDP Path" submitLabel="Submit PMDP Path" fieldName="pmdp_path" onSubmit={(pmdp_path) => submit("submit_pmdp", { pmdp_path })} />}
              {nodeId === "BMDP" && <PathSubmissionForm label="BMDP Path" submitLabel="Submit BMDP Path" fieldName="bmdp_path" onSubmit={(bmdp_path) => submit("submit_bmdp", { bmdp_path })} />}
              {nodeId === "COMMAND_CENTER_APPROVAL" && <CommandCenterForm onSubmit={(payload) => submit("submit_command_center", payload)} />}
            </>
          ) : (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-5 text-sm font-semibold text-slate-600">
              {availability?.disabledReason || "This workflow step is not available."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

type OutputRow = {
  label: string;
  value: string;
  list?: string[];
  copyable?: boolean;
};

function NodeOutputSummary({ nodeId, state, workspace }: { nodeId: string; state?: SrsNodeState; workspace: TrainerWorkspaceData }) {
  const rows = nodeOutputRows(nodeId, state, workspace);
  const showCompletionBanner = nodeId !== "MANDATORY_COORDINATION_MEETING";
  return (
    <div className="space-y-4">
      {showCompletionBanner && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-black text-emerald-800">
            <CheckCircle2 className="h-4 w-4" />
            Step complete
          </div>
          <p className="mt-1 text-sm font-medium text-emerald-900/80">Recorded workflow output is shown below.</p>
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        {rows.map((row) => <OutputCard key={row.label} row={row} />)}
      </div>
    </div>
  );
}

function OutputCard({ row }: { row: OutputRow }) {
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
              if (row.value) void navigator.clipboard?.writeText(row.value);
            }}
            title="Copy path"
            aria-label="Copy path"
          >
            <Copy className="h-4 w-4" />
          </button>
        </div>
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

function nodeOutputRows(nodeId: string, state: SrsNodeState | undefined, workspace: TrainerWorkspaceData): OutputRow[] {
  const completedBy = state?.last_action_by_name || state?.last_action_by || state?.responsible_name || state?.responsible_user || "-";

  if (nodeId === "MANDATORY_COORDINATION_MEETING") {
    const selectedMembers = workspace.team_members.filter((member) => !member.is_project_owner).map((member) => member.full_name || member.user);
    const projectOwner = workspace.team_members.find((member) => member.is_project_owner);
    return [
      { label: "Selected Team Members", value: "", list: selectedMembers },
      { label: "Completed By", value: projectOwner?.full_name || projectOwner?.user || workspace.workflow?.project_owner || completedBy },
    ];
  }

  const displayRows = Object.entries(state?.display_data || {})
    .filter(([, value]) => value !== "" && value !== undefined && value !== null)
    .map(([label, value]) => ({
      label,
      value: String(value),
      copyable: label.toLowerCase().includes("path"),
    }));

  const rows: OutputRow[] = [...displayRows];
  if (nodeId !== "SRS_GATEWAY" && state?.completed_at) rows.push({ label: "Completed At", value: formatWorkflowTimestamp(state.completed_at) });
  rows.push({ label: "Completed By", value: completedBy });
  return rows.length ? rows : [{ label: "Completed By", value: completedBy }];
}

function formatWorkflowTimestamp(value?: string) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const datePart = date.toLocaleDateString("en-US", {
    timeZone: "Africa/Cairo",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const timePart = date.toLocaleTimeString("en-US", {
    timeZone: "Africa/Cairo",
    hour: "numeric",
    minute: "2-digit",
  });
  return `${datePart} at ${timePart}`;
}

function OwnerForm({ owners, loadOwners, onSubmit }: { owners: Record<string, SafeUser[]> | null; loadOwners: () => void; onSubmit: (projectOwner: string) => void }) {
  const [selected, setSelected] = useState("");
  useEffect(() => {
    void loadOwners();
  }, []);
  return (
    <div className="space-y-4">
      {Object.entries(owners || {}).map(([group, users]) => (
        <section key={group} className="rounded-md border border-gray-200 bg-panel p-3">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="text-xs font-bold uppercase text-muted">{group}</div>
            <span className="rounded bg-white px-2 py-1 text-xs font-semibold text-muted">{users.length}</span>
          </div>
          <div className="grid max-h-64 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
            {users.map((user) => (
              <label
                key={user.user}
                className={`flex cursor-pointer items-start gap-3 rounded-md border bg-white p-3 transition ${
                  selected === user.user ? "border-ember ring-2 ring-orange-100" : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <input className="mt-1 accent-ember" name="project_owner" type="radio" checked={selected === user.user} onChange={() => setSelected(user.user)} />
                <span>
                  <span className="block font-semibold text-ink">{user.full_name}</span>
                  <span className="text-xs text-muted">{user.business_role || "BEDO User"} | {user.department}</span>
                </span>
              </label>
            ))}
          </div>
        </section>
      ))}
      <Button type="button" disabled={!selected} onClick={() => onSubmit(selected)}>Assign Project Owner</Button>
    </div>
  );
}

function TeamForm({
  teamMembers,
  loadTeamMembers,
  onSubmit,
}: {
  teamMembers: SafeUser[];
  loadTeamMembers: () => void;
  onSubmit: (users: string[]) => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  useEffect(() => {
    void loadTeamMembers();
  }, []);
  const groupedMembers = useMemo(() => groupSrsUsers(teamMembers), [teamMembers]);
  return (
    <div className="space-y-4">
      <div className="sticky top-0 z-10 flex items-center justify-between gap-3 rounded-md border border-gray-200 bg-white px-3 py-2 shadow-sm">
        <div>
          <div className="text-sm font-bold text-ink">Select SRS team members</div>
          <div className="text-xs text-muted">Grouped by section and department role.</div>
        </div>
        <span className="rounded bg-orange-50 px-2 py-1 text-xs font-bold text-ink">{selected.length} selected</span>
      </div>
      <div className="grid max-h-[52vh] gap-3 overflow-y-auto pr-1">
        {groupedMembers.map((group) => (
          <section key={group.label} className="rounded-md border border-gray-200 bg-panel p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-bold text-ink">{group.label}</div>
                <div className="text-xs text-muted">{group.department}</div>
              </div>
              <span className="rounded bg-white px-2 py-1 text-xs font-semibold text-muted">{group.users.length}</span>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {group.users.map((user) => (
                <label
                  key={user.user}
                  className={`flex cursor-pointer items-start gap-3 rounded-md border bg-white p-3 transition ${
                    selected.includes(user.user) ? "border-ember ring-2 ring-orange-100" : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <input
                    className="mt-1 accent-ember"
                    type="checkbox"
                    checked={selected.includes(user.user)}
                    onChange={(event) => setSelected((current) => event.target.checked ? [...current, user.user] : current.filter((value) => value !== user.user))}
                  />
                  <span className="min-w-0">
                    <span className="block truncate font-semibold text-ink">{user.full_name}</span>
                    <span className="text-xs text-muted">{user.business_role}</span>
                  </span>
                </label>
              ))}
            </div>
          </section>
        ))}
      </div>
      <Button
        type="button"
        disabled={!selected.length}
        onClick={() => onSubmit(selected)}
      >
        Save Team Selection
      </Button>
    </div>
  );
}

function DeliverablesForm({ cases, onSubmit }: { cases: string[]; onSubmit: (payload: Record<string, string>) => void }) {
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        onSubmit({
          case_classification: String(form.get("case_classification") || ""),
          deadline_proposal_days: String(form.get("deadline_proposal_days") || ""),
        });
      }}
    >
      <label className="block">
        <span className="text-sm font-semibold text-ink">Case</span>
        <select className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="case_classification" required>
          <option value="">Select case</option>
          {cases.map((classification) => (
            <option key={classification} value={classification}>{classification}</option>
          ))}
        </select>
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-ink">Deadline</span>
        <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="deadline_proposal_days" type="number" required />
      </label>
      <Button type="submit">Submit Deliverables</Button>
    </form>
  );
}

const commandCenterCases = [
  {
    value: "Case 1 - Save for later",
    label: "Case 1",
    description: "Save for later",
  },
  {
    value: "Case 2 - Buy Critical Components then deliver to ARD",
    label: "Case 2",
    description: "Buy Critical Components then deliver to ARD",
  },
  {
    value: "Case 3 - Deliver to ARD directly",
    label: "Case 3",
    description: "Deliver to ARD directly",
  },
];

function CommandCenterForm({ onSubmit }: { onSubmit: (payload: Record<string, string>) => void }) {
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        onSubmit({
          command_center_case: String(form.get("command_center_case") || ""),
          deadline_days: String(form.get("deadline_days") || ""),
        });
      }}
    >
      <label className="block">
        <span className="text-sm font-semibold text-ink">Command Center Case</span>
        <select className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="command_center_case" required>
          <option value="">Select Command Center case</option>
          {commandCenterCases.map((option) => (
            <option key={option.value} value={option.value}>{option.label} - {option.description}</option>
          ))}
        </select>
      </label>
      <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
        {commandCenterCases.map((option) => (
          <div key={option.value} className="py-1 text-sm">
            <span className="font-bold text-ink">{option.label}:</span> <span className="text-muted">{option.description}</span>
          </div>
        ))}
      </div>
      <label className="block">
        <span className="text-sm font-semibold text-ink">Deadline</span>
        <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="deadline_days" type="number" required />
      </label>
      <Button type="submit">Submit Command Center Approval</Button>
    </form>
  );
}

function groupSrsUsers(users: SafeUser[]) {
  const groups = new Map<string, { label: string; department: string; users: SafeUser[] }>();
  for (const user of users) {
    const label = user.department_key === "SRS" ? srsSectionLabel(user) : user.department || "Other Department";
    const key = `${user.department_key}:${label}`;
    if (!groups.has(key)) groups.set(key, { label, department: user.department || "Department not set", users: [] });
    groups.get(key)?.users.push(user);
  }
  return Array.from(groups.values()).map((group) => ({
    ...group,
    users: group.users.sort((left, right) => roleRank(left.business_role) - roleRank(right.business_role) || left.full_name.localeCompare(right.full_name))
  }));
}

function srsSectionLabel(user: SafeUser) {
  if (user.business_role === "SRS Manager") return "SRS Management";
  const name = user.full_name.replace(/^SRS\s+/i, "");
  const section = name
    .replace(/\s+Section Head$/i, "")
    .replace(/\s+Team Leader$/i, "")
    .replace(/\s+Engineer\s+\d+$/i, "");
  return section ? `${section} Section` : "SRS Department";
}

function roleRank(role: string) {
  const index = ["SRS Manager", "SRS Section Head", "SRS Team Leader", "SRS Engineer"].indexOf(role);
  return index === -1 ? 99 : index;
}

function PathSubmissionForm({
  label,
  submitLabel,
  fieldName,
  onSubmit,
}: {
  label: string;
  submitLabel: string;
  fieldName: string;
  onSubmit: (path: string) => void;
}) {
  const [pathValue, setPathValue] = useState("");
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        onSubmit(String(form.get(fieldName) || ""));
      }}
    >
      <label className="block">
        <span className="text-sm font-semibold text-ink">{label}</span>
        <input
          className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          name={fieldName}
          value={pathValue}
          onChange={(event) => setPathValue(event.target.value)}
          placeholder={`Paste the shared folder path for the ${label.replace(" Path", "")} file`}
          required
        />
      </label>
      <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs font-semibold leading-5 text-amber-900">
        Browser security does not expose the real local file path from a file picker. Use the selector below only to copy the filename into the path box, then add the shared drive/folder path manually.
      </div>
      <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-bold text-ink hover:bg-gray-50">
        Browse local file
        <input
          className="sr-only"
          type="file"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) setPathValue((current) => current || file.name);
          }}
        />
      </label>
      <Button type="submit">{submitLabel}</Button>
    </form>
  );
}

function ExtensionRequestForm({
  unitLabel,
  onSubmit,
}: {
  unitLabel: string;
  onSubmit: (payload: Record<string, string>) => void;
}) {
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        onSubmit({
          extension_days: String(form.get("extension_days") || ""),
          comment: String(form.get("comment") || ""),
        });
      }}
    >
      <label className="block">
        <span className="text-sm font-semibold text-ink">Extension Duration</span>
        <div className="mt-2 flex rounded-md border border-gray-300 bg-white">
          <input className="focus-ring w-full rounded-l-md border-0 px-3 py-2 text-sm outline-none" name="extension_days" type="number" min="1" required />
          <span className="inline-flex items-center rounded-r-md border-l border-gray-300 bg-slate-50 px-3 text-xs font-black uppercase text-slate-500">{unitLabel}</span>
        </div>
      </label>
      <label className="block">
        <span className="text-sm font-semibold text-ink">Reason</span>
        <textarea className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="comment" rows={4} placeholder="Explain why the physical build needs more time" required />
      </label>
      <Button type="submit">Request Extension</Button>
    </form>
  );
}

function StatusBadge({ status }: { status?: string | null }) {
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-bold ${statusBadgeClass(status)}`}>{formatStatus(status)}</span>;
}

function CountdownBadge({
  startAt,
  dueAt,
  serverNow,
  now,
  compact = false,
}: {
  startAt?: string;
  dueAt?: string;
  serverNow?: string;
  now?: Date;
  compact?: boolean;
}) {
  const clockNow = useServerClock(serverNow);
  const current = now || clockNow;
  if (!startAt || !dueAt) return null;
  const start = new Date(startAt);
  const due = new Date(dueAt);
  const currentMs = current.getTime();
  let label = "Due in";
  let target = due;
  let className = "border-amber-200 bg-amber-50 text-amber-800";
  if (currentMs < start.getTime()) {
    label = "Starts in";
    target = start;
    className = "border-slate-200 bg-white text-slate-700";
  } else if (currentMs > due.getTime()) {
    label = "Overdue by";
    target = current;
    className = "border-red-200 bg-red-50 text-red-800";
  }
  const seconds = label === "Overdue by" ? (currentMs - due.getTime()) / 1000 : (target.getTime() - currentMs) / 1000;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-bold ${className}`}>
      <Clock3 className={compact ? "h-3 w-3" : "h-4 w-4"} />
      {label} {formatDistance(seconds)}
    </span>
  );
}

function useServerClock(serverNow?: string): Date {
  const [now, setNow] = useState(() => new Date());
  const offset = useMemo(() => {
    if (!serverNow) return 0;
    return new Date(serverNow).getTime() - Date.now();
  }, [serverNow]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date(Date.now() + offset)), 1000);
    return () => window.clearInterval(timer);
  }, [offset]);

  return now;
}

function isDeadlineOverdue(state: SrsNodeState | undefined, now: Date) {
  const dueAt = state?.deadline_due_at;
  if (!isActiveDeadlineState(state) || !dueAt) return false;
  return now.getTime() > new Date(dueAt).getTime();
}

function isActiveDeadlineState(state: SrsNodeState | undefined) {
  return Boolean(state?.deadline_due_at && ["IN_PROGRESS", "WAITING_APPROVAL", "READY"].includes(state.status));
}
