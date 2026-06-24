import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = join(import.meta.dirname, "..");

function source(...segments: string[]) {
  return readFileSync(join(root, ...segments), "utf-8");
}

function objectKeysFrom(sourceText: string, constName: string) {
  const match = sourceText.match(new RegExp(`(?:export\\s+)?const\\s+${constName}[\\s\\S]*?=\\s*\\{([\\s\\S]*?)\\n\\};`));
  assert.ok(match, `Expected ${constName} object to exist`);
  return Array.from(match[1].matchAll(/^\s*(?:"([^"]+)"|([A-Z0-9_]+))\s*:/gm), (item) => item[1] || item[2]);
}

test("baseline SRS workflow geometry, lanes, routes, and actions are protected", () => {
  const presentation = source("features", "srs", "workflowPresentation.ts");
  const workspace = source("features", "srs", "TrainerWorkspace.tsx");
  const route = source("app", "api", "srs", "workflow", "route.ts");

  assert.deepEqual(objectKeysFrom(presentation, "NODE_POSITIONS"), [
    "PRODUCT_DIGITAL_RELEASE",
    "SRS_GATEWAY",
    "MANDATORY_COORDINATION_MEETING",
    "DELIVERABLES_MATRIX",
    "DUAL_GATE_APPROVAL",
    "DEADLINE_LOCKED_IN_ERP",
    "ACTION_PATHS",
    "CASE_1",
    "CASE_2",
    "CASE_3",
    "CASE_4",
    "GATE_2_PMDP",
    "PMDP_DUAL_GATE_APPROVAL",
    "BMDP",
    "PHYSICAL_BUILD_TEST",
    "EXTENSION_DEADLINE",
    "SRS_DIRECTOR_APPROVAL",
    "PMDP",
  ]);
  assert.equal(objectKeysFrom(presentation, "CONNECTOR_ROUTES").length, 21);
  assert.match(presentation, /id: "deadline_1"/);
  assert.match(presentation, /id: "deadline_2"/);
  assert.match(presentation, /id: "deadline_3"/);
  assert.match(presentation, /id: "deadline_4"/);

  for (const nodeId of [
    "CASES_1_2",
    "CASES_3_4",
    "GM_APPROVAL",
    "GATE_1_SRS_MANAGER_APPROVAL",
    "DUAL_GATE_APPROVAL",
    "PMDP_DUAL_GATE_APPROVAL",
    "EXTENSION_DEADLINE",
    "SRS_DIRECTOR_APPROVAL",
    "FINAL_GM_APPROVAL",
    "ACTION_PATHS",
    "DEADLINE_LOCKED_IN_ERP",
    "CASE_1",
    "CASE_2",
    "CASE_3",
    "CASE_4",
  ]) {
    assert.match(workspace, new RegExp(`"${nodeId}"`));
  }

  for (const action of [
    "submit_deliverables",
    "submit_pmdp_gate",
    "request_pmdp_extension",
    "submit_pmdp",
    "submit_bmdp",
    "submit_command_center",
  ]) {
    assert.match(workspace, new RegExp(`"${action}"`));
  }

  assert.match(workspace, /fetch\("\/api\/srs\/workflow"/);
  assert.match(route, /bedo_platform\.api\.web\.submit_srs_deliverables_matrix/);
  assert.match(route, /bedo_platform\.api\.web\.submit_srs_bmdp_path/);
});

test("baseline ARD workflow geometry, routes, actions, and interruption payload keys are protected", () => {
  const workspace = source("features", "ard", "ArdWorkspace.tsx");
  const route = source("app", "api", "ard", "workflow", "route.ts");

  assert.deepEqual(objectKeysFrom(workspace, "ARD_NODE_POSITIONS"), [
    "HANDOVER_COMPLETE",
    "INTERNAL_ARD_SYNC_MEETING",
    "ARD_PROJECT_OWNER_ASSIGNMENT",
    "ARD_TEAM_SELECTION",
    "PROGRESS_REVIEW_MEETING",
    "GM_APPROVAL",
    "COMMAND_CENTER_PROCUREMENT_CONFIRMATION",
    "ELECTRONICS_SYSTEM_DESIGN",
    "CONCEPT_PROOF_PROTOTYPING",
    "SCMDP_SUBMISSION",
  ]);
  assert.equal(objectKeysFrom(workspace, "ARD_CONNECTOR_ROUTES").length, 12);

  for (const action of [
    "schedule_internal_sync",
    "complete_internal_sync",
    "assign_owner",
    "select_team",
    "progress_review",
    "request_interruption",
    "confirm_procurement",
    "choose_electronics_subcase",
    "complete_electronics",
    "complete_concept_proof",
    "submit_scmdp",
  ]) {
    assert.match(workspace, new RegExp(`"${action}"`));
  }

  for (const key of [
    "procurement_notes",
    "procurement_bom_path",
    "electronics_notes",
    "electronics_bom_path",
    "concept_notes",
    "concept_report_path",
  ]) {
    assert.match(workspace, new RegExp(`${key}:`));
  }

  assert.match(workspace, /fetch\("\/api\/ard\/workflow"/);
  assert.match(route, /bedo_platform\.api\.web\.schedule_ard_internal_sync_meeting/);
  assert.match(route, /bedo_platform\.api\.web\.submit_ard_scmdp/);
});

test("baseline route and BFF files remain present", () => {
  for (const path of [
    ["app", "(app)", "gm", "page.tsx"],
    ["app", "(app)", "srs", "page.tsx"],
    ["app", "(app)", "ard", "page.tsx"],
    ["app", "(app)", "command-center", "page.tsx"],
    ["app", "(app)", "meetings", "page.tsx"],
    ["app", "(app)", "notifications", "page.tsx"],
    ["app", "(app)", "approvals", "page.tsx"],
    ["app", "api", "meetings", "[meetingId]", "confirm", "route.ts"],
    ["app", "api", "notifications", "route.ts"],
    ["app", "api", "approvals", "[approvalId]", "route.ts"],
    ["app", "api", "session", "shell-state", "route.ts"],
  ]) {
    assert.equal(existsSync(join(root, ...path)), true, `Expected ${path.join("/")} to exist`);
  }
});

test("baseline meeting, notification, approval, and shell payload contracts are protected", () => {
  const meetings = source("features", "meetings", "MeetingsPage.tsx");
  const notifications = source("features", "notifications", "NotificationsPage.tsx");
  const approvalRoute = source("app", "api", "approvals", "[approvalId]", "route.ts");
  const shell = source("components", "Shell.tsx");

  assert.match(meetings, /\/api\/meetings\/\$\{routeSegment\(meeting\.name\)\}\/confirm/);
  assert.match(meetings, /selected_users: selectedUsers/);
  assert.match(notifications, /"mark_read" \| "mark_unread" \| "mark_all_read"/);
  assert.match(notifications, /normalizeProjectActionUrl/);
  assert.match(approvalRoute, /export async function GET/);
  assert.match(approvalRoute, /export async function POST/);
  assert.match(shell, /\/api\/session\/shell-state/);
  assert.match(shell, /\/api\/session\/status/);
  assert.match(shell, /\/api\/session\/conflict/);
  assert.match(shell, /\/api\/auth\/logout/);
});
