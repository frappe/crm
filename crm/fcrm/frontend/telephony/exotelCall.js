// The Exotel call's state machine: the call lives on the agent's phone, so the window only follows `exotel_call` events. No DOM.
import { reactive } from "vue";
import { lookupContact } from "./contactRecord.js";

const LIVE = ["incoming", "ringing", "oncall"];
const OUTGOING = ["outbound-api", "outbound-dial"];
const UNANSWERED = ["no-answer", "busy", "failed"];

/** What one `exotel_call` payload says: `{ phase, incoming, number, seconds }`, or null for an event that changes nothing. */
export function readExotelEvent(payload) {
  const seconds =
    parseInt(payload["Legs[0][OnCallDuration]"]) ||
    parseInt(payload.DialCallDuration) ||
    0;
  if (payload.Direction === "incoming") {
    const event = {
      incoming: true,
      number: payload.CallFrom || payload.From,
      seconds,
    };
    const { CallType, DialCallStatus } = payload;
    if (payload.EventType === "Dial" && payload.Status === "busy")
      return { ...event, phase: "ringing" };
    if (CallType === "incomplete" && DialCallStatus === "no-answer")
      return { ...event, phase: "noanswer" };
    if (CallType === "client-hangup" && DialCallStatus === "canceled")
      return { ...event, phase: "noanswer" };
    if (CallType === "completed" && DialCallStatus === "completed")
      return { ...event, phase: "ended" };
    return null;
  }
  if (!OUTGOING.includes(payload.Direction)) return null;
  const event = { incoming: false, number: payload.To, seconds };
  if (payload.EventType === "answered" && payload.Status === "in-progress")
    return {
      ...event,
      phase:
        payload["Legs[1][Status]"] === "in-progress" ? "oncall" : "customer",
    };
  if (payload.EventType !== "terminal") return null;
  if (payload.Status === "completed") return { ...event, phase: "ended" };
  if (UNANSWERED.includes(payload.Status))
    return { ...event, phase: "noanswer" };
  return null;
}

/**
 * `api` is `{ call, contact }`; `socket` carries the user's `exotel_call` events (the server sends them to that user only).
 * `step` is idle, incoming, ringing (we dialled), oncall or ended (the card stays for a note and a task);
 * `outcome` is "noanswer" for an ended call nobody took, `customerRinging` once our phone answered.
 */
export function createExotelCall({ api, socket }) {
  const state = reactive({
    step: "idle",
    contact: null,
    seconds: 0,
    callSid: "",
    outcome: "",
    customerRinging: false,
    error: "",
  });
  let startedAt = 0;
  let timer = null;
  let dialling = false;
  let held = [];

  function tick() {
    state.seconds = Math.floor((Date.now() - startedAt) / 1000);
  }

  function stopTimer() {
    clearInterval(timer);
    timer = null;
  }

  function startTimer(already = 0) {
    startedAt = Date.now() - already * 1000;
    tick();
    stopTimer();
    timer = setInterval(tick, 1000);
  }

  function begin(step, number, callSid) {
    stopTimer();
    Object.assign(state, {
      step,
      seconds: 0,
      callSid,
      outcome: "",
      customerRinging: false,
      contact: { name: "", image: "", number, record: null },
    });
    lookup(number);
  }

  async function lookup(number) {
    try {
      const contact = await lookupContact(api, number);
      if (state.contact?.number === number) state.contact = contact;
    } catch (error) {
      console.error("[crm] The caller lookup failed.", error);
    }
  }

  function apply(payload) {
    const event = readExotelEvent(payload);
    if (!event) return;
    const sid = payload.CallSid;
    const idle = !LIVE.includes(state.step);
    // One call at a time. Events of a call this tab did not start are ours only when it rings in.
    if (idle && event.phase === "ringing" && event.incoming)
      return begin("incoming", event.number, sid);
    if (idle || sid !== state.callSid) return;
    if (event.phase === "customer") state.customerRinging = true;
    else if (event.phase === "oncall") {
      state.step = "oncall";
      state.customerRinging = false;
      startTimer();
    } else if (event.phase === "ended" || event.phase === "noanswer") {
      stopTimer();
      state.seconds = event.seconds || (startedAt ? state.seconds : 0);
      state.outcome = event.phase === "noanswer" ? "noanswer" : "";
      state.step = "ended";
    }
  }

  function onEvent(payload) {
    if (dialling) held.push(payload);
    else apply(payload);
  }

  return {
    state,
    start() {
      socket?.on("exotel_call", onEvent);
    },
    /** Dials `number` through Exotel; events that arrive before the answer names the call wait for it. */
    async makeCall(number) {
      if (dialling || LIVE.includes(state.step)) return;
      dialling = true;
      held = [];
      begin("ringing", number, "");
      try {
        const details = await api.call(number);
        state.callSid = details.CallSid;
        if (details.call_log_creation_failed)
          state.error = "The call connected, but its log was not saved";
      } catch (error) {
        Object.assign(state, { step: "idle", contact: null });
        state.error = error.message;
        throw error;
      } finally {
        dialling = false;
      }
      held.forEach(apply);
      held = [];
    },
    /** The idle request's live call, after a reload: the phone call went on while the tab was gone. */
    restore(live) {
      begin(live.incoming ? "incoming" : "ringing", live.number, live.call_sid);
      if (live.status === "In Progress") {
        state.step = "oncall";
        startTimer(live.seconds || 0);
      }
    },
    /** The card's close after a call: back to idle. */
    dismiss() {
      if (state.step === "ended")
        Object.assign(state, { step: "idle", contact: null, callSid: "" });
    },
    linkToCall(callSid, doctype, doc) {
      if (!callSid || !doc?.name) return;
      return api.link(callSid, doctype, doc.name);
    },
    isLive: () => LIVE.includes(state.step),
    destroy() {
      stopTimer();
      socket?.off("exotel_call", onEvent);
    },
  };
}
