import { redirect } from "next/navigation";
import { getSession } from "@/server/session";
import { LoginForm } from "@/features/auth/LoginForm";

export default async function LoginPage() {
  const session = await getSession();
  if (session) redirect(session.landing_route || "/access-not-configured");

  return (
    <main className="grid min-h-screen grid-cols-1 bg-white lg:grid-cols-[1.1fr_0.9fr]">
      <section className="flex min-h-[45vh] flex-col justify-between bg-ink px-8 py-10 text-white lg:min-h-screen">
        <div>
          <div className="text-xl font-bold">BEDO</div>
          <div className="mt-2 text-sm font-semibold uppercase text-gray-300">Industrial Process Governance</div>
        </div>
        <div className="max-w-xl">
          <h1 className="text-4xl font-bold tracking-normal">Operational control without Desk clutter.</h1>
          <p className="mt-5 text-base leading-7 text-gray-300">
            A focused enterprise shell for role-based dashboards, user administration, and future workflow execution.
          </p>
        </div>
      </section>
      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-ink">Sign in</h2>
            <p className="mt-2 text-sm text-muted">Use your LDAP username and password.</p>
          </div>
          <LoginForm />
        </div>
      </section>
    </main>
  );
}
