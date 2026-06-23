export type MeetingParticipant = {
  user: string;
  department: string;
  participation_source: string;
  selected_by?: string;
  is_required?: number;
  confirmation_status: string;
  confirmed_at?: string;
};

export type MeetingRow = {
  name: string;
  meeting_id?: string;
  meeting_type: string;
  project?: string;
  trainer_item?: string;
  source_workflow?: string;
  source_workflow_generation?: number;
  source_node?: string;
  organizer: string;
  organizer_department?: string;
  scheduled_at: string;
  time_zone: string;
  expected_end_at?: string;
  status: string;
  title: string;
  description?: string;
  created_at?: string;
  confirmed_at?: string;
  completed_at?: string;
  overdue_at?: string;
  participants: MeetingParticipant[];
  confirmation_candidates?: string[];
};
