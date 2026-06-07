import { redirect } from "next/navigation";
import { AddProjectPage } from "@/features/srs/AddProjectPage";
import type { SafeUser } from "@/features/srs/types";
import type { BedoUserContext } from "@/lib/routes";
import { canAccessRoute } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page() {
  const session = await requireSession();
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);
  if (!canAccessRoute(freshSession, "/gm")) redirect("/forbidden");
  const data = await frappeCall<{ users: SafeUser[] }>("bedo_platform.api.web.list_report_to_candidates", {}, session.user).catch(() => ({ users: [] }));
  return <AddProjectPage reportToUsers={data.users} />;
}
