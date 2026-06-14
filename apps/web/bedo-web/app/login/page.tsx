import { redirect } from "next/navigation";
import { getSession } from "@/server/session";
import { LoginForm } from "@/features/auth/LoginForm";

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
          <LoginForm initialError={params.error} />
        </div>
      </section>
    </main>
  );
}
