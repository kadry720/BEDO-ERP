import type { SrsNodeDefinition } from "@/features/srs/types";

export type ConnectorSide = "top" | "bottom" | "left" | "right";

export type ConnectorRoute = {
  fromSide: ConnectorSide;
  toSide: ConnectorSide;
};

export type StatusTone = "complete" | "in-progress" | "pending" | "awaiting-approval" | "locked" | "not-applicable" | "overdue";

export const FLOWCHART_DIMENSIONS = {
  laneLabelWidth: 200,
  canvasWidth: 1500,
  canvasHeight: 1120,
  deadlineHeaderHeight: 56,
};

export const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Active",
  COMPLETED: "Complete",
  COMPLETE: "Complete",
  DETAILS_FINALIZED: "Details Finalized",
  DRAFT: "Draft",
  IN_PROGRESS: "In Progress",
  LOCKED: "Locked",
  NOT_STARTED: "Not Started",
  NOT_APPLICABLE: "Not Applicable",
  OVERDUE: "Overdue",
  PENDING: "Pending",
  READY: "Pending",
  RELEASED_TO_SRS: "Released to SRS",
  SRS_COMPLETE: "SRS Complete",
  SRS_GATEWAY_IN_PROGRESS: "SRS Gateway in Progress",
  SRS_IN_PROGRESS: "SRS in Progress",
  SKIPPED: "Skipped",
  WAITING_APPROVAL: "Awaiting Approval",
  WAITING_GM_APPROVAL: "Awaiting GM Approval",
  WAITING_SRS_MANAGER_APPROVAL: "Awaiting SRS Manager Approval",
};

export function formatStatus(status?: string | null) {
  if (!status) return "Not Started";
  return STATUS_LABELS[status] || status.toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function statusBadgeClass(status?: string | null) {
  const label = formatStatus(status);
  if (label === "Complete" || label === "SRS Complete") return "border-green-200 bg-green-50 text-green-800";
  if (label === "In Progress" || label === "Active" || label.includes("Progress")) return "border-amber-200 bg-amber-50 text-amber-800";
  if (label.includes("Awaiting")) return "border-blue-200 bg-blue-50 text-blue-800";
  if (label === "Overdue") return "border-red-200 bg-red-50 text-red-800";
  if (label === "Not Applicable") return "border-slate-200 bg-slate-100 text-slate-500";
  if (label === "Locked") return "border-gray-200 bg-gray-100 text-gray-600";
  return "border-gray-200 bg-white text-gray-700";
}

export function nodeStatusClass(status?: string | null, canOpen = false) {
  const label = formatStatus(status);
  if (label === "SRS Complete" || label === "Complete") return "border-green-300 bg-green-50 shadow-sm";
  if (label === "In Progress" || label.includes("Progress") || label === "Active") return "border-amber-300 bg-amber-50 shadow-sm";
  if (label.includes("Awaiting")) return "border-blue-300 bg-blue-50 shadow-sm";
  if (label === "Overdue") return "border-red-300 bg-red-50 shadow-sm";
  if (label === "Not Applicable") return "border-slate-200 bg-slate-100";
  if (canOpen) return "border-slate-300 bg-white shadow-sm";
  return "border-gray-200 bg-gray-100";
}

export const NODE_POSITIONS: Record<string, { x: number; y: number; w: number; h: number }> = {
  PRODUCT_DIGITAL_RELEASE: { x: 40, y: 58, w: 230, h: 96 },
  SRS_GATEWAY: { x: 40, y: 230, w: 270, h: 124 },
  MANDATORY_COORDINATION_MEETING: { x: 360, y: 224, w: 285, h: 138 },
  DELIVERABLES_MATRIX: { x: 690, y: 224, w: 290, h: 138 },
  CASES_1_2: { x: 420, y: 470, w: 230, h: 96 },
  CASES_3_4: { x: 420, y: 625, w: 230, h: 96 },
  GM_APPROVAL: { x: 710, y: 615, w: 245, h: 128 },
  GATE_1_SRS_MANAGER_APPROVAL: { x: 1000, y: 460, w: 295, h: 132 },
  DEADLINE_LOCKED_IN_ERP: { x: 1000, y: 625, w: 255, h: 104 },
  ACTION_PATHS: { x: 1265, y: 570, w: 220, h: 96 },
  CASE_1: { x: 670, y: 800, w: 185, h: 102 },
  CASE_2: { x: 875, y: 800, w: 185, h: 102 },
  CASE_3: { x: 1080, y: 800, w: 195, h: 102 },
  CASE_4: { x: 1295, y: 800, w: 195, h: 102 },
  BMDP: { x: 930, y: 960, w: 320, h: 124 },
};

export const NODE_LABELS: Record<string, string> = {
  ACTION_PATHS: "Action Paths",
  BMDP: "BMDP",
  CASES_1_2: "Cases 1,2",
  CASES_3_4: "Cases 3,4",
  CASE_1: "Case 1",
  CASE_2: "Case 2",
  CASE_3: "Case 3",
  CASE_4: "Case 4",
  DEADLINE_LOCKED_IN_ERP: "Deadline Locked in ERP",
  DELIVERABLES_MATRIX: "Deliverables Matrix",
  GATE_1_SRS_MANAGER_APPROVAL: "Gate 1: SRS Manager Deadline Approval",
  GM_APPROVAL: "GM Approval",
  MANDATORY_COORDINATION_MEETING: "Mandatory Coordination Meeting",
  PRODUCT_DIGITAL_RELEASE: "Product Digital Release",
  SRS_GATEWAY: "SRS Gateway",
};

export const LANE_BANDS = [
  { id: "operations", label: "Operations", y: 0, h: 180 },
  { id: "srs_entry", label: "SRS Entry & Assignment", y: 180, h: 200 },
  { id: "study_phase", label: "Multidisciplinary Study Phase", y: 380, h: 740 },
];

export const DEADLINE_BANDS = [
  { id: "deadline_1", label: "Deadline 1", detail: "1 Day", x: 0, w: 280 },
  { id: "deadline_2", label: "Deadline 2", detail: "2 Days", x: 280, w: 510 },
  { id: "deadline_3", label: "Deadline 3", detail: "Depending on SRS Manager Approval", x: 790, w: 710 },
];

export const CONNECTOR_ROUTES: Record<string, ConnectorRoute> = {
  "PRODUCT_DIGITAL_RELEASE->SRS_GATEWAY": { fromSide: "bottom", toSide: "top" },
  "SRS_GATEWAY->MANDATORY_COORDINATION_MEETING": { fromSide: "right", toSide: "left" },
  "MANDATORY_COORDINATION_MEETING->DELIVERABLES_MATRIX": { fromSide: "right", toSide: "left" },
  "DELIVERABLES_MATRIX->CASES_1_2": { fromSide: "bottom", toSide: "top" },
  "DELIVERABLES_MATRIX->CASES_3_4": { fromSide: "bottom", toSide: "left" },
  "CASES_1_2->GATE_1_SRS_MANAGER_APPROVAL": { fromSide: "right", toSide: "left" },
  "CASES_3_4->GM_APPROVAL": { fromSide: "right", toSide: "left" },
  "GM_APPROVAL->GATE_1_SRS_MANAGER_APPROVAL": { fromSide: "right", toSide: "left" },
  "GATE_1_SRS_MANAGER_APPROVAL->DEADLINE_LOCKED_IN_ERP": { fromSide: "bottom", toSide: "top" },
  "DEADLINE_LOCKED_IN_ERP->ACTION_PATHS": { fromSide: "right", toSide: "left" },
  "ACTION_PATHS->CASE_1": { fromSide: "bottom", toSide: "top" },
  "ACTION_PATHS->CASE_2": { fromSide: "bottom", toSide: "top" },
  "ACTION_PATHS->CASE_3": { fromSide: "bottom", toSide: "top" },
  "ACTION_PATHS->CASE_4": { fromSide: "bottom", toSide: "top" },
  "CASE_1->BMDP": { fromSide: "bottom", toSide: "top" },
  "CASE_2->BMDP": { fromSide: "bottom", toSide: "top" },
  "CASE_3->BMDP": { fromSide: "bottom", toSide: "top" },
  "CASE_4->BMDP": { fromSide: "bottom", toSide: "top" },
};

export function nodePosition(node: SrsNodeDefinition) {
  return NODE_POSITIONS[node.id] || { x: 0, y: 0, w: 170, h: 90 };
}

export function midpoint(nodeId: string) {
  const position = NODE_POSITIONS[nodeId] || { x: 0, y: 0, w: 0, h: 0 };
  return { x: position.x + position.w / 2, y: position.y + position.h / 2 };
}

export function anchorPoint(nodeId: string, side: ConnectorSide) {
  const position = NODE_POSITIONS[nodeId] || { x: 0, y: 0, w: 0, h: 0 };
  if (side === "top") return { x: position.x + position.w / 2, y: position.y };
  if (side === "bottom") return { x: position.x + position.w / 2, y: position.y + position.h };
  if (side === "left") return { x: position.x, y: position.y + position.h / 2 };
  return { x: position.x + position.w, y: position.y + position.h / 2 };
}

export function sideNormal(side: ConnectorSide) {
  if (side === "top") return { x: 0, y: -1 };
  if (side === "bottom") return { x: 0, y: 1 };
  if (side === "left") return { x: -1, y: 0 };
  return { x: 1, y: 0 };
}

export function statusTone(status?: string | null): StatusTone {
  const label = formatStatus(status);
  if (label === "Complete" || label === "SRS Complete") return "complete";
  if (label === "Overdue") return "overdue";
  if (label === "Not Applicable") return "not-applicable";
  if (label.includes("Awaiting")) return "awaiting-approval";
  if (label === "In Progress" || label.includes("Progress") || label === "Active") return "in-progress";
  if (label === "Locked") return "locked";
  return "pending";
}

export function formatNodeId(nodeId?: string) {
  if (!nodeId) return "Not Started";
  if (NODE_LABELS[nodeId]) return NODE_LABELS[nodeId];
  return nodeId.toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatDistance(totalSeconds: number) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}
