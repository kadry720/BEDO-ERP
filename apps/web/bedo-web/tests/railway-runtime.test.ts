import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("Railway web runtime uses Gunicorn instead of the development bench server", () => {
  const script = readFileSync(join(import.meta.dirname, "..", "..", "..", "..", "infrastructure", "railway", "start-web.sh"), "utf-8");

  assert.match(script, /gunicorn/);
  assert.doesNotMatch(script, /bench --site "\$\{FRAPPE_SITE_NAME\}" serve/);
});
