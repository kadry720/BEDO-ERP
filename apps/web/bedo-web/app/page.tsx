import { redirect } from "next/navigation";
import { getSession } from "@/server/session";

export default async function Page() {
  const session = await getSession();
  redirect(session?.landing_route || "/login");
}
