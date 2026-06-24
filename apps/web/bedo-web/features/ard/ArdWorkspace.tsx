"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState, type CSSProperties, type ComponentType, type ReactNode } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Copy,
  Cpu,
  FileInput,
  GitBranch,
  Loader2,
  Lock,
  PackageCheck,
  Route,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { Button } from "@/components/Button";
import type { ArdFlowchartDefinition, ArdWorkspaceData } from "@/features/ard/types";
import type { SrsNodeDefinition, SrsNodeState } from "@/features/srs/types";
import {
  formatDistance,
  formatNodeId,
  formatStatus,
  statusBadgeClass,
  statusTone,
  type ConnectorRoute,
  type ConnectorSide,
} from "@/features/srs/workflowPresentation";

type NodeAvailability = ArdWorkspaceData["node_availability"][number];
type FlowIcon = ComponentType<{ className?: string; style?: CSSProperties }>;

const ARD_FLOWCHART_DIMENSIONS = {
  laneLabelWidth: 170,
  canvasWidth: 1700,
  canvasHeight: 1100,
  deadlineHeaderHeight: 0,
};

const ARD_LANE_BANDS: Array<{ id: string; label: string; detail: string; y: number; h: number }> = [
  { id: "handover", label: "Handover", detail: "SRS to ARD transfer", y: 0, h: 160 },
  { id: "formation", label: "ARD Formation", detail: "Sync, owner, team selection", y: 160, h: 250 },
  { id: "review", label: "Review", detail: "Progress review and route decision", y: 410, h: 210 },
  { id: "interruptions", label: "Interruption Paths", detail: "GM-approved interruption tracks", y: 620, h: 280 },
  { id: "final", label: "Final Submission", detail: "SCMDP submitted back to SRS", y: 900, h: 200 },
];

const ARD_DEADLINE_BANDS: Array<{ id: string; label: string; detail: string; x: number; w: number }> = [];

const ARD_NODE_POSITIONS: Record<string, { x: number; y: number; w: number; h: number }> = {
  HANDOVER_COMPLETE: { x: 70, y: 44, w: 260, h: 96 },
  INTERNAL_ARD_SYNC_MEETING: { x: 175, y: 222, w: 300, h: 112 },
  ARD_PROJECT_OWNER_ASSIGNMENT: { x: 555, y: 222, w: 300, h: 112 },
  ARD_TEAM_SELECTION: { x: 935, y: 222, w: 300, h: 112 },
  PROGRESS_REVIEW_MEETING: { x: 555, y: 462, w: 300, h: 112 },
  GM_APPROVAL: { x: 955, y: 470, w: 250, h: 96 },
  COMMAND_CENTER_PROCUREMENT_CONFIRMATION: { x: 1260, y: 636, w: 330, h: 106 },
  ELECTRONICS_SYSTEM_DESIGN: { x: 1260, y: 766, w: 330, h: 106 },
  CONCEPT_PROOF_PROTOTYPING: { x: 1260, y: 896, w: 330, h: 106 },
  SCMDP_SUBMISSION: { x: 555, y: 956, w: 315, h: 108 },
};

const ARD_CONNECTOR_ROUTES: Record<string, ConnectorRoute> = {
  "HANDOVER_COMPLETE->INTERNAL_ARD_SYNC_MEETING": { fromSide: "bottom", toSide: "top", points: [{ x: 200, y: 184 }, { x: 325, y: 184 }] },
  "INTERNAL_ARD_SYNC_MEETING->ARD_PROJECT_OWNER_ASSIGNMENT": { fromSide: "right", toSide: "left" },
  "ARD_PROJECT_OWNER_ASSIGNMENT->ARD_TEAM_SELECTION": { fromSide: "right", toSide: "left" },
  "ARD_TEAM_SELECTION->PROGRESS_REVIEW_MEETING": { fromSide: "bottom", toSide: "top", points: [{ x: 1085, y: 386 }, { x: 705, y: 386 }] },
  "PROGRESS_REVIEW_MEETING->SCMDP_SUBMISSION": { fromSide: "bottom", toSide: "top" },
  "PROGRESS_REVIEW_MEETING->GM_APPROVAL": { fromSide: "right", toSide: "left" },
  "GM_APPROVAL->COMMAND_CENTER_PROCUREMENT_CONFIRMATION": { fromSide: "right", toSide: "left", points: [{ x: 1230, y: 518 }, { x: 1230, y: 689 }] },
  "GM_APPROVAL->ELECTRONICS_SYSTEM_DESIGN": { fromSide: "right", toSide: "left", points: [{ x: 1245, y: 518 }, { x: 1245, y: 819 }] },
  "GM_APPROVAL->CONCEPT_PROOF_PROTOTYPING": { fromSide: "right", toSide: "left", points: [{ x: 1260, y: 518 }, { x: 1260, y: 949 }] },
  "COMMAND_CENTER_PROCUREMENT_CONFIRMATION->SCMDP_SUBMISSION": { fromSide: "left", toSide: "right", points: [{ x: 1010, y: 689 }, { x: 1010, y: 1010 }] },
  "ELECTRONICS_SYSTEM_DESIGN->SCMDP_SUBMISSION": { fromSide: "left", toSide: "right", points: [{ x: 980, y: 819 }, { x: 980, y: 1010 }] },
  "CONCEPT_PROOF_PROTOTYPING->SCMDP_SUBMISSION": { fromSide: "left", toSide: "right" },
};

const ARD_NODE_LABELS: Record<string, string> = {
  HANDOVER_COMPLETE: "Handover Complete",
  INTERNAL_ARD_SYNC_MEETING: "Internal ARD Sync Meeting",
  ARD_PROJECT_OWNER_ASSIGNMENT: "ARD Project Owner Assignment",
  ARD_TEAM_SELECTION: "ARD Team Selection",
  PROGRESS_REVIEW_MEETING: "Progress Review Meeting",
  GM_APPROVAL: "GM Approval",
  COMMAND_CENTER_PROCUREMENT_CONFIRMATION: "Command Center Procurement Confirmation",
  ELECTRONICS_SYSTEM_DESIGN: "Electronics System Design",
  CONCEPT_PROOF_PROTOTYPING: "Concept-Proof Prototyping",
  SCMDP_SUBMISSION: "SCMDP Submission",
};

const ARD_NODE_SUBTITLES: Record<string, string> = {
  HANDOVER_COMPLETE: "BMDP/PMDP handoff accepted",
  INTERNAL_ARD_SYNC_MEETING: "Schedule and complete the ARD kickoff sync",
  ARD_PROJECT_OWNER_ASSIGNMENT: "Assign the ARD project owner",
  ARD_TEAM_SELECTION: "Select the ARD execution team",
  PROGRESS_REVIEW_MEETING: "Confirm progress or request interruption paths",
  GM_APPROVAL: "GM approval for interruption route",
  COMMAND_CENTER_PROCUREMENT_CONFIRMATION: "Procurement pause confirmation",
  ELECTRONICS_SYSTEM_DESIGN: "Electronics route and supplier deadline",
  CONCEPT_PROOF_PROTOTYPING: "Concept proof completion",
  SCMDP_SUBMISSION: "Submit the SCMDP path",
};

const ARD_NODE_ICONS: Record<string, FlowIcon> = {
  HANDOVER_COMPLETE: PackageCheck,
  INTERNAL_ARD_SYNC_MEETING: CalendarClock,
  ARD_PROJECT_OWNER_ASSIGNMENT: Users,
  ARD_TEAM_SELECTION: Users,
  PROGRESS_REVIEW_MEETING: ClipboardCheck,
  GM_APPROVAL: ShieldCheck,
  COMMAND_CENTER_PROCUREMENT_CONFIRMATION: PackageCheck,
  ELECTRONICS_SYSTEM_DESIGN: Cpu,
  CONCEPT_PROOF_PROTOTYPING: GitBranch,
  SCMDP_SUBMISSION: FileInput,
};

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

export function ArdWorkspace({
  initialWorkspace,
  flowchart,
}: {
  initialWorkspace: ArdWorkspaceData;
  flowchart: ArdFlowchartDefinition;
}) {
  const [workspace, setWorkspace] = useState(initialWorkspace);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const states = useMemo(() => new Map(workspace.node_states.map((state) => [state.node_id, state])), [workspace.node_states]);
  const activeDeadline = workspace.node_states.find((state) => isActiveDeadlineState(state));

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">{workspace.project.project_code}</div>
            <h1 className="mt-2 text-3xl font-black text-slate-950">{workspace.trainer_item.trainer_item_name}</h1>
            <p className="mt-2 text-sm font-semibold text-slate-600">
              ARD workflow generation {workspace.workflow.generation} | Current step: {formatArdNodeId(workspace.workflow.current_node, flowchart)}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <StatusBadge status={workspace.workflow.status} />
            {activeDeadline && <CountdownBadge startAt={activeDeadline.deadline_start_at} dueAt={activeDeadline.deadline_due_at} serverNow={workspace.server_now} />}
          </div>
        </div>
      </header>

      <ArdFlowchart
        workspace={workspace}
        setWorkspace={setWorkspace}
        flowchart={flowchart}
        states={states}
        activeNode={activeNode}
        setActiveNode={setActiveNode}
      />
    </section>
  );
}

function ArdFlowchart({
  workspace,
  setWorkspace,
  flowchart,
  states,
  activeNode,
  setActiveNode,
}: {
  workspace: ArdWorkspaceData;
  setWorkspace: (workspace: ArdWorkspaceData) => void;
  flowchart: ArdFlowchartDefinition;
  states: Map<string, SrsNodeState>;
  activeNode: string | null;
  setActiveNode: (node: string | null) => void;
}) {
  const now = useServerClock(workspace.server_now);
  const frameRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const availability = useMemo(() => new Map(workspace.node_availability.map((node) => [node.nodeId, node])), [workspace.node_availability]);
  const flowchartNodeIds = useMemo(() => new Set(flowchart.nodes.map((node) => node.id)), [flowchart.nodes]);
  const diagramWidth = ARD_FLOWCHART_DIMENSIONS.laneLabelWidth + ARD_FLOWCHART_DIMENSIONS.canvasWidth;
  const diagramHeight = ARD_FLOWCHART_DIMENSIONS.deadlineHeaderHeight + ARD_FLOWCHART_DIMENSIONS.canvasHeight;
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
            <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">ARD Workflow</p>
            <h2 className="mt-1 text-lg font-bold text-white">{workspace.trainer_item.trainer_item_name}</h2>
            <p className="text-xs text-slate-300">{workspace.project.project_code} | {workspace.project.end_user}</p>
          </div>
          {activeDeadlineState ? (
            <CountdownBadge startAt={activeDeadlineState.deadline_start_at} dueAt={activeDeadlineState.deadline_due_at} serverNow={workspace.server_now} now={now} />
          ) : (
            <StatusBadge status={workspace.workflow.status} />
          )}
        </div>

        <div className="grid grid-cols-2 gap-px bg-slate-100 lg:grid-cols-4">
          <HeaderStat label="Trainer Item" value={workspace.trainer_item.trainer_item_name} />
          <HeaderStat label="Current Stage" value={formatArdNodeId(workspace.workflow.current_node, flowchart)} />
          <HeaderStat label="Status" value={formatStatus(workspace.workflow.status)} tone={statusTone(workspace.workflow.status)} />
          <HeaderStatProgress label="ARD Progress" value={progress} />
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
            {ARD_FLOWCHART_DIMENSIONS.deadlineHeaderHeight > 0 && ARD_DEADLINE_BANDS.length > 0 && (
              <div className="flex border-b border-slate-200 bg-slate-100">
                <div className="shrink-0 border-r border-slate-200" style={{ width: ARD_FLOWCHART_DIMENSIONS.laneLabelWidth }} />
                <div className="relative" style={{ width: ARD_FLOWCHART_DIMENSIONS.canvasWidth, height: ARD_FLOWCHART_DIMENSIONS.deadlineHeaderHeight }}>
                  {ARD_DEADLINE_BANDS.map((column, index) => (
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
            )}

            <div className="flex">
              <div className="relative shrink-0 border-r border-slate-200" style={{ width: ARD_FLOWCHART_DIMENSIONS.laneLabelWidth, height: ARD_FLOWCHART_DIMENSIONS.canvasHeight }}>
                {ARD_LANE_BANDS.map((lane, index) => (
                  <div
                    key={lane.id}
                    className={`absolute left-0 flex w-full items-center justify-center px-4 text-center ${index > 0 ? "border-t border-slate-700/40" : ""}`}
                    style={{ top: lane.y, height: lane.h, backgroundColor: index % 2 === 0 ? "#1e293b" : "#0f172a" }}
                  >
                    <span>
                      <span className="block text-[13px] font-semibold uppercase tracking-wide text-slate-100">{deadlineColumnMeta.get(lane.id)?.label || lane.label}</span>
                      <span className="mt-1 block text-[11px] font-medium leading-snug text-slate-300">{deadlineColumnMeta.get(lane.id)?.detail || lane.detail}</span>
                    </span>
                  </div>
                ))}
              </div>

              <div
                className="relative"
                style={{
                  width: ARD_FLOWCHART_DIMENSIONS.canvasWidth,
                  height: ARD_FLOWCHART_DIMENSIONS.canvasHeight,
                  backgroundColor: "#f8fafc",
                  backgroundImage:
                    "linear-gradient(to right, rgba(148,163,184,0.10) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.10) 1px, transparent 1px)",
                  backgroundSize: "32px 32px",
                }}
              >
                {ARD_LANE_BANDS.map((lane, index) => (
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

                {ARD_DEADLINE_BANDS.map((column, index) => (
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

                <svg className="pointer-events-none absolute inset-0" width={ARD_FLOWCHART_DIMENSIONS.canvasWidth} height={ARD_FLOWCHART_DIMENSIONS.canvasHeight}>
                  <defs>
                    <marker id="ard-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
                    </marker>
                  </defs>
                  {flowchart.edges.map((edge) => {
                    const path = ardEdgePath(edge.from, edge.to);
                    const sourceStatus = states.get(edge.from)?.status;
                    const targetStatus = states.get(edge.to)?.status;
                    const notApplicable = sourceStatus === "NOT_APPLICABLE" || targetStatus === "NOT_APPLICABLE";
                    const active = sourceStatus === "COMPLETED" && !notApplicable;
                    return (
                      <path
                        key={`${edge.from}-${edge.to}`}
                        d={path}
                        fill="none"
                        markerEnd="url(#ard-arrow)"
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

function ardEdgePath(fromId: string, toId: string) {
  const route = ARD_CONNECTOR_ROUTES[`${fromId}->${toId}`] || { fromSide: "right" as const, toSide: "left" as const };
  const start = ardAnchorPoint(fromId, route.fromSide);
  const end = ardAnchorPoint(toId, route.toSide);
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

function ardNodePosition(node: Pick<SrsNodeDefinition, "id">) {
  return ARD_NODE_POSITIONS[node.id] || { x: 0, y: 0, w: 190, h: 92 };
}

function ardAnchorPoint(nodeId: string, side: ConnectorSide) {
  const position = ARD_NODE_POSITIONS[nodeId] || { x: 0, y: 0, w: 0, h: 0 };
  if (side === "top") return { x: position.x + position.w / 2, y: position.y };
  if (side === "bottom") return { x: position.x + position.w / 2, y: position.y + position.h };
  if (side === "left") return { x: position.x, y: position.y + position.h / 2 };
  return { x: position.x + position.w, y: position.y + position.h / 2 };
}

function countdownPosition(nodeId: string) {
  const position = ardNodePosition({ id: nodeId });
  return { left: position.x, top: Math.max(8, position.y - 36) };
}

function canOpenNodeModal(node: SrsNodeDefinition, state?: SrsNodeState, availability?: NodeAvailability) {
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
  const position = ardNodePosition(node);
  const overdue = isDeadlineOverdue(state, now);
  const status = overdue ? "OVERDUE" : state?.status || "LOCKED";
  const isComplete = status === "COMPLETED";
  const isInactivePath = status === "NOT_APPLICABLE";
  const canOpen = canOpenNodeModal(node, state, availability);
  const canAct = Boolean(availability?.canOpen) && !isComplete && !isInactivePath;
  const tone = statusTone(status);
  const style = TONE_STYLES[tone];
  const StatusIcon = STATUS_ICONS[tone];
  const NodeIcon = ARD_NODE_ICONS[node.id] || Route;
  const subtitle = ARD_NODE_SUBTITLES[node.id];
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
  const styleProps: CSSProperties = {
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
      <button className={className} style={styleProps} type="button" onClick={onOpen} title={canAct ? node.label : `${node.label} output`}>
        {content}
      </button>
    );
  }

  return (
    <div className={className} style={styleProps} title={availability?.disabledReason || "Display-only step"}>
      {content}
    </div>
  );
}

function nodeCardSummary(nodeId: string, state?: SrsNodeState) {
  if (state?.status === "COMPLETED") return "";
  if (nodeId === "SCMDP_SUBMISSION") {
    const value = state?.display_data?.["SCMDP Path"];
    return value ? `Path: ${String(value)}` : "";
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
  onUpdated,
}: {
  nodeId: string;
  workspace: ArdWorkspaceData;
  flowchart: ArdFlowchartDefinition;
  state?: SrsNodeState;
  availability?: NodeAvailability;
  onClose: () => void;
  onUpdated: (workspace: ArdWorkspaceData) => void;
}) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState("");
  const node = flowchart.nodes.find((candidate) => candidate.id === nodeId);
  const readOnly = state?.status === "COMPLETED";
  const modalDeadlineState = state && isActiveDeadlineState(state) ? state : undefined;

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
      setError(data?.error || "ARD workflow action failed. Check permissions and workflow state.");
      return;
    }
    onUpdated(data);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4">
      <div className="flex max-h-[92vh] w-full max-w-3xl flex-col rounded-md bg-white shadow-xl">
        <div className="border-b border-gray-200 px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs font-bold uppercase text-muted">{readOnly ? "Workflow Output" : "ARD Action"}</div>
              <h3 className="mt-1 text-xl font-bold text-ink">{node?.label || formatArdNodeId(nodeId, flowchart)}</h3>
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
                <StatusBadge status={state?.status || workspace.workflow.status} />
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
            <ArdNodeOutputSummary nodeId={nodeId} state={state} workspace={workspace} />
          ) : availability?.canOpen ? (
            <ArdNodeAction
              nodeId={nodeId}
              disabled={!availability?.canAct}
              disabledReason={availability?.disabledReason}
              loading={loading}
              workspace={workspace}
              state={state}
              onSubmit={submit}
            />
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

function ArdNodeAction({
  nodeId,
  disabled,
  disabledReason,
  loading,
  workspace,
  state,
  onSubmit,
}: {
  nodeId: string;
  disabled: boolean;
  disabledReason?: string;
  loading: string;
  workspace: ArdWorkspaceData;
  state?: SrsNodeState;
  onSubmit: (action: string, payload?: Record<string, unknown>) => void;
}) {
  return (
    <div className="space-y-4">
      {disabled && disabledReason && <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm font-semibold text-slate-600">{disabledReason}</div>}
      {nodeId === "INTERNAL_ARD_SYNC_MEETING" && (
        <InternalSyncForm disabled={disabled} loading={loading} users={workspace.ard_users} onSubmit={onSubmit} canComplete={state?.status === "IN_PROGRESS"} />
      )}
      {nodeId === "ARD_PROJECT_OWNER_ASSIGNMENT" && (
        <OwnerForm disabled={disabled} loading={loading} users={workspace.ard_users} onSubmit={onSubmit} />
      )}
      {nodeId === "ARD_TEAM_SELECTION" && (
        <TeamSelectionForm disabled={disabled} loading={loading} users={workspace.ard_users.filter((user) => user.user !== workspace.workflow.project_owner)} onSubmit={onSubmit} />
      )}
      {nodeId === "PROGRESS_REVIEW_MEETING" && (
        <ProgressReviewForm disabled={disabled} loading={loading} onSubmit={onSubmit} />
      )}
      {nodeId === "COMMAND_CENTER_PROCUREMENT_CONFIRMATION" && (
        <InterruptionActionForm disabled={disabled} loading={loading} action="confirm_procurement" label="Confirm Items Received" onSubmit={onSubmit} />
      )}
      {nodeId === "ELECTRONICS_SYSTEM_DESIGN" && (
        <ElectronicsSubcaseForm disabled={disabled} loading={loading} onSubmit={onSubmit} />
      )}
      {nodeId === "CONCEPT_PROOF_PROTOTYPING" && (
        <InterruptionActionForm disabled={disabled} loading={loading} action="complete_concept_proof" label="Confirm Prototyping Complete" onSubmit={onSubmit} />
      )}
      {nodeId === "SCMDP_SUBMISSION" && <ScmdpForm disabled={disabled} loading={loading} onSubmit={onSubmit} />}
    </div>
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
        <span className="text-sm font-semibold text-ink">Meeting date and time</span>
        <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" type="datetime-local" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} disabled={disabled} />
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
      <label className="block">
        <span className="text-sm font-semibold text-ink">ARD project owner</span>
        <select className="focus-ring mt-2 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm" value={owner} disabled={disabled} onChange={(event) => setOwner(event.target.value)}>
          <option value="">Select ARD project owner</option>
          {users.map((user) => <option key={user.user} value={user.user}>{user.full_name} | {user.business_role}</option>)}
        </select>
      </label>
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
      <div className="flex items-center justify-between gap-3 rounded-md border border-gray-200 bg-white px-3 py-2 shadow-sm">
        <div>
          <div className="text-sm font-bold text-ink">Select ARD team members</div>
          <div className="text-xs text-muted">Grouped by available ARD staff.</div>
        </div>
        <span className="rounded bg-orange-50 px-2 py-1 text-xs font-bold text-ink">{selected.length} selected</span>
      </div>
      <UserCheckboxes users={users} selected={selected} setSelected={setSelected} disabled={disabled} />
      <ActionButton loading={loading === "select_team"} disabled={disabled || !selected.length} onClick={() => onSubmit("select_team", { users: selected })}>
        Save ARD Team
      </ActionButton>
    </div>
  );
}

function ProgressReviewForm({ disabled, loading, onSubmit }: { disabled: boolean; loading: string; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  const [showInterruption, setShowInterruption] = useState(false);
  return (
    <div className="space-y-3">
      <ActionButton loading={loading === "progress_review"} disabled={disabled} onClick={() => onSubmit("progress_review", { outcome: "ON_PLAN" })}>
        Mark On Plan
      </ActionButton>
      <Button variant="secondary" type="button" disabled={disabled} onClick={() => setShowInterruption((current) => !current)}>
        Request Interruption
      </Button>
      {showInterruption && <InterruptionRequestForm disabled={disabled} loading={loading} onSubmit={onSubmit} />}
    </div>
  );
}

function InterruptionRequestForm({ disabled, loading, onSubmit }: { disabled: boolean; loading: string; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [bomPath, setBomPath] = useState("");
  const [conceptPath, setConceptPath] = useState("");
  const toggle = (value: string, checked: boolean) => setSelected((current) => checked ? [...current, value] : current.filter((item) => item !== value));
  return (
    <div className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-3">
      {[
        ["PROCUREMENT_PAUSE", "Procurement Pause"],
        ["ELECTRONICS_SYSTEM_DESIGN", "Electronics System Design"],
        ["CONCEPT_PROOF_PROTOTYPING", "Concept-Proof Prototyping"],
      ].map(([value, label]) => (
        <label key={value} className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <input className="accent-slate-950" type="checkbox" disabled={disabled} checked={selected.includes(value)} onChange={(event) => toggle(value, event.target.checked)} />
          {label}
        </label>
      ))}
      <textarea className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" rows={3} value={notes} disabled={disabled} onChange={(event) => setNotes(event.target.value)} placeholder="Notes" />
      <input className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={bomPath} disabled={disabled} onChange={(event) => setBomPath(event.target.value)} placeholder="Optional BOM path" />
      <input className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={conceptPath} disabled={disabled} onChange={(event) => setConceptPath(event.target.value)} placeholder="Concept-Proof technical report path" />
      <ActionButton
        loading={loading === "request_interruption"}
        disabled={disabled || !selected.length}
        onClick={() => onSubmit("request_interruption", {
          selected_cases: selected,
          procurement_notes: notes,
          procurement_bom_path: bomPath,
          electronics_notes: notes,
          electronics_bom_path: bomPath,
          concept_notes: notes,
          concept_report_path: conceptPath,
        })}
      >
        Submit Interruption Request
      </ActionButton>
    </div>
  );
}

function InterruptionActionForm({ disabled, loading, action, label, onSubmit }: { disabled: boolean; loading: string; action: string; label: string; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  return (
    <ActionButton loading={loading === action} disabled={disabled} onClick={() => onSubmit(action)}>
      {label}
    </ActionButton>
  );
}

function ElectronicsSubcaseForm({ disabled, loading, onSubmit }: { disabled: boolean; loading: string; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  const [subcase, setSubcase] = useState("INVENTORY_STOCK");
  const [deadlineDays, setDeadlineDays] = useState("");
  const needsDeadline = subcase !== "INVENTORY_STOCK";
  return (
    <div className="space-y-3">
      <label className="block">
        <span className="text-sm font-semibold text-ink">Electronics subcase</span>
        <select className="focus-ring mt-2 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm" value={subcase} disabled={disabled} onChange={(event) => setSubcase(event.target.value)}>
          <option value="INVENTORY_STOCK">Inventory Stock</option>
          <option value="DESIGN_COMPLETE_NO_INVENTORY">Design Complete / No Inventory</option>
          <option value="NEW_DESIGN">New Design</option>
        </select>
      </label>
      {needsDeadline && (
        <label className="block">
          <span className="text-sm font-semibold text-ink">Supplier deadline days</span>
          <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" type="number" min={1} value={deadlineDays} disabled={disabled} onChange={(event) => setDeadlineDays(event.target.value)} />
        </label>
      )}
      <div className="flex flex-wrap gap-2">
        <ActionButton loading={loading === "choose_electronics_subcase"} disabled={disabled || (needsDeadline && !deadlineDays)} onClick={() => onSubmit("choose_electronics_subcase", { subcase, supplier_deadline_days: deadlineDays })}>
          Save Electronics Subcase
        </ActionButton>
        {subcase === "NEW_DESIGN" && (
          <ActionButton loading={loading === "complete_electronics"} disabled={disabled} onClick={() => onSubmit("complete_electronics")}>
            Complete Electronics Action
          </ActionButton>
        )}
      </div>
    </div>
  );
}

function ScmdpForm({ disabled, loading, onSubmit }: { disabled: boolean; loading: string; onSubmit: (action: string, payload?: Record<string, unknown>) => void }) {
  const [path, setPath] = useState("");
  const [checked, setChecked] = useState(false);
  return (
    <div className="space-y-4">
      <label className="block">
        <span className="text-sm font-semibold text-ink">SCMDP path</span>
        <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" value={path} disabled={disabled} onChange={(event) => setPath(event.target.value)} placeholder="Paste the shared SCMDP path" />
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
    <div className="grid max-h-[38vh] gap-3 overflow-y-auto pr-1">
      {users.map((user) => (
        <label
          key={user.user}
          className={`flex cursor-pointer items-start gap-3 rounded-md border bg-white p-2.5 transition ${
            selected.includes(user.user) ? "border-ember ring-2 ring-orange-100" : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <input
            className="mt-1 accent-ember"
            type="checkbox"
            disabled={disabled}
            checked={selected.includes(user.user)}
            onChange={(event) => setSelected(event.target.checked ? [...selected, user.user] : selected.filter((value) => value !== user.user))}
          />
          <span className="min-w-0">
            <span className="block truncate font-semibold text-ink">{user.full_name}</span>
            <span className="block truncate text-xs text-muted">{user.business_role || "BEDO User"} | {user.department}</span>
          </span>
        </label>
      ))}
    </div>
  );
}

type OutputRow = {
  label: string;
  value: string;
  list?: string[];
  copyable?: boolean;
};

function ArdNodeOutputSummary({ nodeId, state, workspace }: { nodeId: string; state?: SrsNodeState; workspace: ArdWorkspaceData }) {
  const rows = nodeOutputRows(nodeId, state, workspace);
  return (
    <div className="space-y-4">
      <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-black text-emerald-800">
          <CheckCircle2 className="h-4 w-4" />
          Step complete
        </div>
        <p className="mt-1 text-sm font-medium text-emerald-900/80">Recorded ARD workflow output is shown below.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {rows.map((row) => <OutputCard key={row.label} row={row} />)}
      </div>
    </div>
  );
}

function OutputCard({ row }: { row: OutputRow }) {
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

function nodeOutputRows(nodeId: string, state: SrsNodeState | undefined, workspace: ArdWorkspaceData): OutputRow[] {
  const completedBy = state?.last_action_by_name || state?.last_action_by || state?.responsible_name || state?.responsible_user || "-";
  const displayRows = Object.entries(state?.display_data || {})
    .filter(([, value]) => value !== "" && value !== undefined && value !== null)
    .map(([label, value]) => ({
      label,
      value: String(value),
      copyable: label.toLowerCase().includes("path"),
    }));
  const rows: OutputRow[] = [...displayRows];

  if (nodeId === "INTERNAL_ARD_SYNC_MEETING" && workspace.meetings.internal_sync) {
    rows.push({ label: "Meeting", value: workspace.meetings.internal_sync.title || "Internal ARD Sync Meeting" });
    rows.push({ label: "Scheduled At", value: formatWorkflowTimestamp(workspace.meetings.internal_sync.scheduled_at) });
    rows.push({ label: "Participants", value: "", list: workspace.meetings.internal_sync.participants?.map((participant) => participant.user) || [] });
  }

  if (nodeId === "ARD_TEAM_SELECTION") {
    rows.push({ label: "Selected ARD Team", value: "", list: workspace.team_members.filter((member) => !member.is_project_owner).map((member) => member.full_name || member.user) });
  }

  if (nodeId === "ARD_PROJECT_OWNER_ASSIGNMENT") {
    const owner = workspace.team_members.find((member) => member.is_project_owner);
    rows.push({ label: "ARD Project Owner", value: owner?.full_name || workspace.workflow.project_owner || "-" });
  }

  if (state?.completed_at) rows.push({ label: "Completed At", value: formatWorkflowTimestamp(state.completed_at) });
  rows.push({ label: "Completed By", value: completedBy });
  return rows.length ? rows : [{ label: "Completed By", value: completedBy }];
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

function formatArdNodeId(nodeId?: string, flowchart?: ArdFlowchartDefinition) {
  if (!nodeId) return "Not Started";
  const node = flowchart?.nodes.find((candidate) => candidate.id === nodeId);
  if (node?.label) return node.label;
  if (ARD_NODE_LABELS[nodeId]) return ARD_NODE_LABELS[nodeId];
  return formatNodeId(nodeId);
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
