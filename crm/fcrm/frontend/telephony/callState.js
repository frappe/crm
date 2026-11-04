// CRM's call state shared between the shell hook, the acts and the call window (#45837 Q8).
import { reactive } from "vue";

/** The app key of CRM's standing window: `shell.windowOf` takes it. */
export const CALL_WINDOW_APP = "crm";

/** What the shell hook learned at idle: the user's enabled media, their default, and a live Exotel call. */
export const callState = reactive({
  media: [],
  defaultMedium: null,
  liveExotel: null,
});

/**
 * Asks the call window to dial `number`: it asks for a medium when the user must choose.
 * The handle exists before the window's code has loaded, so the window reads the request when it mounts.
 * A new `dial` object each time, so the window sees a repeated number as a new request.
 */
export function startOutgoingCall(shell, number) {
  shell.windowOf(CALL_WINDOW_APP).open({ dial: { number } });
}
