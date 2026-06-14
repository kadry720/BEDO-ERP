export const COMMAND_CENTER_CASE_1 = "Case 1 - Save for later";
export const COMMAND_CENTER_CASE_2 = "Case 2 - Buy Critical Components then deliver to ARD";
export const COMMAND_CENTER_CASE_3 = "Case 3 - Deliver to ARD directly";

export const commandCenterCases = [
  {
    value: COMMAND_CENTER_CASE_1,
    label: "Case 1",
    description: "Save for later",
  },
  {
    value: COMMAND_CENTER_CASE_2,
    label: "Case 2",
    description: "Buy Critical Components then deliver to ARD",
  },
  {
    value: COMMAND_CENTER_CASE_3,
    label: "Case 3",
    description: "Deliver to ARD directly",
  },
];

export function commandCenterDecisionRequiresDeadline(commandCase: string) {
  return commandCase !== COMMAND_CENTER_CASE_3;
}
