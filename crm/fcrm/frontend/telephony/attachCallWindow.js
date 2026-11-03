// The shell hook's gate: one request at idle, and the window only for a user with a medium CRM can draw.
import { callState } from "./callState.js";

/** `loadWindow` is `() => import('./CallWindow.vue')`, so a user without telephony never loads the window's code. */
export async function attachCallWindow(shell, { callingMedia, loadWindow }) {
  const { media, default_medium, live_exotel_call } = await callingMedia();
  if (!media.length) return;
  Object.assign(callState, {
    media,
    defaultMedium: default_medium,
    liveExotel: live_exotel_call,
  });
  const { default: CallWindow } = await loadWindow();
  return shell.window(CallWindow, { icon: "lucide-phone", width: 260 });
}
