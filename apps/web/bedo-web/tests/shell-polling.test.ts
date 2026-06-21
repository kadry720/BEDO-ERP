import assert from "node:assert/strict";
import test from "node:test";
import { shellPollIntervals, shouldPollShellWhenVisible } from "../lib/shell-polling";

test("session status polling is not the previous five second hot loop", () => {
  assert.equal(shellPollIntervals.sessionStatusMs, 30000);
  assert.equal(shellPollIntervals.shellStateMs, 300000);
});

test("shell polling pauses while the browser tab is hidden", () => {
  assert.equal(shouldPollShellWhenVisible("visible"), true);
  assert.equal(shouldPollShellWhenVisible("hidden"), false);
});
