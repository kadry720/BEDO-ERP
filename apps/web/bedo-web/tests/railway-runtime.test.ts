import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("Railway web runtime uses Gunicorn instead of the development bench server", () => {
  const script = readFileSync(join(import.meta.dirname, "..", "..", "..", "..", "infrastructure", "railway", "start-web.sh"), "utf-8");

  assert.match(script, /gunicorn/);
  assert.doesNotMatch(script, /bench --site "\$\{FRAPPE_SITE_NAME\}" serve/);
});

test("Railway Gunicorn runtime forces the configured Frappe site header", () => {
  const root = join(import.meta.dirname, "..", "..", "..", "..");
  const script = readFileSync(join(root, "infrastructure", "railway", "start-web.sh"), "utf-8");
  const wrapper = readFileSync(join(root, "infrastructure", "railway", "frappe_wsgi.py"), "utf-8");

  assert.match(script, /export SITES_PATH="\$\{FRAPPE_BENCH_PATH\}\/sites"/);
  assert.match(script, /cd "\$\{SITES_PATH\}"/);
  assert.match(script, /frappe_wsgi:application/);
  assert.match(wrapper, /HTTP_X_FRAPPE_SITE_NAME/);
  assert.match(wrapper, /FRAPPE_SITE_NAME/);
});
