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
};

export const adminRoute = "/admin/users";

export const routeLabels: Record<string, string> = {
  "/gm": "GM Support Office",
  "/srs": "SRS",
  "/admin/users": "User Administration",
  "/notifications": "Notifications"
};

export const placeholderRoutes = ["/gm", "/srs"];

export function isAdminUser(context: BedoUserContext) {
  return context.roles.includes("BEDO User Administrator") || context.roles.includes("BEDO System Administrator");
}

export function isGeneralManager(context: BedoUserContext) {
  return context.roles.includes("General Manager");
}

export function isSrsUser(context: BedoUserContext) {
  return context.roles.some((role) => role.startsWith("SRS "));
}

export function canAccessRoute(context: BedoUserContext, route: string) {
  if (route === adminRoute) return isAdminUser(context);
  return context.modules.some((module) => module.route === route);
}

export function displayName(context: BedoUserContext) {
  return [context.first_name, context.last_name].filter(Boolean).join(" ") || context.username;
}
