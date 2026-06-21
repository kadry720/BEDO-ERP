import { Shell } from "@/components/Shell";
import { requireSession } from "@/server/session";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();
  return <Shell session={session}>{children}</Shell>;
}
