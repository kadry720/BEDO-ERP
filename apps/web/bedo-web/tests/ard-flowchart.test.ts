import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("ARD flowchart BFF route uses signed Frappe flowchart method", () => {
  const route = join(import.meta.dirname, "..", "app", "api", "ard", "flowchart", "route.ts");

  assert.equal(existsSync(route), true);
  assert.match(readFileSync(route, "utf-8"), /bedo_platform\.api\.web\.get_ard_flowchart_definition/);
});

test("ARD project route renders the ARD workspace for trainer item routes", () => {
  const route = join(import.meta.dirname, "..", "app", "(app)", "ard", "project", "[...parts]", "page.tsx");
  const source = readFileSync(route, "utf-8");

  assert.equal(existsSync(route), true);
  assert.match(source, /loadArdWorkspaceOrForbidden/);
  assert.match(source, /<ArdWorkspace/);
});

test("ARD project route uses ARD project detail instead of SRS project detail", () => {
  const route = join(import.meta.dirname, "..", "app", "(app)", "ard", "project", "[...parts]", "page.tsx");
  const source = readFileSync(route, "utf-8");

  assert.match(source, /loadArdProjectDetailOrForbidden/);
  assert.match(source, /<ArdProjectDetail/);
  assert.doesNotMatch(source, /features\/srs\/ProjectDetail/);
});

test("ARD project detail screen exposes ARD workflow columns and no SRS approval labels", () => {
  const component = join(import.meta.dirname, "..", "features", "ard", "ArdProjectDetail.tsx");

  assert.equal(existsSync(component), true);
  const source = readFileSync(component, "utf-8");
  assert.match(source, /ARD Project Owner/);
  assert.match(source, /ARD Team/);
  assert.match(source, /Current ARD Step/);
  assert.match(source, /Open Workflow/);
  assert.doesNotMatch(source, /Awaiting SRS Manager Approval/);
  assert.doesNotMatch(source, /Awaiting GM Approval/);
});

test("ARD project detail table keeps SRS table proportions and single-line actions", () => {
  const component = join(import.meta.dirname, "..", "features", "ard", "ArdProjectDetail.tsx");
  const source = readFileSync(component, "utf-8");

  assert.match(source, /min-w-\[860px\]/);
  assert.match(source, /whitespace-nowrap/);
  assert.match(source, /Open Workflow/);
  assert.doesNotMatch(source, /Open ARD Workflow/);
});

test("ARD workspace component exposes core node actions", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "ard", "ArdWorkspace.tsx"), "utf-8");

  assert.match(source, /INTERNAL_ARD_SYNC_MEETING/);
  assert.match(source, /ARD_PROJECT_OWNER_ASSIGNMENT/);
  assert.match(source, /ARD_TEAM_SELECTION/);
  assert.match(source, /PROGRESS_REVIEW_MEETING/);
  assert.match(source, /SCMDP_SUBMISSION/);
  assert.match(source, /schedule_internal_sync/);
  assert.match(source, /assign_owner/);
  assert.match(source, /select_team/);
  assert.match(source, /request_interruption/);
  assert.match(source, /choose_electronics_subcase/);
  assert.match(source, /submit_scmdp/);
});

test("ARD workspace uses the SRS canvas flowchart pattern instead of the old card grid", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "ard", "ArdWorkspace.tsx"), "utf-8");

  assert.match(source, /useLayoutEffect/);
  assert.match(source, /frameRef/);
  assert.match(source, /ARD_FLOWCHART_DIMENSIONS/);
  assert.match(source, /ARD_NODE_POSITIONS/);
  assert.match(source, /ARD_CONNECTOR_ROUTES/);
  assert.match(source, /function ArdFlowchart/);
  assert.match(source, /function FlowNode/);
  assert.match(source, /function NodeModal/);
  assert.match(source, /fixed inset-0 z-50/);
  assert.match(source, /marker id="ard-arrow"/);
  assert.doesNotMatch(source, /grid gap-5 xl:grid-cols-\[1fr_420px\]/);
  assert.doesNotMatch(source, /<aside className="space-y-5">/);
});

test("ARD workflow BFF route uses signed Frappe mutation methods", () => {
  const route = join(import.meta.dirname, "..", "app", "api", "ard", "workflow", "route.ts");
  const source = readFileSync(route, "utf-8");

  assert.equal(existsSync(route), true);
  assert.match(source, /bedo_platform\.api\.web\.schedule_ard_internal_sync_meeting/);
  assert.match(source, /bedo_platform\.api\.web\.complete_ard_internal_sync_meeting/);
  assert.match(source, /bedo_platform\.api\.web\.assign_ard_project_owner/);
  assert.match(source, /bedo_platform\.api\.web\.select_ard_team/);
  assert.match(source, /bedo_platform\.api\.web\.submit_ard_progress_review_outcome/);
  assert.match(source, /bedo_platform\.api\.web\.submit_ard_interruption_request/);
  assert.match(source, /bedo_platform\.api\.web\.choose_ard_electronics_subcase/);
  assert.match(source, /bedo_platform\.api\.web\.complete_ard_concept_proof/);
  assert.match(source, /bedo_platform\.api\.web\.submit_ard_scmdp/);
});
