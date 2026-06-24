export type BedoModule = {
  route: string;
  title: string;
  module: string;
  department_key?: string;
  content?: string;
};

export type BedoUserContext = {
  user: string;
  username: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  email?: string;
  phone_number?: string;
  enabled: number;
  roles: string[];
  landing_route: string;
  modules: BedoModule[];
  session_id?: string;
};

export const adminRoute = "/admin/users";

export const routeLabels: Record<string, string> = {
  "/gm": "GM Support Office Dashboard",
  "/srs": "SRS Dashboard",
  "/srs/ard-electronics-cases": "ARD Electronics Cases",
  "/ard": "ARD Dashboard",
  "/command-center": "Command Center Dashboard",
  "/admin/users": "Admin Dashboard",
  "/meetings": "Meetings",
  "/notifications": "Notifications",
  "/approvals": "Approvals"
};

export const placeholderRoutes = ["/gm", "/srs", "/ard", "/command-center"];

export function isAdminUser(context: BedoUserContext) {
  return context.roles.includes("BEDO User Administrator") || context.roles.includes("BEDO System Administrator");
}

export function isSecurityAuditor(context: BedoUserContext) {
  return (
    context.roles.includes("General Manager") ||
    context.roles.includes("BEDO User Administrator") ||
    context.roles.includes("BEDO Security Auditor") ||
    context.roles.includes("BEDO System Administrator")
  );
}

export function isGeneralManager(context: BedoUserContext) {
  return context.roles.includes("General Manager");
}

export function isSrsUser(context: BedoUserContext) {
  return context.roles.some((role) => role.startsWith("SRS "));
}

export function isCommandCenterUser(context: BedoUserContext) {
  return context.roles.includes("Command Center Representative");
}

export function isArdUser(context: BedoUserContext) {
  return context.roles.some((role) => role.startsWith("ARD "));
}

export function canAccessRoute(context: BedoUserContext, route: string) {
  if (route === adminRoute) return isAdminUser(context) || isSecurityAuditor(context);
  return context.modules.some((module) => module.route === route);
}

export function displayName(context: BedoUserContext) {
  return [context.first_name, context.last_name].filter(Boolean).join(" ") || context.username;
}
