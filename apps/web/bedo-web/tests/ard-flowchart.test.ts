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
