import assert from "node:assert/strict";
import test from "node:test";
import { logoutRedirectUrl } from "../app/api/auth/logout/route";

test("logout redirect uses the browser host instead of 0.0.0.0", () => {
  const request = new Request("http://0.0.0.0:3000/api/auth/logout", {
    headers: {
      host: "172.20.88.65:3000",
    },
  });

  assert.equal(logoutRedirectUrl(request).toString(), "http://172.20.88.65:3000/login");
});
