import type { CSSProperties, ComponentType, ReactNode } from "react";

export type WorkflowConnectorSide = "top" | "bottom" | "left" | "right";

export type WorkflowConnectorRoute = {
  fromSide: WorkflowConnectorSide;
  toSide: WorkflowConnectorSide;
  points?: Array<{ x: number; y: number }>;
};

export type WorkflowTone = "complete" | "in-progress" | "pending" | "awaiting-approval" | "locked" | "not-applicable" | "overdue";

export type WorkflowIcon = ComponentType<{ className?: string; style?: CSSProperties }>;

export type WorkflowDimensions = {
  laneLabelWidth: number;
  canvasWidth: number;
  canvasHeight: number;
  deadlineHeaderHeight: number;
};

export type WorkflowLaneBand = {
  id: string;
  label: string;
  detail: string;
  y: number;
  h: number;
};

export type WorkflowDeadlineBand = {
  id: string;
  label: string;
  detail: string;
  x: number;
  w: number;
};

export type WorkflowDeadlineColumn = {
  id: string;
  label: string;
  detail: string;
};

export type WorkflowNode = {
  id: string;
  label: string;
  clickable: boolean;
};

export type WorkflowNodeState = {
  node_id: string;
  status: string;
  deadline_start_at?: string;
  deadline_due_at?: string;
  display_data?: Record<string, string | number>;
};

export type WorkflowNodeAvailability = {
  nodeId: string;
  canOpen: boolean;
  canAct: boolean;
  disabledReason?: string;
};

export type WorkflowCanvasHeaderStat = {
  label: string;
  value: string;
  tone?: WorkflowTone;
};

export type WorkflowOutputRow = {
  label: string;
  value: string;
  list?: string[];
  copyable?: boolean;
};

export type WorkflowActionDialogMeta = {
  overline: string;
  title: string;
  projectCode: string;
  trainerItem: string;
  status: ReactNode;
  deadline?: ReactNode;
};
