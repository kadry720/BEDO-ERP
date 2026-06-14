import { redirect } from "next/navigation";
import { AdminUsersDashboard } from "@/features/admin/AdminUsersDashboard";
import type { AdminBootstrap, SecurityEvent } from "@/features/admin/types";
import { isAdminUser, isSecurityAuditor } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page() {
  const session = await requireSession();
  if (!isAdminUser(session) && !isSecurityAuditor(session)) redirect("/forbidden");
  const canManageUsers = isAdminUser(session);
  const bootstrapRequest = canManageUsers
    ? frappeCall<AdminBootstrap>("bedo_platform.api.web.get_admin_bootstrap", {}, session.user)
    : Promise.resolve<AdminBootstrap>({ users: [], roles: [], departments: [], technical_desk_roles: [] });
  const [bootstrap, security] = await Promise.all([
    bootstrapRequest,
    frappeCall<{ events: SecurityEvent[] }>("bedo_platform.api.web.list_security_events", { limit: 50 }, session.user).catch(() => ({ events: [] }))
  ]);
  return <AdminUsersDashboard bootstrap={{ ...bootstrap, can_manage_users: canManageUsers }} securityEvents={security.events} />;
}
