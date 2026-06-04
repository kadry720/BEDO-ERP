import { redirect } from "next/navigation";
import { AdminUsersDashboard } from "@/features/admin/AdminUsersDashboard";
import type { AdminBootstrap, SecurityEvent } from "@/features/admin/types";
import { isAdminUser } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page() {
  const session = await requireSession();
  if (!isAdminUser(session)) redirect("/forbidden");
  const [bootstrap, security] = await Promise.all([
    frappeCall<AdminBootstrap>("bedo_platform.api.web.get_admin_bootstrap", {}, session.user),
    frappeCall<{ events: SecurityEvent[] }>("bedo_platform.api.web.list_security_events", { limit: 50 }, session.user).catch(() => ({ events: [] }))
  ]);
  return <AdminUsersDashboard bootstrap={bootstrap} securityEvents={security.events} />;
}
