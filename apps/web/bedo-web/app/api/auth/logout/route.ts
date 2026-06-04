import { redirect } from "next/navigation";
import { frappeCall } from "@/server/frappe";
import { clearSession, getSession } from "@/server/session";

export async function POST() {
  const session = await getSession();
  if (session) {
    await frappeCall("bedo_platform.api.web.logout", {}, session.user).catch(() => null);
  }
  await clearSession();
  redirect("/login");
}
