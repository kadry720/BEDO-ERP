import { redirect } from "next/navigation";
import type { BedoUserContext } from "@/lib/routes";
import { canAccessRoute, routeLabels } from "@/lib/routes";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

type Props = {
  route: string;
  eyebrow: string;
};

export async function DashboardPlaceholder({ route, eyebrow }: Props) {
  const session = await requireSession();
  const freshSession = await frappeCall<BedoUserContext>("bedo_platform.api.web.me", {}, session.user).catch(() => session);
  if (!canAccessRoute(freshSession, route)) redirect("/forbidden");
  return (
    <section className="space-y-6">
      <div className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="text-xs font-semibold uppercase text-muted">{eyebrow}</div>
        <h1 className="mt-2 text-3xl font-bold tracking-normal text-ink">{routeLabels[route]}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
          This department dashboard is intentionally empty in this phase. The current redesign only builds the secure
          application shell, authentication, route visibility, and user administration foundation.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {["Module visibility", "Workflow status", "Next phase"].map((title) => (
          <div key={title} className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
            <div className="text-sm font-semibold text-ink">{title}</div>
            <p className="mt-2 text-sm leading-6 text-muted">Placeholder only. No business workflow logic is active.</p>
          </div>
        ))}
      </div>
    </section>
  );
}
