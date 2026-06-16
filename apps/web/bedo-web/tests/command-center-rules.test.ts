import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  COMMAND_CENTER_CASE_1,
  COMMAND_CENTER_CASE_2,
  COMMAND_CENTER_CASE_3,
  commandCenterDecisionRequiresDeadline,
} from "../features/srs/commandCenterRules";

describe("commandCenterDecisionRequiresDeadline", () => {
  it("requires deadlines for Case 1 and Case 2", () => {
    assert.equal(commandCenterDecisionRequiresDeadline(COMMAND_CENTER_CASE_1), true);
    assert.equal(commandCenterDecisionRequiresDeadline(COMMAND_CENTER_CASE_2), true);
  });

  it("does not require a deadline for Case 3", () => {
    assert.equal(commandCenterDecisionRequiresDeadline(COMMAND_CENTER_CASE_3), false);
  });
});
