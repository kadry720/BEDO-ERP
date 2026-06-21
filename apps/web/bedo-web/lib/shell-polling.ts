export const shellPollIntervals = {
  sessionStatusMs: 30000,
  shellStateMs: 300000,
} as const;

export function shouldPollShellWhenVisible(visibilityState: DocumentVisibilityState | string | undefined) {
  return visibilityState !== "hidden";
}
