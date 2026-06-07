import Link from "next/link";
import { Bell, LogOut, Shield, UserCircle } from "lucide-react";
import { displayName, isAdminUser, routeLabels, type BedoUserContext } from "@/lib/routes";

export function Shell({ session, children }: { session: BedoUserContext; children: React.ReactNode }) {
  const routes = session.modules.filter((module) => module.route !== "/admin/users");
  return (
    <div className="min-h-screen bg-panel">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-gray-200 bg-white lg:block">
        <div className="border-b border-gray-200 px-6 py-5">
          <div className="text-lg font-bold tracking-normal text-ink">BEDO</div>
          <div className="mt-1 text-xs font-semibold uppercase text-muted">Process Governance</div>
        </div>
        <nav className="space-y-1 px-4 py-5">
          {routes.map((module) => (
            <Link
              key={module.route}
              href={module.route}
              className="flex rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
            >
              {routeLabels[module.route] || module.title}
            </Link>
          ))}
          {isAdminUser(session) && (
            <Link href="/admin/users" className="mt-4 flex rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white">
              <Shield className="mr-2 h-4 w-4" />
              Admin
            </Link>
          )}
        </nav>
      </aside>
      <div className="lg:pl-72">
        <header className="sticky top-0 z-10 flex min-h-16 items-center justify-end border-b border-gray-200 bg-white px-5">
          <div className="flex items-center gap-3">
            <Link href="/notifications" className="focus-ring rounded-md p-2 text-gray-600 hover:bg-gray-100" title="Notifications">
              <Bell className="h-5 w-5" />
            </Link>
            <Link href="/profile" className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-gray-100">
              <UserCircle className="h-4 w-4" />
              {displayName(session)}
            </Link>
            <form action="/api/auth/logout" method="post">
              <button className="focus-ring rounded-md p-2 text-gray-600 hover:bg-gray-100" title="Log out" type="submit">
                <LogOut className="h-5 w-5" />
              </button>
            </form>
          </div>
        </header>
        <main className="px-5 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
