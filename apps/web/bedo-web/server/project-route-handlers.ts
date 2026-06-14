import { NextResponse } from "next/server";
import { decodedRouteParam } from "@/lib/route-ids";
import { apiErrorResponse } from "@/server/api-errors";
import { frappeCall } from "@/server/frappe";
import { getSession } from "@/server/session";

export function joinedProjectId(...parts: string[]) {
  return decodedRouteParam(parts.join("/"));
}

export async function getProject(projectId: string) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const project = decodedRouteParam(projectId);
    const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Project could not be loaded.");
  }
}

export async function updateProject(request: Request, projectId: string) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    const project = decodedRouteParam(projectId);
    await frappeCall("bedo_platform.api.web.update_project_details", { project, payload }, session.user);
    const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Project could not be updated.");
  }
}

export async function deleteProject(projectId: string) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const project = decodedRouteParam(projectId);
    await frappeCall("bedo_platform.api.web.delete_project", { project }, session.user);
    return NextResponse.json({ success: true });
  } catch (error) {
    return apiErrorResponse(error, "Project could not be deleted.");
  }
}

export async function listTrainerItems(projectId: string) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const project = decodedRouteParam(projectId);
    const data = await frappeCall("bedo_platform.api.web.list_trainer_items_for_project", { project }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Trainer items could not be loaded.");
  }
}

export async function addTrainerItem(request: Request, projectId: string) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const payload = await request.json();
    const project = decodedRouteParam(projectId);
    await frappeCall("bedo_platform.api.web.add_trainer_item", { project, payload }, session.user);
    const data = await frappeCall("bedo_platform.api.web.list_trainer_items_for_project", { project }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Trainer item could not be saved.");
  }
}

export async function releaseProjectToSrs(projectId: string) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const project = decodedRouteParam(projectId);
    await frappeCall("bedo_platform.api.web.release_project_to_srs", { project }, session.user);
    const projectData = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.get_project_detail", { project }, session.user);
    const items = await frappeCall<Record<string, unknown>>("bedo_platform.api.web.list_trainer_items_for_project", { project }, session.user);
    return NextResponse.json({ ...projectData, ...items });
  } catch (error) {
    return apiErrorResponse(error, "Project could not be released to SRS.");
  }
}

export async function finalizeProjectDetails(projectId: string) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: "Not authenticated." }, { status: 401 });
    const project = decodedRouteParam(projectId);
    await frappeCall("bedo_platform.api.web.finalize_project_details", { project }, session.user);
    const data = await frappeCall("bedo_platform.api.web.get_project_detail", { project }, session.user);
    return NextResponse.json(data);
  } catch (error) {
    return apiErrorResponse(error, "Project details could not be finalized.");
  }
}
