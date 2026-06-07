import type { BedoUserContext } from "@/lib/routes";

export type ProjectCounts = {
  trainer_items?: number;
  srs_in_progress?: number;
  awaiting_owner_assignment?: number;
  in_coordination?: number;
  waiting_approval?: number;
  in_action_paths?: number;
  completed?: number;
  overdue?: number;
};

export type BedoProject = {
  name: string;
  project_code: string;
  project_name: string;
  end_user: string;
  po_deadline_date: string;
  status: string;
  created_by_user?: string;
  created_at?: string;
  finalized_at?: string;
  released_to_srs_at?: string;
  modified?: string;
  counts?: ProjectCounts;
};

export type ProjectList = {
  projects: BedoProject[];
  page: number;
  page_size: number;
  total: number;
};

export type TrainerItem = {
  name: string;
  project: string;
  trainer_name: string;
  trainer_item_name: string;
  quantity: number;
  original_quantity: number;
  separation_mode: string;
  sequence_no: number;
  status: string;
  current_node: string;
  current_responsible_user?: string;
  released_to_srs_at?: string;
  workflow?: SrsWorkflow | null;
  deadline?: { node_id: string; due_at: string; status: string; deadline_status?: string; server_now?: string } | null;
};

export type TrainerItemList = {
  trainer_items: TrainerItem[];
};

export type SrsWorkflow = {
  name: string;
  project: string;
  trainer_item: string;
  status: string;
  current_node: string;
  project_owner?: string;
  case_classification?: string;
  deadline_proposal_days?: number;
  approved_deadline_days?: number;
  bmdp_path?: string;
};

export type SrsNodeState = {
  node_id: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  deadline_start_at?: string;
  deadline_due_at?: string;
  deadline_days?: number;
  responsible_user?: string;
};

export type SrsNodeDefinition = {
  id: string;
  label: string;
  lane: "operations" | "srs_entry" | "study_phase";
  column: "deadline_1" | "deadline_2" | "deadline_3";
  kind: "display" | "action" | "approval" | "input";
  clickable: boolean;
  requiredRoles?: string[];
  requiredPreviousNodes?: string[];
  isTerminal?: boolean;
};

export type SrsFlowchartDefinition = {
  lanes: Array<{ id: string; label: string }>;
  deadline_columns: Array<{ id: string; label: string; detail: string }>;
  nodes: SrsNodeDefinition[];
  edges: Array<{ from: string; to: string }>;
  case_classifications: string[];
};

export type SafeUser = {
  user: string;
  username: string;
  full_name: string;
  business_role: string;
  department: string;
  department_key: string;
};

export type TrainerWorkspace = {
  project: BedoProject;
  trainer_item: TrainerItem;
  workflow: SrsWorkflow | null;
  node_states: SrsNodeState[];
  deadlines: Array<{ node_id: string; start_at: string; due_at: string; deadline_days: number; status: string; deadline_status?: string; server_now?: string }>;
  node_availability: Array<{ nodeId: string; canView: boolean; canOpen: boolean; canAct: boolean; disabledReason?: string }>;
  server_now: string;
  report_to_users: string[];
  audit_events: Array<{ event_type: string; user: string; target_user?: string; node_id?: string; message?: string; created_at: string }>;
  tabs: string[];
};

export type NotificationRow = {
  name: string;
  notification_type: string;
  title: string;
  message: string;
  action_url: string;
  priority: string;
  is_read: number;
  created_at: string;
};

export type DashboardProps = {
  session: BedoUserContext;
  initialProjects: ProjectList;
  mode: "gm" | "srs";
};
