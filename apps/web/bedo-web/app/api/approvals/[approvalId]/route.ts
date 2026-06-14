import { NextResponse } from "next/server";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

type Params = { params: Promise<{ approvalId: string }> };

export async function GET(_request: Request, { params }: Params) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const { approvalId } = await params;
    const data = await frappeCall("bedo_platform.api.web.get_approval_detail", { approval: approvalId }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Approval could not be loaded.");
  }
}

export async function POST(request: Request, { params }: Params) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const { approvalId } = await params;
    const payload = await request.json().catch(() => ({}));
    const method = payload?.with_edits ? "bedo_platform.api.web.approve_srs_approval_with_edits" : "bedo_platform.api.web.approve_srs_approval";
    const data = await frappeCall(method, { approval: approvalId, payload }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Approval could not be completed.");
  }
}
