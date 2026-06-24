import type { BedoProject, SafeUser, SrsFlowchartDefinition, SrsNodeState, TrainerItem, WorkflowDeadline } from "@/features/srs/types";

export type ArdWorkflow = {
  name: string;
  project: string;
  trainer_item: string;
  source_handoff: string;
  source_workflow: string;
  generation: number;
  status: string;
  current_node: string;
  project_owner: string;
  started_by: string;
  started_at: string;
  internal_sync_meeting: string;
  progress_review_meeting: string;
  scmdp_path: string;
  scmdp_submitted_by: string;
  scmdp_submitted_at: string;
  completed_by: string;
  completed_at: string;
};

export type ArdTeamMember = {
  user: string;
  full_name: string;
  department: string;
  business_role: string;
  is_project_owner: number;
  selected_by: string;
  selected_at: string;
};

export type ArdMeeting = {
  name: string;
  title: string;
  meeting_type: string;
  scheduled_at: string;
  expected_end_at: string;
  status: string;
  organizer: string;
  participants: Array<{
    user: string;
    department: string;
    participation_source: string;
    confirmation_status: string;
  }>;
};

export type ArdWorkspaceData = {
  project: BedoProject;
  trainer_item: TrainerItem;
  workflow: ArdWorkflow;
  node_states: SrsNodeState[];
  team_members: ArdTeamMember[];
  node_availability: Array<{ nodeId: string; canView: boolean; canOpen: boolean; canAct: boolean; disabledReason?: string }>;
  meetings: {
    internal_sync?: ArdMeeting | null;
    progress_review?: ArdMeeting | null;
  };
  ard_users: SafeUser[];
  deadlines: WorkflowDeadline[];
  server_now: string;
  tabs: string[];
};

export type ArdFlowchartDefinition = SrsFlowchartDefinition;

export type ArdProjectTrainerItem = TrainerItem & {
  workflow: null;
  ard_workflow: ArdWorkflow;
  team_members: ArdTeamMember[];
};

export type ArdProjectDetailData = {
  project: BedoProject;
  trainer_items: ArdProjectTrainerItem[];
};
