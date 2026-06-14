import { NextResponse } from "next/server";
import { decodedRouteParam } from "@/lib/route-ids";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

type Params = { params: Promise<{ supplierFileId: string }> };

export async function POST(_request: Request, { params }: Params) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const { supplierFileId } = await params;
    const supplierFile = decodedRouteParam(supplierFileId);
    const result = await frappeCall<{ trainer_item: string }>("bedo_platform.api.web.deliver_supplier_file", { supplier_file: supplierFile }, session.user);
    const data = await frappeCall("bedo_platform.api.web.get_trainer_item_workspace", { trainer_item: result.trainer_item }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Supplier file could not be delivered.");
  }
}
