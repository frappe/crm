// CRM's call state shared between the shell hook, the act and the call window (#45837 Q8).
import { reactive } from "vue";
import { __ } from "frappe/i18n";

/** What the shell hook learned at idle: the user's enabled media, their default, and a live Exotel call. */
export const callState = reactive({
  media: [],
  defaultMedium: null,
  liveExotel: null,
});

let starter = null;

/** The call window registers how a call starts; the returned function unregisters it. */
export function registerOutgoingStarter(start) {
  starter = start;
  return () => {
    if (starter === start) starter = null;
  };
}

/** Starts an outgoing call to `number`: the window opens, asks for a medium when the user must choose, and dials. */
export function startOutgoingCall(number) {
  // The media land before the window's code has loaded and mounted.
  if (!starter) throw new Error(__("The call window is still loading. Try again in a moment."));
  return starter(number);
}
