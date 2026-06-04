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
  "/ard": "ARD",
  "/ard/blueprint": "ARD Blueprint",
  "/ard/validation": "ARD Validation",
  "/ard/scmdp": "ARD SCMDP",
  "/ard/coordination": "ARD Coordination",
  "/command-center": "Command Center",
  "/production": "Production",
  "/qc": "Quality Control",
  "/operations": "Operations",
  "/admin/users": "User Administration"
};

export const placeholderRoutes = Object.keys(routeLabels).filter((route) => route !== adminRoute);

export function isAdminUser(context: BedoUserContext) {
  return context.roles.includes("BEDO User Administrator") || context.roles.includes("BEDO System Administrator");
}

export function canAccessRoute(context: BedoUserContext, route: string) {
  if (route === adminRoute) return isAdminUser(context);
  return context.modules.some((module) => module.route === route);
}

export function displayName(context: BedoUserContext) {
  return [context.first_name, context.last_name].filter(Boolean).join(" ") || context.username;
}
