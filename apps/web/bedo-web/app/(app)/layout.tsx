import { Shell } from "@/components/Shell";
import type { BedoUserContext } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();
  const shellSession = await sessionForShell(session);
  return <Shell session={shellSession}>{children}</Shell>;
}

async function sessionForShell(session: BedoUserContext) {
  if (session.modules.length) return session;
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);
  return { ...freshSession, session_id: session.session_id };
}
