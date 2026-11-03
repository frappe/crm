// The shell hook's gate: one request at idle, and the window only for a user with a medium CRM can draw.

// Exotel joins with #46118; until then an Exotel-only user gets no window.
const DRAWN_MEDIA = ["Twilio"];

/** `loadWindow` is `() => import('./CallWindow.vue')`, so a user without telephony never loads the window's code. */
export async function attachCallWindow(shell, { callingMedia, loadWindow }) {
  const { media } = await callingMedia();
  if (!media.some((medium) => DRAWN_MEDIA.includes(medium))) return;
  const { default: CallWindow } = await loadWindow();
  return shell.window(CallWindow, { icon: "lucide-phone", width: 260 });
}
