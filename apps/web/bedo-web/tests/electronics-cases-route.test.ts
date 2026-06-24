import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = join(import.meta.dirname, "..");

function source(...segments: string[]) {
  return readFileSync(join(root, ...segments), "utf-8");
}

test("SRS Electronics Section Head has a dedicated ARD Electronics Cases route", () => {
  const pagePath = join(root, "app", "(app)", "srs", "ard-electronics-cases", "page.tsx");
  const apiPath = join(root, "app", "api", "srs", "ard-electronics-cases", "route.ts");

  assert.equal(existsSync(pagePath), true);
  assert.equal(existsSync(apiPath), true);
  assert.match(source("app", "api", "srs", "ard-electronics-cases", "route.ts"), /list_srs_electronics_ard_cases/);
  assert.match(source("app", "(app)", "srs", "ard-electronics-cases", "page.tsx"), /ElectronicsCasesPage/);
});

test("Electronics Cases navigation is shown only for the exact capability role", () => {
  const shell = source("components", "Shell.tsx");

  assert.match(shell, /SRS Electronics Section Head/);
  assert.match(shell, /\/srs\/ard-electronics-cases/);
  assert.match(shell, /ARD Electronics Cases/);
  assert.match(shell, /sort\(\(left, right\) => right\.href\.length - left\.href\.length\)/);
  assert.doesNotMatch(shell, /srselectronicshead/);
});
