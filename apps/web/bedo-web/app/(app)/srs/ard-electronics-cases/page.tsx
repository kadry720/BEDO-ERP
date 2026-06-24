import { redirect } from "next/navigation";
import { ElectronicsCasesPage } from "@/features/srs/ElectronicsCasesPage";
import type { BedoUserContext } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

const electronicsCapabilityRole = "SRS Electronics Section Head";

export default async function Page() {
  const session = await requireSession();
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);
  if (!freshSession.roles.includes(electronicsCapabilityRole)) redirect("/forbidden");
  return <ElectronicsCasesPage />;
}
