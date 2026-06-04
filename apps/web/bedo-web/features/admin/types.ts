export type AdminUser = {
  user: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  primary_department: string;
  roles: string[];
  enabled: number;
};

export type Department = {
  key: string;
  name: string;
  pillar_number: number;
  dashboard_route: string;
  is_global_access_department: number;
};

export type SecurityEvent = {
  event_type: string;
  username: string;
  user: string;
  status: string;
  ip_address: string;
  user_agent: string;
  message: string;
  created_at: string;
};

export type AdminBootstrap = {
  users: AdminUser[];
  roles: string[];
  departments: Department[];
  technical_desk_roles: string[];
};
