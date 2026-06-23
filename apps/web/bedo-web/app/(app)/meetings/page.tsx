import { MeetingsPage } from "@/features/meetings/MeetingsPage";
import type { MeetingRow } from "@/features/meetings/types";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export default async function Page() {
  const session = await getSession();
  let meetings: MeetingRow[] = [];
  if (session) {
    const data = await frappeCall<{ meetings: MeetingRow[] }>("bedo_platform.api.web.list_my_meetings", {}, session.user);
    meetings = data.meetings || [];
  }
  return <MeetingsPage initialMeetings={meetings} currentUser={session?.user || ""} />;
}
