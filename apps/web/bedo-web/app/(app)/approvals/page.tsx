import { ApprovalsPage } from "@/features/approvals/ApprovalsPage";
import type { ApprovalRow } from "@/features/srs/types";
import { frappeCall } from "@/server/frappe";
import { requireSession } from "@/server/session";

export default async function Page() {
  const session = await requireSession();
  const data = await frappeCall<{ approvals: ApprovalRow[]; count: number }>("bedo_platform.api.web.list_my_pending_approvals", { status: "WAITING" }, session.user).catch(
    () => ({ approvals: [], count: 0 })
  );
  return <ApprovalsPage initialApprovals={data.approvals} />;
}
