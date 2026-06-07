import { NextResponse } from "next/server";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export function joinedProjectId(...parts: string[]) {
  return parts.join("/");
}

export async function getProject(projectId: string) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  return NextResponse.json(data);
}

export async function updateProject(request: Request, projectId: string) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const payload = await request.json();
  await frappeCall("bedo_platform.api.web.update_project_details", { project: projectId, payload }, session.user);
  const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  return NextResponse.json(data);
}

export async function deleteProject(projectId: string) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  await frappeCall("bedo_platform.api.web.delete_project", { project: projectId }, session.user);
  return NextResponse.json({ success: true });
}

export async function listTrainerItems(projectId: string) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const data = await frappeCall("bedo_platform.api.web.list_trainer_items_for_project", { project: projectId }, session.user);
  return NextResponse.json(data);
}

export async function addTrainerItem(request: Request, projectId: string) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  const payload = await request.json();
  await frappeCall("bedo_platform.api.web.add_trainer_item", { project: projectId, payload }, session.user);
  const data = await frappeCall("bedo_platform.api.web.list_trainer_items_for_project", { project: projectId }, session.user);
  return NextResponse.json(data);
}

export async function releaseProjectToSrs(projectId: string) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  await frappeCall("bedo_platform.api.web.release_project_to_srs", { project: projectId }, session.user);
  const project = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  const items = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.list_trainer_items_for_project", { project: projectId }, session.user);
  return NextResponse.json({ ...project, ...items });
}

export async function finalizeProjectDetails(projectId: string) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
  await frappeCall("bedo_platform.api.web.finalize_project_details", { project: projectId }, session.user);
  const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project: projectId }, session.user);
  return NextResponse.json(data);
}
