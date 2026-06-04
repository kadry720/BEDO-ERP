import { redirect } from "next/navigation";
import { getSession } from "@/server/session";

export default async function LoginPage({ searchParams }: { searchParams?: Promise<{ error?: string }> }) {
  const session = await getSession();
  if (session) redirect(session.landing_route || "/access-not-configured");
  const params = searchParams ? await searchParams : {};

  return (
    <main className="min-h-screen bg-ink text-white">
      <header className="border-b border-orange-400 bg-ember px-8 py-5">
        <div className="text-xl font-bold">BEDO</div>
        <div className="mt-1 text-xs font-semibold uppercase tracking-wide text-orange-50">Industrial Process Governance</div>
      </header>
      <section className="flex min-h-[calc(100vh-84px)] items-center justify-center px-6 py-12">
        <div className="w-full max-w-xl rounded-md border border-gray-200 bg-white p-8 text-ink shadow-panel">
          <div className="mb-8 text-center">
            <h2 className="text-4xl font-bold tracking-normal text-ink">Sign in</h2>
            <p className="mt-3 text-base text-muted">Use your LDAP username and password.</p>
          </div>
          <form className="space-y-6" action="/api/auth/login" method="post">
            <label className="block">
              <span className="text-base font-semibold text-ink">Username</span>
              <input
                className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-4 py-4 text-base"
                name="username"
                autoComplete="username"
                required
              />
            </label>
            <label className="block">
              <span className="text-base font-semibold text-ink">Password</span>
              <input
                className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-4 py-4 text-base"
                name="password"
                type="password"
                autoComplete="current-password"
                required
              />
            </label>
            {params.error === "invalid" && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                Invalid username or password.
              </div>
            )}
            <button
              className="focus-ring inline-flex min-h-12 w-full items-center justify-center rounded-md bg-ink px-4 text-base font-semibold text-white transition hover:bg-steel"
              type="submit"
            >
              Sign in
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
