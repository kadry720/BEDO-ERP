import type { SrsNodeDefinition } from "@/features/srs/types";

export type ConnectorSide = "top" | "bottom" | "left" | "right";

export type ConnectorRoute = {
  fromSide: ConnectorSide;
  toSide: ConnectorSide;
  points?: Array<{ x: number; y: number }>;
};

export type StatusTone = "complete" | "in-progress" | "pending" | "awaiting-approval" | "locked" | "not-applicable" | "overdue";

export const FLOWCHART_DIMENSIONS = {
  laneLabelWidth: 170,
  canvasWidth: 1700,
  canvasHeight: 1100,
  deadlineHeaderHeight: 0,
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
  NOT_APPLICABLE: "Inactive Path",
  OVERDUE: "Overdue",
  PENDING: "Pending",
  READY: "Pending",
  RELEASED_TO_SRS: "Released to SRS",
  SRS_COMPLETE: "SRS Complete",
  SRS_GATEWAY_IN_PROGRESS: "SRS Gateway in Progress",
  SRS_IN_PROGRESS: "SRS in Progress",
  GATE_2_PMDP_IN_PROGRESS: "Gate 2 PMDP in Progress",
  WAITING_PMDP_DUAL_GATE_APPROVAL: "Awaiting PMDP Dual Gate Approval",
  PHYSICAL_BUILD_IN_PROGRESS: "Physical Build in Progress",
  WAITING_EXTENSION_APPROVAL: "Awaiting Extension Approval",
  PMDP_IN_PROGRESS: "PMDP in Progress",
  COMMAND_CENTER_APPROVAL_IN_PROGRESS: "Command Center Approval in Progress",
  WAITING_FINAL_GM_APPROVAL: "Awaiting Final GM Approval",
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
  if (label === "Inactive Path") return "border-slate-300 bg-slate-950 text-slate-100";
  if (label === "Locked") return "border-gray-200 bg-gray-100 text-gray-600";
  return "border-gray-200 bg-white text-gray-700";
}

export function nodeStatusClass(status?: string | null, canOpen = false) {
  const label = formatStatus(status);
  if (label === "SRS Complete" || label === "Complete") return "border-green-300 bg-green-50 shadow-sm";
  if (label === "In Progress" || label.includes("Progress") || label === "Active") return "border-amber-300 bg-amber-50 shadow-sm";
  if (label.includes("Awaiting")) return "border-blue-300 bg-blue-50 shadow-sm";
  if (label === "Overdue") return "border-red-300 bg-red-50 shadow-sm";
  if (label === "Inactive Path") return "border-slate-950 bg-slate-950";
  if (canOpen) return "border-slate-300 bg-white shadow-sm";
  return "border-gray-200 bg-gray-100";
}

export const NODE_POSITIONS: Record<string, { x: number; y: number; w: number; h: number }> = {
  PRODUCT_DIGITAL_RELEASE: { x: 70, y: 52, w: 230, h: 96 },
  SRS_GATEWAY: { x: 370, y: 48, w: 230, h: 104 },
  MANDATORY_COORDINATION_MEETING: { x: 70, y: 245, w: 285, h: 118 },
  DELIVERABLES_MATRIX: { x: 405, y: 245, w: 285, h: 118 },
  DUAL_GATE_APPROVAL: { x: 740, y: 246, w: 270, h: 116 },
  DEADLINE_LOCKED_IN_ERP: { x: 1060, y: 252, w: 260, h: 104 },
  ACTION_PATHS: { x: 1380, y: 256, w: 240, h: 96 },
  CASE_1: { x: 145, y: 500, w: 122, h: 92 },
  CASE_2: { x: 305, y: 500, w: 122, h: 92 },
  CASE_3: { x: 465, y: 500, w: 122, h: 92 },
  CASE_4: { x: 625, y: 500, w: 122, h: 92 },
  GATE_2_PMDP: { x: 465, y: 632, w: 270, h: 104 },
  PMDP_DUAL_GATE_APPROVAL: { x: 795, y: 632, w: 270, h: 112 },
  BMDP: { x: 1160, y: 625, w: 270, h: 104 },
  PHYSICAL_BUILD_TEST: { x: 795, y: 820, w: 270, h: 112 },
  EXTENSION_DEADLINE: { x: 1125, y: 790, w: 230, h: 104 },
  SRS_DIRECTOR_APPROVAL: { x: 1125, y: 925, w: 240, h: 104 },
  PMDP: { x: 795, y: 980, w: 230, h: 96 },
  COMMAND_CENTER_APPROVAL: { x: 1450, y: 800, w: 230, h: 112 },
  FINAL_GM_APPROVAL: { x: 1450, y: 950, w: 230, h: 112 },
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
  COMMAND_CENTER_APPROVAL: "Command Center Approval",
  DEADLINE_LOCKED_IN_ERP: "Deadline Locked in ERP",
  DELIVERABLES_MATRIX: "Deliverables Submission",
  DUAL_GATE_APPROVAL: "Dual Gate Approval",
  EXTENSION_DEADLINE: "Extension Deadline",
  FINAL_GM_APPROVAL: "GM Approval",
  GATE_2_PMDP: "Gate 2 PMDP",
  GATE_1_SRS_MANAGER_APPROVAL: "BMDP Deadline Approval",
  GM_APPROVAL: "GM Approval",
  MANDATORY_COORDINATION_MEETING: "Mandatory Coordination Meeting",
  PHYSICAL_BUILD_TEST: "Physical Build & Test",
  PMDP: "PMDP",
  PMDP_DUAL_GATE_APPROVAL: "Dual Gate Approval (SRS + Pillar 4)",
  PRODUCT_DIGITAL_RELEASE: "Product Digital Release",
  SRS_DIRECTOR_APPROVAL: "SRS Director Approval",
  SRS_GATEWAY: "SRS Gateway",
};

export const LANE_BANDS: Array<{ id: string; label: string; detail: string; y: number; h: number }> = [
  { id: "deadline_1", label: "Deadline 1", detail: "1 Day", y: 0, h: 190 },
  { id: "deadline_2", label: "Deadline 2", detail: "2 Days", y: 190, h: 240 },
  { id: "deadline_3", label: "Deadline 3", detail: "SRS / GM approved duration", y: 430, h: 330 },
  { id: "deadline_4", label: "Deadline 4", detail: "Build, PMDP, command center", y: 760, h: 340 },
];

export const DEADLINE_BANDS: Array<{ id: string; label: string; detail: string; x: number; w: number }> = [];

export const CONNECTOR_ROUTES: Record<string, ConnectorRoute> = {
  "PRODUCT_DIGITAL_RELEASE->SRS_GATEWAY": { fromSide: "right", toSide: "left" },
  "SRS_GATEWAY->MANDATORY_COORDINATION_MEETING": { fromSide: "bottom", toSide: "top", points: [{ x: 485, y: 205 }, { x: 213, y: 205 }] },
  "MANDATORY_COORDINATION_MEETING->DELIVERABLES_MATRIX": { fromSide: "right", toSide: "left" },
  "DELIVERABLES_MATRIX->DUAL_GATE_APPROVAL": { fromSide: "right", toSide: "left" },
  "DUAL_GATE_APPROVAL->DEADLINE_LOCKED_IN_ERP": { fromSide: "right", toSide: "left" },
  "DEADLINE_LOCKED_IN_ERP->ACTION_PATHS": { fromSide: "right", toSide: "left" },
  "ACTION_PATHS->CASE_1": { fromSide: "bottom", toSide: "top", points: [{ x: 1500, y: 455 }, { x: 206, y: 455 }] },
  "ACTION_PATHS->CASE_2": { fromSide: "bottom", toSide: "top", points: [{ x: 1500, y: 470 }, { x: 366, y: 470 }] },
  "ACTION_PATHS->CASE_3": { fromSide: "bottom", toSide: "top", points: [{ x: 1500, y: 485 }, { x: 526, y: 485 }] },
  "ACTION_PATHS->CASE_4": { fromSide: "bottom", toSide: "top", points: [{ x: 1500, y: 500 }, { x: 686, y: 500 }] },
  "CASE_1->BMDP": { fromSide: "right", toSide: "left", points: [{ x: 900, y: 546 }, { x: 900, y: 677 }] },
  "CASE_2->BMDP": { fromSide: "right", toSide: "left", points: [{ x: 945, y: 546 }, { x: 945, y: 677 }] },
  "CASE_4->BMDP": { fromSide: "right", toSide: "left", points: [{ x: 990, y: 546 }, { x: 990, y: 677 }] },
  "CASE_3->GATE_2_PMDP": { fromSide: "bottom", toSide: "top" },
  "GATE_2_PMDP->PMDP_DUAL_GATE_APPROVAL": { fromSide: "right", toSide: "left" },
  "PMDP_DUAL_GATE_APPROVAL->PHYSICAL_BUILD_TEST": { fromSide: "bottom", toSide: "top", points: [{ x: 930, y: 780 }] },
  "PHYSICAL_BUILD_TEST->EXTENSION_DEADLINE": { fromSide: "right", toSide: "left" },
  "EXTENSION_DEADLINE->SRS_DIRECTOR_APPROVAL": { fromSide: "bottom", toSide: "top" },
  "SRS_DIRECTOR_APPROVAL->PHYSICAL_BUILD_TEST": { fromSide: "left", toSide: "right", points: [{ x: 1090, y: 977 }, { x: 1090, y: 876 }] },
  "PHYSICAL_BUILD_TEST->PMDP": { fromSide: "bottom", toSide: "top" },
  "PMDP->BMDP": { fromSide: "right", toSide: "bottom", points: [{ x: 1085, y: 1028 }, { x: 1085, y: 760 }, { x: 1295, y: 760 }] },
  "BMDP->COMMAND_CENTER_APPROVAL": { fromSide: "right", toSide: "left", points: [{ x: 1440, y: 677 }, { x: 1440, y: 856 }] },
  "COMMAND_CENTER_APPROVAL->FINAL_GM_APPROVAL": { fromSide: "bottom", toSide: "top" },
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
  if (label === "Inactive Path") return "not-applicable";
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
