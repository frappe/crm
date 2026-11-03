// The Twilio call's state machine: one device per tab, one call at a time. No DOM, so a test drives it with the fake `Device`.
import { reactive } from "vue";
import { __ } from "frappe/i18n";
import { lookupContact } from "./contactRecord.js";

const DEVICE_OPTIONS = {
  codecPreferences: ["opus", "pcmu"],
  fakeLocalDTMF: true,
  enableRingingState: true,
};
const LIVE = ["incoming", "ringing", "oncall"];

/**
 * `api` is `{ token, contact, link }`; `loadDevice(tokenData)` gives the `Device` class.
 * `step` is idle, incoming, ringing (we dialled), oncall or ended (the card stays for a note and a task).
 */
export function createTwilioCall({ api, loadDevice }) {
  const state = reactive({
    step: "idle",
    contact: null,
    muted: false,
    seconds: 0,
    callSid: "",
    error: "",
  });
  let device = null;
  let call = null;
  let incoming = false;
  let startedAt = 0;
  let timer = null;
  let connecting = false;
  let destroyed = false;

  function tick() {
    state.seconds = Math.floor((Date.now() - startedAt) / 1000);
  }

  function stopTimer() {
    clearInterval(timer);
    timer = null;
  }

  async function start() {
    try {
      const tokenData = await api.token();
      if (!tokenData?.token)
        throw new Error(tokenData?.detail || __("No access token"));
      const Device = await loadDevice(tokenData);
      if (destroyed) return;
      device = new Device(tokenData.token, DEVICE_OPTIONS);
      device.on("incoming", onIncoming);
      device.on("error", (error) => (state.error = error.message));
      device.on("tokenWillExpire", refreshToken);
      if (tokenData.mock && typeof window !== "undefined") {
        window.__crmTelephonyMock = { ...window.__crmTelephonyMock, makeCall };
      }
      await device.register();
    } catch (error) {
      state.error = error.message;
      console.error("[crm] The Twilio device did not start.", error);
    }
  }

  async function refreshToken() {
    try {
      const tokenData = await api.token();
      if (!tokenData?.token) throw new Error(tokenData?.detail);
      device.updateToken(tokenData.token);
    } catch (error) {
      state.error = error.message || "The access token did not refresh";
      console.error("[crm] The Twilio token did not refresh.", error);
    }
  }

  function begin(next, number, isIncoming) {
    call = next;
    incoming = isIncoming;
    Object.assign(state, {
      step: isIncoming ? "incoming" : "ringing",
      muted: false,
      seconds: 0,
      callSid: "",
    });
    state.contact = { name: "", image: "", number, record: null };
    lookup(number);
    // A late event of a call that is over must not touch the next one.
    call.on("accept", () => {
      if (next !== call) return;
      if (incoming) connected();
      else state.callSid = sid();
    });
    if (!isIncoming)
      call.on(
        "messageReceived",
        ({ content }) =>
          next === call && content?.CallStatus === "in-progress" && connected()
      );
    for (const event of ["disconnect", "cancel", "reject"])
      call.on(event, () => finish(next));
  }

  function sid() {
    return call?.parameters?.CallSid || "";
  }

  function onIncoming(next) {
    // One call at a time: a second caller hears busy, and the call just ended gives way.
    if (connecting || LIVE.includes(state.step)) return next.reject();
    begin(next, next.parameters.From, true);
  }

  async function makeCall(number) {
    if (!device || connecting || LIVE.includes(state.step)) return;
    connecting = true;
    try {
      const next = await device.connect({ params: { To: number } });
      begin(next, number, false);
    } catch (error) {
      state.error = error.message;
      throw error;
    } finally {
      connecting = false;
    }
  }

  function connected() {
    if (!call || (state.step !== "incoming" && state.step !== "ringing"))
      return;
    state.step = "oncall";
    state.callSid = sid();
    startedAt = Date.now();
    stopTimer();
    timer = setInterval(tick, 1000);
  }

  function finish(finished) {
    if (finished !== call) return;
    stopTimer();
    if (state.step === "oncall") {
      tick();
      state.step = "ended";
      state.muted = false;
    } else {
      state.step = "idle";
      state.contact = null;
    }
    call = null;
  }

  async function lookup(number) {
    try {
      const contact = await lookupContact(api, number);
      if (state.contact?.number === number) state.contact = contact;
    } catch (error) {
      console.error("[crm] The caller lookup failed.", error);
    }
  }

  return {
    state,
    start,
    makeCall,
    accept: () => call?.accept(),
    reject: () => call?.reject(),
    hangUp: () => call?.disconnect(),
    toggleMute() {
      call.mute(!call.isMuted());
      state.muted = call.isMuted();
    },
    /** The card's close after a call: back to idle. */
    dismiss() {
      if (state.step === "ended")
        Object.assign(state, { step: "idle", contact: null, callSid: "" });
    },
    /** Links a note or task the user made during the call to the call's log; `callSid` is read before the form opened. */
    linkToCall(callSid, doctype, doc) {
      if (!callSid || !doc?.name) return;
      return api.link(callSid, doctype, doc.name);
    },
    isLive: () => LIVE.includes(state.step),
    destroy() {
      destroyed = true;
      stopTimer();
      device?.destroy();
      device = null;
      call = null;
    },
  };
}

export function formatClock(seconds) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(Math.floor(seconds / 60))}:${pad(seconds % 60)}`;
}
