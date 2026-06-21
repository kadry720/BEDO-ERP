import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("Vercel functions are pinned near the Railway Europe target and use Fluid Compute", () => {
  const config = JSON.parse(readFileSync(join(import.meta.dirname, "..", "vercel.json"), "utf-8"));

  assert.deepEqual(config.regions, ["fra1"]);
  assert.equal(config.fluid, true);
});
