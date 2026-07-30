# 📞 Avaya Integration — Requirements & Technical Discovery

| | |
|---|---|
| 🖋️ **Prepared by** | Tiberbu — CRM Engineering |
| 🎧 **Audience** | Avaya Engineering / Integration team |
| 📦 **Product** | Tiberbu CRM (customer-relationship & support platform for the Careverse HMIS) |
| 📝 **Document status** | Draft v0.1 — for discovery & alignment |
| 📅 **Date** | 2026-07-29 |

---

## 📌 1. Purpose of this document

Tiberbu is integrating its CRM with Avaya so that **every customer call is placed, received, screen-popped, recorded, and logged inside the CRM**, and so that call events can drive automated customer-support workflows. Tiberbu operates (or plans to operate) Avaya in **both on-premise and cloud forms**, and the CRM will support both behind a single configuration switch.

This document (a) states Tiberbu's integration **requirements**, (b) describes the **integration model** the CRM expects, and (c) lists the **information and access we need from Avaya Engineering** to build and certify the integration. Sections marked **[NEEDS AVAYA CONFIRMATION]** are our current understanding of Avaya capabilities that we ask your team to validate or correct — we do not want to assume API behavior on your platform.

---

## 🏥 2. Business context (brief)

- Tiberbu provides **Careverse**, a FHIR-ready Health Information Management System for the Kenyan healthcare market.
- The CRM manages the **sales pipeline** (selling/deploying Careverse to facilities) and the **customer-support journey** (onboarding, tickets, SLAs) for live customers.
- Support is delivered through an **Avaya contact-centre**. Today those calls are disconnected from the customer record. The integration closes that gap.

---

## 🎯 3. Integration goals

| # | Goal | Outcome |
|---|---|---|
| G1 | **Click-to-dial** | An agent clicks a phone number on a customer record in the CRM and Avaya places the call. |
| G2 | **Inbound screen-pop** | On an inbound call, the CRM identifies the caller and shows the matching customer record to the answering agent **before/at** answer. |
| G3 | **Automatic call logging** | Every call (in/out, answered/missed) is written to the CRM against the right customer, with direction, timestamps, duration, and final disposition/status. |
| G4 | **Call recording access** | The CRM can retrieve/stream the recording of a logged call for authorized users, subject to consent/retention policy. |
| G5 | **Event-driven automation** | Call outcomes (e.g. missed call, completed call) can trigger CRM workflows (callback tasks, SLA timers, notifications). |
| G6 | **Dual deployment** | The same CRM integration supports **Avaya on-premise** and **Avaya cloud**, selectable by configuration. |

---

## 🚀 4. Deployment modes the CRM must support

The CRM ships a single "Avaya" connector with a **mode** switch. We need Avaya's guidance on the correct product/API surface for each.

### 🖥️ 4.1 Mode A — On-premise (Avaya Aura family) **[NEEDS AVAYA CONFIRMATION]**

Our understanding of the likely integration surface:

- **Avaya Aura Communication Manager (CM)** for call processing.
- **Avaya Aura Application Enablement Services (AES)** exposing CTI via **TSAPI**, **DMCC**, and/or **JTAPI** for call events and call control.
- **Recording** via an on-premise recorder (e.g. **Avaya Contact Recorder / Avaya Workforce Optimization**, or a SIPREC/DMCC-service-observe based recorder), producing a retrievable recording reference.

**We need Avaya to confirm:** which CTI interface you recommend (TSAPI vs DMCC vs JTAPI vs a newer API), whether a supported **connector/adapter/SDK** exists that we can run server-side, and how recordings are exposed for programmatic retrieval.

### ☁️ 4.2 Mode B — Cloud (Avaya Experience Platform / AXP) **[NEEDS AVAYA CONFIRMATION]**

Our understanding:

- **Avaya Experience Platform (AXP)** provides **REST APIs** and **webhooks/notifications** for call lifecycle events, and cloud-hosted **media/recording** access.

**We need Avaya to confirm:** the REST API base/regions, the auth model, the webhook/notification catalog for call lifecycle, click-to-dial (originate) endpoints, and recording retrieval endpoints.

---

## 🔌 5. The integration model the CRM expects

The CRM already integrates with two other telephony providers using a consistent, provider-agnostic pattern. Avaya will plug into the **same shape**, so the requirements below describe *what the CRM needs from Avaya's side* in provider-neutral terms.

### 📤 5.1 Outbound / click-to-dial (G1)

- The CRM, acting for a specific agent (identified by an **Avaya extension / agent ID / DID**), needs to **originate a call** from that agent's device/line to a customer number.
- **Cloud:** an **originate/click-to-dial REST call** the CRM can invoke server-side. **[NEEDS AVAYA CONFIRMATION: endpoint, params, auth]**
- **On-prem:** a **CTI make-call** via the AES interface (through a connector we run). **[NEEDS AVAYA CONFIRMATION]**
- The CRM must be able to correlate the originated call with subsequent status/recording events (a **call ID / UCID / conversation ID**).

### 📥 5.2 Inbound notification → screen-pop (G2)

The CRM needs a **real-time signal** at (or before) the moment a call reaches an agent, carrying at minimum:

- caller number (ANI / from),
- called number (DNIS / to),
- the **target agent** (extension / agent ID / email) so the CRM pops the record on the right person's screen,
- a **unique call identifier** for correlation,
- call direction and initial state.

**Preferred delivery:** an HTTP **webhook/callback to a CRM endpoint** (cloud), and/or CTI events surfaced by an on-prem connector (on-prem). **[NEEDS AVAYA CONFIRMATION: event catalog, payload schema, delivery mechanism, latency]**

### 📇 5.3 Call lifecycle → logging (G3)

For each call the CRM needs lifecycle updates to record and finalize a call log:

- states such as **initiated / ringing / answered (in-progress) / completed / failed / busy / no-answer / cancelled**,
- **start time, answer time, end time, duration**,
- final **disposition/status**,
- the correlating **call ID**.

**[NEEDS AVAYA CONFIRMATION:** the exact status vocabulary and which events fire, so we can map Avaya states → CRM statuses.**]**

### 🎙️ 5.4 Recording retrieval (G4)

- The CRM stores a **reference (URL/ID)** to the recording on the call log — it does **not** need to host the media, but must be able to **retrieve/stream** it on demand for an authorized user.
- We require an **authenticated** retrieval mechanism (the CRM will proxy playback behind its own permissions; recordings are never exposed publicly).
- **[NEEDS AVAYA CONFIRMATION:** how recordings are addressed (per call ID?), the retrieval endpoint/protocol, auth, availability latency after call end, supported formats, and range/streaming support.**]**

### 👤 5.5 Agent ↔ user mapping

- The CRM maps each CRM user to their **Avaya identity** (extension / agent ID / DID / SIP address).
- **[NEEDS AVAYA CONFIRMATION:** the canonical agent identifier we should key on across events and originate calls.**]**

---

## 🔐 6. Security & compliance requirements

- **Authentication:** the CRM will store Avaya credentials/secrets encrypted. We need the supported auth model per mode — **OAuth2 client-credentials, API key, mutual TLS, CTI service login, etc. [NEEDS AVAYA CONFIRMATION].**
- **Inbound webhook verification:** for cloud webhooks, we require a verification mechanism (**signature/HMAC header or shared verify token**) so the CRM can reject forged calls. **[NEEDS AVAYA CONFIRMATION]**
- **Network:** for on-prem, the CTI/recorder endpoints must be reachable from the CRM/connector host; please advise required ports/protocols and whether a connector must sit inside the Avaya network. For cloud, please provide source IP ranges (if webhooks are IP-allowlisted) and any egress requirements.
- **Data residency & privacy:** Tiberbu operates under the **Kenya Data Protection Act (2019)** and healthcare-adjacent confidentiality. We need to confirm **where recordings/media reside**, retention controls, and consent handling. Please advise Avaya's options for data residency and recording retention.
- **PII/PHI:** call metadata will be linked to customer records; recordings may contain health-related conversation. Handling must satisfy the above.

---

## ⚙️ 7. Non-functional expectations (for Avaya to confirm feasibility)

| Concern | Expectation | Avaya confirm? |
|---|---|---|
| Screen-pop latency | Inbound event delivered within ~1–2s of ring | [NEEDS AVAYA CONFIRMATION] |
| Event reliability | At-least-once delivery; retry on webhook failure | [NEEDS AVAYA CONFIRMATION] |
| Recording availability | Retrievable within a defined window after call end | [NEEDS AVAYA CONFIRMATION] |
| Rate limits | Documented API rate limits for originate/retrieval | [NEEDS AVAYA CONFIRMATION] |
| Environments | Sandbox/test tenant or lab CM/AES for integration testing | [NEEDS AVAYA CONFIRMATION] |
| Versioning | API versioning / deprecation policy | [NEEDS AVAYA CONFIRMATION] |

---

## 🤝 8. Responsibility split — Tiberbu CRM side vs. Avaya side

This section states the requirements on **both** sides of the boundary so each team knows what it must deliver and what it can rely on from the other.

### 🛠️ 8.1 Tiberbu CRM (Frappe) side — what we build & expose

The CRM is built on the **Frappe framework (Python/MariaDB)** with a web frontend. Our side of the integration comprises:

**8.1.1 Inbound webhook endpoint (for cloud / and for an on-prem connector to post to)**

- The CRM exposes an **HTTPS webhook URL** that accepts Avaya call events (inbound ring, status changes, recording-ready).
- It is a **public-callable endpoint guarded by a shared verify token** (and/or signature validation — see §6): requests without the correct token are rejected. Avaya (cloud) or the on-prem connector will `POST` JSON call events here.
- We will provide the concrete URL and token at integration time. Shape: `https://<tiberbu-crm-host>/api/method/<avaya-webhook-handler>?token=<verify-token>`.
- **Requirement on Avaya:** deliver events to this endpoint with the fields in §5.2/§5.3; retry on non-2xx (§7).

**8.1.2 Outbound originate trigger**

- When an agent clicks-to-dial, the CRM calls Avaya's **originate** API (cloud REST, or CTI make-call via the on-prem connector), passing the agent's Avaya identity and the destination number.
- The CRM expects back a **call identifier** to correlate later events/recording (§5.1).

**8.1.3 Real-time push to the agent's browser (screen-pop)**

- On receiving an inbound event, the CRM matches the caller number to a customer record and **pushes a real-time notification to the specific agent's browser session** (the CRM has a built-in websocket channel for this), rendering the call popup + matched record.
- **Requirement on Avaya:** the inbound event must identify the **target agent** (extension/agent-ID/email) so we push to the right session (§5.2).

**8.1.4 Call log persistence**

- The CRM writes/updates a **Call Log record** per call, capturing direction, from/to, start/answer/end times, duration, final status, the Avaya **call ID**, and a **recording reference**. It links the call to the matched Lead/Deal/Contact and surfaces it on the customer activity timeline.
- **Requirement on Avaya:** provide the lifecycle states & timestamps in §5.3 and a stable call ID.

**8.1.5 Recording playback proxy**

- The CRM stores only the **recording reference**; on demand it **authenticates to Avaya, retrieves/streams the media, and serves it to authorized CRM users behind CRM permissions** (recordings are never exposed publicly, supporting HTTP range/seek).
- **Requirement on Avaya:** an authenticated retrieval endpoint addressable by call ID, with range/streaming support (§5.4).

**8.1.6 Configuration & mapping**

- An admin **settings screen** holds Avaya connection config for both modes (base URL/region or AES host, credentials/secrets stored encrypted, verify token, recorder access) plus a **mode toggle**.
- A per-user **agent-to-Avaya-identity mapping** (CRM user ↔ extension/agent-ID/DID).

**8.1.7 Workflow automation (CRM-internal)**

- Call events drive CRM workflows (missed-call → callback task + SLA timer; completed-call → journey step) using the CRM's own SLA/assignment/notification engine. **No Avaya dependency beyond the events in §5.3.**

**8.1.8 Frappe-side integration requirements (environmental)**

- **HTTPS reachability:** the CRM webhook (8.1.1) must be reachable by Avaya cloud or the on-prem connector; the CRM host must be able to reach Avaya's originate/recording endpoints (outbound). Firewall/allow-list coordination required (§6).
- **Realtime service:** the CRM's websocket/realtime service must be running for screen-pop (8.1.3).
- **Secrets:** Avaya credentials are stored using the framework's encrypted-field mechanism.
- **Time sync:** CRM and Avaya clocks should be NTP-synced so call timestamps/durations reconcile.

### 📡 8.2 Avaya side — what we ask Avaya to provide

Summarized here; itemized as an action list in §9:

- The **APIs/interfaces** for originate, inbound/lifecycle events, and recording retrieval (per mode).
- **Credentials/access** and the auth + webhook-verification model (§6).
- **Event delivery** to the CRM webhook (cloud) or a supported **connector/SDK** to run on-prem, with the fields in §5.
- **Recording access** (authenticated, addressable, streamable).
- A **test environment** (sandbox tenant or lab CM/AES + recorder) and the non-functional confirmations in §7.

### 🔗 8.3 Interface contract at a glance — **mechanism per interaction**

Each row states the **transport mechanism** so both teams know exactly what to build. "Owner of endpoint" = who hosts the URL the other side calls.

| # | Interaction | Mechanism | Direction | Endpoint owner | Trigger |
|---|---|---|---|---|---|
| I1 | Click-to-dial (originate) | **Outbound HTTPS REST call** (cloud) / **CTI make-call** via connector (on-prem) | CRM → Avaya | **Avaya** | Agent clicks a number in the CRM |
| I2 | Inbound call + lifecycle events | **Webhook** — Avaya `POST`s JSON to a CRM HTTPS URL (cloud) / on-prem connector `POST`s to the same CRM URL | Avaya → CRM | **CRM** | Call rings / changes state / recording ready |
| I3 | Screen-pop to agent | **WebSocket** (CRM's realtime channel) — server pushes to the agent's browser | CRM server → agent browser | **CRM** | CRM receives an I2 inbound event |
| I4 | Call logging | **Internal** DB write (no network) | internal to CRM | **CRM** | Every I2 event |
| I5 | Recording retrieval / playback | **Outbound authenticated HTTPS GET** (range/stream), proxied to the CRM user | CRM → Avaya → CRM user | **Avaya** (media) | Authorized user plays a recording in the CRM |

**Plain-language summary for each engineer:**

- **Avaya engineer builds/*exposes*:** the **REST originate API** (I1), the ability to **POST webhooks** to our URL (I2), and an **authenticated media-retrieval endpoint** (I5). (On-prem: expose CTI via AES so our connector can subscribe to events and issue make-call.)
- **Frappe/CRM engineer builds/*exposes*:** the **inbound webhook endpoint** that receives I2, the **realtime push** for I3, the **call-log persistence** for I4, and the **outbound calls** to Avaya for I1 and I5 (plus the recording proxy). On-prem only: a **connector process** that bridges AES CTI ↔ the same webhook.

---

### 🧪 8.4 API examples (illustrative)

> **Read this first — two different confidence levels:**
> - **CRM/Frappe-side shapes (I2 receiver, I3 realtime, I5 proxy)** follow the CRM's existing, proven telephony-provider pattern and are **concrete** — the Frappe engineer can build to them now.
> - **Avaya-side shapes (I1 originate, I2 payload, I5 media)** are **ILLUSTRATIVE PLACEHOLDERS** showing the *kind* of request/response we expect. **They are NOT Avaya's real API** — the actual endpoints, fields, and auth are what we ask Avaya to confirm in §9. Do not implement against these verbatim.

#### 📞 I1 — Click-to-dial (CRM → Avaya), Cloud/AXP — *illustrative, Avaya to confirm*

```http
POST https://api.avaya.example/experience/v1/calls          # [NEEDS AVAYA CONFIRMATION: real base URL/path]
Authorization: Bearer <access_token>                        # [NEEDS AVAYA CONFIRMATION: auth model]
Content-Type: application/json

{
  "agent": "1042",                 // agent extension / agent ID  [§5.5]
  "to": "+254712345678",           // customer number
  "callerId": "+254203900000",     // outbound presentation number
  "record": true
}
```

```jsonc
// Expected response — we need a correlating call identifier back:
HTTP/1.1 201 Created
{
  "callId": "AXP-8f3c2a…",         // <-- CRM stores this to correlate events + recording  [§5.1]
  "status": "initiated"
}
```

*On-prem equivalent:* our connector issues a **CTI make-call** (e.g. TSAPI/DMCC `makeCall(agentDevice, destination)`) and receives a **UCID/call-ID** — **[NEEDS AVAYA CONFIRMATION: interface + call-ID field].**

#### 🔔 I2 — Inbound / lifecycle webhook (Avaya → CRM)

**CRM receiver (concrete — Frappe side).** The CRM exposes a token-guarded, guest-callable endpoint (same pattern as the CRM's existing providers):

```http
POST https://<tiberbu-crm-host>/api/method/crm.integrations.avaya.handler.handle_request?token=<verify-token>
Content-Type: application/json
```

**Avaya-sent body — *illustrative, Avaya to confirm the real schema (§5.2/§5.3)*:**

```jsonc
{
  "event": "call.ringing",          // [NEEDS AVAYA CONFIRMATION: event vocabulary]
  "callId": "AXP-8f3c2a…",          // correlation id
  "direction": "inbound",
  "from": "+254712345678",          // ANI (caller)
  "to": "+254203900000",            // DNIS (called)
  "agent": "1042",                  // target agent → CRM screen-pops this user  [§5.2]
  "timestamp": "2026-07-29T09:15:03Z",
  "status": "ringing"               // ringing|answered|completed|missed|failed|busy|no-answer
}
```

**How the CRM responds:** validate the token → `200 OK` immediately; then match `from` → customer record, push screen-pop (I3), and upsert the call log (I4). A later `"event": "recording.available"` webhook carries the recording reference for I5. **Requirement on Avaya:** retry on non-2xx (§7).

*On-prem:* the connector receives the equivalent as **CTI events** (e.g. TSAPI *Delivered/Established/Connection Cleared*) and translates them into the **same** JSON `POST` to the CRM URL above — so the CRM handler is identical for both modes.

#### 🪟 I3 — Screen-pop (CRM server → agent browser), WebSocket — *concrete, Frappe side*

```js
// CRM server, on receiving I2 inbound event → push to the matched agent's session:
frappe.publish_realtime(
  "avaya_call",                       // event name the browser subscribes to
  { call_id, from, to, status, contact },   // matched customer record included
  user=agent_user_email               // targeted to the specific agent
)
// CRM browser (Vue) listens:  socket.on('avaya_call', (data) => showCallPopup(data))
```

#### ▶️ I5 — Recording retrieval (CRM → Avaya → user), authenticated stream

**CRM user-facing (concrete — Frappe side).** The browser `<audio>` points at a CRM proxy URL, never at Avaya directly:

```
GET https://<tiberbu-crm-host>/api/method/crm.integrations.api.get_recording_url?call_log_name=<name>
    → CRM authenticates the user, then server-side fetches from Avaya and streams back (supports Range)
```

**CRM → Avaya fetch — *illustrative, Avaya to confirm (§5.4)*:**

```http
GET https://media.avaya.example/recordings/AXP-8f3c2a…    # [NEEDS AVAYA CONFIRMATION: addressing + endpoint]
Authorization: Bearer <access_token>                       # [NEEDS AVAYA CONFIRMATION: auth]
Range: bytes=0-                                            # streaming/seek support required
```

---

## 📋 9. Information & access requested from Avaya Engineering (action list)

Please provide, per applicable mode:

**A. Products & interfaces**

1. Confirm the correct Avaya product(s) for our on-prem (Aura/AES) and cloud (AXP) integrations, and the **recommended API/CTI interface** for each.
2. API reference documentation (REST specs / CTI SDK docs) and versions.

**B. Authentication & security**

3. Auth model and credential type for each interface (OAuth2 / API key / mTLS / CTI login).
4. Webhook signature/verification mechanism (cloud).
5. Network requirements: ports/protocols (on-prem), source IP ranges / allow-listing (cloud), connector placement guidance.

**C. Call control & events** *(please return your real request/response and webhook payload schemas against the illustrative examples in §8.4 — i.e. correct I1, I2, I5 to Avaya's actual API)*

6. **Click-to-dial / originate** (I1) endpoint(s), method, parameters, auth, and the returned **call identifier** — confirm/replace the §8.4 I1 example.
7. **Inbound & lifecycle event** catalog (I2): event types/vocabulary, **actual JSON payload schema(s)**, delivery mechanism (webhook `POST` / CTI), retry behavior, and the fields in §5.2/§5.3 (ANI, DNIS, agent, call ID, state, timestamps) — confirm/replace the §8.4 I2 example.
8. The canonical **agent identifier** to key on (extension / agent ID / DID / SIP address).

**D. Recording**

9. How recordings are **addressed and retrieved** (I5): endpoint/protocol/auth, availability latency after call end, formats, and streaming/range support — confirm/replace the §8.4 I5 example.
10. **Data residency & retention** options relevant to Kenya DPA 2019.

**E. Enablement**

11. A **sandbox/test tenant** (cloud) or **lab CM/AES + recorder** (on-prem) for integration and certification testing.
12. Rate limits, SLAs, versioning/deprecation policy, and a technical point of contact for the integration.

---

## 🗺️ 10. Proposed next steps

1. **Discovery workshop** between Tiberbu CRM Engineering and Avaya Engineering to walk through §5 and answer §9.
2. Avaya returns the §9 action list (docs, access, test environment).
3. Tiberbu finalizes the connector design per confirmed contracts and builds against the sandbox.
4. Joint **certification test**: click-to-dial, inbound screen-pop, full call logging, and recording retrieval — for the mode(s) in scope.

---

*Prepared for discovery. All items marked **[NEEDS AVAYA CONFIRMATION]** reflect Tiberbu's current understanding of Avaya capabilities and are stated as questions, not assumptions — please correct anything inaccurate. Contact: Tiberbu CRM Engineering.*
