import { Shell } from "@/components/Shell";
import type { BedoUserContext } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);
  return <Shell session={freshSession}>{children}</Shell>;
}
