"use client";

import { useEffect, useMemo, useState, type CSSProperties, type ComponentType, type ReactNode } from "react";
import {
  CalendarClock,
  ClipboardCheck,
  Clock3,
  Copy,
  Cpu,
  FileInput,
  GitBranch,
  Loader2,
  PackageCheck,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Button } from "@/components/Button";
import { WorkflowActionDialog } from "@/components/workflow/WorkflowActionDialog";
import { WorkflowCanvas } from "@/components/workflow/WorkflowCanvas";
import { WorkflowOutputSummary } from "@/components/workflow/WorkflowOutputSummary";
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
  const availability = useMemo(() => new Map(workspace.node_availability.map((node) => [node.nodeId, node])), [workspace.node_availability]);
  const flowchartNodeIds = useMemo(() => new Set(flowchart.nodes.map((node) => node.id)), [flowchart.nodes]);
  const notApplicableNodeIds = new Set(workspace.node_states.filter((state) => state.status === "NOT_APPLICABLE").map((state) => state.node_id));
  const applicableNodeCount = flowchart.nodes.filter((node) => !notApplicableNodeIds.has(node.id)).length;
  const completeCount = workspace.node_states.filter((state) => flowchartNodeIds.has(state.node_id) && state.status === "COMPLETED" && !notApplicableNodeIds.has(state.node_id)).length;
  const progress = applicableNodeCount ? Math.round((completeCount / applicableNodeCount) * 100) : 0;
  const activeDeadlineState = workspace.node_states.find((state) => flowchartNodeIds.has(state.node_id) && isActiveDeadlineState(state))!;

  return (
    <WorkflowCanvas
      eyebrow="ARD Workflow"
      title={workspace.trainer_item.trainer_item_name}
      subtitle={`${workspace.project.project_code} | ${workspace.project.end_user}`}
      dimensions={ARD_FLOWCHART_DIMENSIONS}
      laneBands={ARD_LANE_BANDS}
      deadlineBands={ARD_DEADLINE_BANDS}
      deadlineColumns={flowchart.deadline_columns}
      nodes={flowchart.nodes}
      edges={flowchart.edges}
      states={states}
      availability={availability}
      headerStats={[
        { label: "Trainer Item", value: workspace.trainer_item.trainer_item_name },
        { label: "Current Stage", value: formatArdNodeId(workspace.workflow.current_node, flowchart) },
        { label: "Status", value: formatStatus(workspace.workflow.status), tone: statusTone(workspace.workflow.status) },
        { label: "ARD Progress", value: String(progress) },
      ]}
      markerId="ard-arrow"
      connectorRoutes={ARD_CONNECTOR_ROUTES}
      activeDeadlineState={activeDeadlineState}
      now={now}
      status={workspace.workflow.status}
      nodeIcons={ARD_NODE_ICONS}
      nodeSubtitles={ARD_NODE_SUBTITLES}
      canOpenNode={canOpenNodeModal}
      isDeadlineOverdue={isDeadlineOverdue}
      statusTone={statusTone}
      formatStatus={formatStatus}
      nodeSummary={nodeCardSummary}
      positionForNode={ardNodePosition}
      anchorPoint={ardAnchorPoint}
      renderStatusBadge={(status) => <StatusBadge status={status} />}
      renderDeadlineBadge={(state, compact) => (
        <CountdownBadge
          startAt={state.deadline_start_at}
          dueAt={state.deadline_due_at}
          serverNow={workspace.server_now}
          now={now}
          compact={compact}
        />
      )}
      onOpenNode={setActiveNode}
    >
      {activeNode && (
        <NodeModal
          nodeId={activeNode || ""}
          workspace={workspace}
          flowchart={flowchart}
          state={states.get(activeNode || "")}
          availability={availability.get(activeNode || "")}
          onClose={() => setActiveNode(null)}
          onUpdated={(next) => {
            setWorkspace(next);
            setActiveNode(null);
          }}
        />
      )}
    </WorkflowCanvas>
  );
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

function canOpenNodeModal(node: SrsNodeDefinition, state?: SrsNodeState, availability?: NodeAvailability) {
  if (state?.status === "NOT_APPLICABLE") return false;
  if (state?.status === "COMPLETED") return true;
  return Boolean(node.clickable && availability?.canOpen);
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
    <WorkflowActionDialog
      meta={{
        overline: readOnly ? "Workflow Output" : "ARD Action",
        title: node?.label || formatArdNodeId(nodeId, flowchart),
        projectCode: workspace.project.project_code,
        trainerItem: workspace.trainer_item.trainer_item_name,
        status: <StatusBadge status={state?.status || workspace.workflow.status} />,
        deadline: modalDeadlineState ? <CountdownBadge startAt={modalDeadlineState.deadline_start_at} dueAt={modalDeadlineState.deadline_due_at} serverNow={workspace.server_now} /> : undefined,
      }}
      error={error}
      onClose={onClose}
    >
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
    </WorkflowActionDialog>
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
  const [procurementNotes, setProcurementNotes] = useState("");
  const [procurementBomPath, setProcurementBomPath] = useState("");
  const [electronicsNotes, setElectronicsNotes] = useState("");
  const [electronicsBomPath, setElectronicsBomPath] = useState("");
  const [conceptNotes, setConceptNotes] = useState("");
  const [conceptReportPath, setConceptReportPath] = useState("");
  const toggle = (value: string, checked: boolean) => setSelected((current) => checked ? [...current, value] : current.filter((item) => item !== value));
  const showProcurement = selected.includes("PROCUREMENT_PAUSE");
  const showElectronics = selected.includes("ELECTRONICS_SYSTEM_DESIGN");
  const showConcept = selected.includes("CONCEPT_PROOF_PROTOTYPING");

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
      {showProcurement && (
        <InterruptionCaseSection title="Procurement Pause">
          <textarea className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" rows={3} value={procurementNotes} disabled={disabled} onChange={(event) => setProcurementNotes(event.target.value)} placeholder="Procurement notes" />
          <input className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={procurementBomPath} disabled={disabled} onChange={(event) => setProcurementBomPath(event.target.value)} placeholder="Procurement BOM path" />
        </InterruptionCaseSection>
      )}
      {showElectronics && (
        <InterruptionCaseSection title="Electronics System Design">
          <textarea className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" rows={3} value={electronicsNotes} disabled={disabled} onChange={(event) => setElectronicsNotes(event.target.value)} placeholder="Electronics notes" />
          <input className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={electronicsBomPath} disabled={disabled} onChange={(event) => setElectronicsBomPath(event.target.value)} placeholder="Electronics BOM path" />
        </InterruptionCaseSection>
      )}
      {showConcept && (
        <InterruptionCaseSection title="Concept-Proof Prototyping">
          <textarea className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" rows={3} value={conceptNotes} disabled={disabled} onChange={(event) => setConceptNotes(event.target.value)} placeholder="Concept-proof notes" />
          <input className="focus-ring w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={conceptReportPath} disabled={disabled} onChange={(event) => setConceptReportPath(event.target.value)} placeholder="Concept-proof technical report path" />
        </InterruptionCaseSection>
      )}
      <ActionButton
        loading={loading === "request_interruption"}
        disabled={disabled || !selected.length}
        onClick={() => onSubmit("request_interruption", {
          selected_cases: selected,
          procurement_notes: procurementNotes,
          procurement_bom_path: procurementBomPath,
          electronics_notes: electronicsNotes,
          electronics_bom_path: electronicsBomPath,
          concept_notes: conceptNotes,
          concept_report_path: conceptReportPath,
        })}
      >
        Submit Interruption Request
      </ActionButton>
    </div>
  );
}

function InterruptionCaseSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-2 rounded-md border border-slate-200 bg-white p-3">
      <div className="text-xs font-black uppercase tracking-wide text-slate-500">{title}</div>
      {children}
    </section>
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
  return <WorkflowOutputSummary rows={rows} description="Recorded ARD workflow output is shown below." />;
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
  const rows: OutputRow[] = nodeId === "ARD_PROJECT_OWNER_ASSIGNMENT"
    ? displayRows.filter((row) => !row.label.toLowerCase().includes("project owner"))
    : [...displayRows];

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
    const displayOwner = displayRows.find((row) => row.label.toLowerCase().includes("project owner"));
    rows.push({ label: "ARD Project Owner", value: owner?.full_name || displayOwner?.value || workspace.workflow.project_owner || "-" });
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
