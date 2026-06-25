import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = join(import.meta.dirname, "..");

function source(...segments: string[]) {
  return readFileSync(join(root, ...segments), "utf-8");
}

test("permanent dialog primitive uses a document-body portal and focus/scroll management", () => {
  const dialogPath = join(root, "components", "ui", "Dialog.tsx");

  assert.equal(existsSync(dialogPath), true);
  const dialog = source("components", "ui", "Dialog.tsx");
  assert.match(dialog, /createPortal/);
  assert.match(dialog, /document\.body/);
  assert.match(dialog, /aria-modal="true"/);
  assert.match(dialog, /overflow = "hidden"/);
  assert.match(dialog, /focusableSelectors/);
  assert.match(dialog, /event\.key === "Tab"/);
  assert.match(dialog, /event\.key === "Escape"/);
});

test("dialog backdrop cannot close while users interact with modal controls", () => {
  const dialog = source("components", "ui", "Dialog.tsx");

  assert.doesNotMatch(dialog, /<button className="absolute inset-0 cursor-default"/);
  assert.match(dialog, /data-dialog-backdrop/);
  assert.doesNotMatch(dialog, /onMouseDown=/);
  assert.doesNotMatch(dialog, /event\.target === event\.currentTarget/);
  assert.match(dialog, /relative z-10 flex max-h-\[92vh\]/);
});

test("dialog focus setup is stable across parent rerenders", () => {
  const dialog = source("components", "ui", "Dialog.tsx");

  assert.match(dialog, /onCloseRef = useRef\(onClose\)/);
  assert.match(dialog, /onCloseRef\.current = onClose/);
  assert.match(dialog, /onCloseRef\.current\(\)/);
  assert.doesNotMatch(dialog, /\[initialFocus, mounted, onClose\]/);
  assert.match(dialog, /\[initialFocus, mounted\]/);
});

test("workflow dialogs and confirmation dialogs reuse the permanent dialog primitive", () => {
  assert.match(source("components", "workflow", "WorkflowActionDialog.tsx"), /from "@\/components\/ui\/Dialog"/);
  assert.match(source("features", "approvals", "ApprovalsPage.tsx"), /from "@\/components\/ui\/Dialog"/);
  assert.match(source("features", "admin", "AdminUsersDashboard.tsx"), /from "@\/components\/ui\/Dialog"/);
});
