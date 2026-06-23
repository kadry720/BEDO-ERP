import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("workflow path submission forms do not expose file browse controls", () => {
  const source = readFileSync(join(import.meta.dirname, "..", "features", "srs", "TrainerWorkspace.tsx"), "utf-8");

  assert.doesNotMatch(source, /Browse local file/);
  assert.doesNotMatch(source, /type="file"/);
  assert.doesNotMatch(source, /file picker/);
});

test("copy path buttons expose success and failure feedback", () => {
  const srsSource = readFileSync(join(import.meta.dirname, "..", "features", "srs", "TrainerWorkspace.tsx"), "utf-8");
  const ardSource = readFileSync(join(import.meta.dirname, "..", "features", "ard", "ArdWorkspace.tsx"), "utf-8");

  assert.match(srsSource, /copyStatus/);
  assert.match(srsSource, /Copy failed/);
  assert.match(ardSource, /copyStatus/);
  assert.match(ardSource, /Copy failed/);
});
