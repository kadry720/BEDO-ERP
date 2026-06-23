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
  price_egp?: number;
  original_quantity: number;
  separation_mode: string;
  sequence_no: number;
  status: string;
  current_node: string;
  current_responsible_user?: string;
  current_responsible_name?: string;
  released_to_srs_at?: string;
  workflow?: (SrsWorkflow & { project_owner_full_name?: string }) | null;
  deadline?: { node_id: string; start_at?: string; due_at: string; status: string; deadline_status?: string; server_now?: string } | null;
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
  pmdp_gate_path?: string;
  pmdp_gate_submitted_by?: string;
  pmdp_gate_submitted_at?: string;
  physical_build_started_at?: string;
  pmdp_path?: string;
  pmdp_submitted_by?: string;
  pmdp_submitted_at?: string;
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
  responsible_name?: string;
  last_action_by?: string;
  last_action_by_name?: string;
  display_data?: Record<string, string | number>;
};

export type SrsNodeDefinition = {
  id: string;
  label: string;
  lane: "operations" | "srs_entry" | "study_phase";
  column: "deadline_1" | "deadline_2" | "deadline_3" | "deadline_4";
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
  deadline_unit_label?: string;
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
  team_members: Array<{ user: string; full_name: string; is_project_owner?: number; selected_by?: string; selected_at?: string }>;
  approvals: Array<Record<string, string | number>>;
  command_center_handoff?: CommandCenterHandoff | null;
  supplier_files?: SupplierFile[];
  audit_events: Array<{ event_type: string; user: string; target_user?: string; node_id?: string; message?: string; created_at: string }>;
  tabs: string[];
  deadline_unit_label?: string;
};

export type WorkflowDeadline = {
  name?: string;
  workflow_type?: string;
  node_id?: string;
  start_at?: string;
  due_at?: string;
  deadline_days?: number;
  status?: string;
  server_now?: string;
};

export type CommandCenterHandoff = {
  name: string;
  project: string;
  trainer_item: string;
  srs_workflow_instance: string;
  handoff_type: string;
  status: string;
  command_center_case: string;
  deadline_days: number;
  approved_deadline_days: number;
  deadline: string;
  deadline_detail?: WorkflowDeadline;
  responsible_user: string;
  responsible_name: string;
  submitted_by: string;
  submitted_by_name: string;
  submitted_at: string;
  gm_approval: string;
  gm_approved_by: string;
  gm_approved_by_name: string;
  gm_approved_at: string;
  generation?: number;
  case3_cleared_at?: string;
  handover_meeting?: string;
  handover_confirmation_status?: string;
  handover_confirmed_by?: string;
  handover_confirmed_by_name?: string;
  handover_confirmed_at?: string;
  handover_failure_description?: string;
  handover_failed_by?: string;
  handover_failed_by_name?: string;
  handover_failed_at?: string;
  completed_by: string;
  completed_by_name: string;
  completed_at: string;
  notes: string;
  can_submit_decision: boolean;
  can_complete_case_1: boolean;
  can_schedule_handover_meeting?: boolean;
  can_submit_handover_confirmation?: boolean;
};

export type SupplierFile = {
  name: string;
  project: string;
  trainer_item: string;
  source_type: string;
  source_handoff: string;
  status: string;
  responsible_user: string;
  responsible_name: string;
  deadline: string;
  deadline_detail?: WorkflowDeadline;
  deadline_days: number;
  started_at: string;
  completed_by: string;
  completed_by_name: string;
  completed_at: string;
  details: string;
  latest_extension_approval: string;
  can_deliver: boolean;
  can_request_extension: boolean;
};

export type NotificationRow = {
  name: string;
  notification_type: string;
  type_label?: string;
  title: string;
  message: string;
  action_url: string;
  priority: string;
  is_read: number;
  created_at: string;
  project?: string;
  project_code?: string;
  project_name?: string;
  trainer_item?: string;
  trainer_item_name?: string;
};

export type ApprovalRow = {
  name: string;
  approval_type: string;
  approval_department: string;
  approval_label: string;
  status: string;
  required_role: string;
  project: string;
  project_code: string;
  project_name: string;
  end_user: string;
  po_deadline_date: string;
  trainer_item: string;
  trainer_item_name: string;
  submitted_by: string;
  submitted_by_name: string;
  submitted_at: string;
  project_owner: string;
  project_owner_name: string;
  current_node: string;
  command_center_handoff?: string;
  supplier_file?: string;
  deadline?: string;
  target_node?: string;
  target_node_label?: string;
  responsible_user?: string;
  responsible_user_name?: string;
  deadline_due_at?: string;
  case_classification: string;
  deadline_proposal_days: number;
  deadline_unit_label?: string;
  priority: string;
  comments?: string;
  created_at: string;
};

export type DashboardProps = {
  session: BedoUserContext;
  initialProjects: ProjectList;
  mode: "gm" | "srs" | "command-center" | "ard";
};
