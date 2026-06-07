import { NextResponse } from "next/server";
import { getSession } from "@/server/session";

export async function POST() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  return NextResponse.json(
    { error: "Legacy project assignment is disabled in the SRS phase. Use the SRS workflow endpoints." },
    { status: 410 }
  );
}
