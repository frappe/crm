{#- The public booking page's script: picking a time, the form, and rescheduling
or cancelling. Rendered with the page, so its Jinja (strings, PAGE) still applies. -#}
      (function () {
        const PAGE = {{ page_data | tojson }};
        var FIELDS = {{ fields | tojson }};
        var BREAKS = { "Section Break": 1, "Column Break": 1 };
{% include "crm/templates/includes/crm_form_logic.js" %}
        const CSRF = {{ (csrf_token or "") | tojson }};
        const T = {
          minutes: {{ _("{0} minutes") | tojson }},
          noSlots: {{ _("No open times this month. Try the next one.") | tojson }},
          pickDay: {{ _("Pick a day") | tojson }},
          loading: {{ _("Loading…") | tojson }},
          titles: {
            booked: {{ _("You're booked") | tojson }},
            moved: {{ _("Your meeting has moved") | tojson }},
            upcoming: {{ _("Your meeting is booked") | tojson }},
            cancelled: {{ _("Meeting cancelled") | tojson }},
            past: {{ _("This meeting has passed") | tojson }},
          },
          notes: {
            booked: {{ _("We've sent the details to {0}.") | tojson }},
            moved: {{ _("We've sent the new time to {0}.") | tojson }},
            upcoming: {{ _("Need a different time? Reschedule or cancel below.") | tojson }},
            cancelled: {{ _("{1} has been told, and there's nothing else you need to do.") | tojson }},
          },
          pickTime: {{ _("Pick a time") | tojson }},
          withHost: {{ _("With {0}") | tojson }},
          bookAgain: {{ _("Book another time") | tojson }},
          pickNewTime: {{ _("Pick a new time") | tojson }},
          locations: {
            "Google Meet": {{ _("Google Meet") | tojson }},
            "Phone call": {{ _("Phone call") | tojson }},
            "In person": {{ _("In person") | tojson }},
            "Custom link": {{ _("Online") | tojson }},
          },
          generic: {{ _("Something went wrong. Please try again.") | tojson }},
          badPhone: {{ _("{0} isn't a valid phone number") | tojson }},
          missingOne: {{ _("Please fill in the required field: {0}") | tojson }},
          missingMany: {{ _("Please fill in all required fields.") | tojson }},
        };
        const $ = (id) => document.getElementById(id);
        const params = new URLSearchParams(location.search);

        const state = {
          tz: guessTimezone(),
          year: 0,
          month: 0, // 0-based
          slotsByDay: {}, // "YYYY-MM-DD" in state.tz -> [Date]
          day: null,
          slot: null, // Date
          booking: null, // from the API when managing one
          rescheduling: false,
          loadId: 0,
        };

        // About panel

        function renderAbout() {
          $("page-title").textContent = PAGE.title;
          $("page-duration").textContent = T.minutes.replace("{0}", PAGE.duration);
          $("page-location").textContent =
            PAGE.location_type === "In person" && PAGE.location ? PAGE.location : T.locations[PAGE.location_type] || PAGE.location_type;
          $("page-description").textContent = PAGE.description;
          const avatars = $("host-avatars");
          PAGE.hosts.slice(0, 4).forEach((h) => {
            const el = document.createElement("div");
            el.className = "avatar";
            if (h.image) {
              const img = document.createElement("img");
              img.src = h.image;
              img.alt = "";
              el.appendChild(img);
            } else {
              el.textContent = (h.full_name || "?").charAt(0).toUpperCase();
            }
            avatars.appendChild(el);
          });
          $("host-names").textContent = PAGE.hosts.length === 1 ? PAGE.hosts[0].full_name : "";
        }

        // Time helpers. All dates are real instants; "day keys" are calendar dates in state.tz.

        function guessTimezone() {
          try {
            return Intl.DateTimeFormat().resolvedOptions().timeZone || PAGE.timezone;
          } catch (e) {
            return PAGE.timezone;
          }
        }

        function dayKey(date) {
          const p = new Intl.DateTimeFormat("en-CA", { timeZone: state.tz, year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
          return p; // en-CA formats as YYYY-MM-DD
        }

        function formatTime(date) {
          return new Intl.DateTimeFormat(undefined, { timeZone: state.tz, hour: "numeric", minute: "2-digit" }).format(date);
        }

        function formatDay(date, opts) {
          return new Intl.DateTimeFormat(undefined, Object.assign({ timeZone: state.tz, weekday: "long", day: "numeric", month: "long" }, opts || {})).format(date);
        }

        function formatRange(start, end) {
          return `${formatDay(start)}, ${formatTime(start)} – ${formatTime(end)}`;
        }

        function keyToLabel(key) {
          const [y, m, d] = key.split("-").map(Number);
          // noon UTC lands on the same calendar date in every timezone
          return formatDay(new Date(Date.UTC(y, m - 1, d, 12)), { timeZone: "UTC" });
        }

        // API

        async function api(method, args, post) {
          let url = `/api/method/crm.api.booking.${method}`;
          const init = { headers: { Accept: "application/json" } };
          if (post) {
            init.method = "POST";
            init.headers["Content-Type"] = "application/json";
            init.headers["X-Frappe-CSRF-Token"] = CSRF;
            init.body = JSON.stringify(args);
          } else {
            url += "?" + new URLSearchParams(args).toString();
          }
          const res = await fetch(url, init);
          const data = await res.json().catch(() => ({}));
          if (!res.ok) {
            const err = new Error(serverMessage(data) || T.generic);
            err.status = res.status;
            throw err;
          }
          return data.message;
        }

        function serverMessage(data) {
          try {
            const msgs = JSON.parse(data._server_messages || "[]").map((m) => JSON.parse(m).message);
            const div = document.createElement("div");
            div.innerHTML = msgs.join(" ");
            return div.textContent;
          } catch (e) {
            return "";
          }
        }

        function showError(message) {
          const el = $("error");
          el.textContent = message || "";
          el.style.display = message ? "block" : "none";
        }

        // Steps

        function show(step) {
          ["pick", "details", "move", "cancel", "done"].forEach((s) => ($("step-" + s).hidden = s !== step));
          $("card").classList.toggle("narrow", step === "done" || step === "cancel" || step === "move");
          showError("");
        }

        // Month calendar

        function renderWeekdays() {
          const fmt = new Intl.DateTimeFormat(undefined, { weekday: "short", timeZone: "UTC" });
          // 2023-01-01 was a Sunday
          $("weekdays").innerHTML = "";
          for (let i = 0; i < 7; i++) {
            const el = document.createElement("div");
            el.textContent = fmt.format(new Date(Date.UTC(2023, 0, 1 + i, 12)));
            $("weekdays").appendChild(el);
          }
        }

        function setMonthFromToday() {
          const [y, m] = dayKey(new Date()).split("-").map(Number);
          state.year = y;
          state.month = m - 1;
        }

        function monthBounds() {
          const last = new Date(Date.UTC(state.year, state.month + 1, 0)).getUTCDate();
          return { last };
        }

        function canGoBack() {
          const [y, m] = dayKey(new Date()).split("-").map(Number);
          return state.year > y || (state.year === y && state.month > m - 1);
        }

        function canGoForward() {
          const limit = new Date(Date.now() + PAGE.max_days_ahead * 86400000);
          const [y, m] = dayKey(limit).split("-").map(Number);
          return state.year < y || (state.year === y && state.month < m - 1);
        }

        async function loadMonth() {
          const loadId = ++state.loadId;
          state.slotsByDay = {};
          state.day = null;
          renderMonth();
          $("slots-head").textContent = T.loading;
          $("slots").innerHTML = "";
          // a day either side covers every timezone's view of the month
          const start = new Date(Date.UTC(state.year, state.month, 1) - 86400000);
          const end = new Date(Date.UTC(state.year, state.month + 1, 1) + 86400000);
          const args = { route: PAGE.route, start: start.toISOString(), end: end.toISOString() };
          if (state.rescheduling) args.token = state.booking.token;
          try {
            const slots = await api("get_slots", args);
            if (loadId !== state.loadId) return;
            const monthPrefix = `${state.year}-${String(state.month + 1).padStart(2, "0")}-`;
            slots.forEach((iso) => {
              const date = new Date(iso);
              const key = dayKey(date);
              if (!key.startsWith(monthPrefix)) return;
              (state.slotsByDay[key] = state.slotsByDay[key] || []).push(date);
            });
            const first = Object.keys(state.slotsByDay).sort()[0];
            state.day = first || null;
            renderMonth();
            renderSlots();
          } catch (e) {
            if (loadId !== state.loadId) return;
            showError(e.message);
            $("slots-head").textContent = "";
          }
        }

        function renderMonth() {
          $("month-label").textContent = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric", timeZone: "UTC" }).format(
            new Date(Date.UTC(state.year, state.month, 15))
          );
          $("prev-month").disabled = !canGoBack();
          $("next-month").disabled = !canGoForward();
          const days = $("days");
          days.innerHTML = "";
          const lead = new Date(Date.UTC(state.year, state.month, 1)).getUTCDay();
          for (let i = 0; i < lead; i++) days.appendChild(document.createElement("div"));
          const today = dayKey(new Date());
          for (let d = 1; d <= monthBounds().last; d++) {
            const key = `${state.year}-${String(state.month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
            const btn = document.createElement("button");
            btn.className = "day";
            btn.textContent = d;
            const open = !!state.slotsByDay[key];
            if (open) btn.classList.add("open");
            if (key === state.day) btn.classList.add("selected");
            if (key === today) btn.classList.add("today");
            btn.disabled = !open;
            btn.addEventListener("click", () => {
              state.day = key;
              renderMonth();
              renderSlots();
            });
            days.appendChild(btn);
          }
        }

        function renderSlots() {
          const list = $("slots");
          list.innerHTML = "";
          if (!Object.keys(state.slotsByDay).length) {
            $("slots-head").textContent = "";
            const el = document.createElement("div");
            el.className = "empty";
            el.textContent = T.noSlots;
            list.appendChild(el);
            return;
          }
          if (!state.day) {
            $("slots-head").textContent = T.pickDay;
            return;
          }
          $("slots-head").textContent = keyToLabel(state.day);
          state.slotsByDay[state.day].forEach((date) => {
            const btn = document.createElement("button");
            btn.className = "slot";
            btn.textContent = formatTime(date);
            btn.addEventListener("click", () => pickSlot(date));
            list.appendChild(btn);
          });
        }

        function slotEnd(date) {
          return new Date(date.getTime() + PAGE.duration * 60000);
        }

        function pickSlot(date) {
          state.slot = date;
          if (state.rescheduling) {
            $("move-from").textContent = formatRange(new Date(state.booking.start), new Date(state.booking.end));
            $("move-to").textContent = formatRange(date, slotEnd(date));
            show("move");
            return;
          }
          $("chosen-time").textContent = formatRange(date, slotEnd(date));
          show("details");
          // the form's first input
          const firstInput = $("details-form").querySelector("input, select, textarea");
          if (firstInput) firstInput.focus();
        }

        // Timezone select

        function renderTimezones() {
          const select = $("bk-timezone");
          let zones = [];
          try {
            zones = Intl.supportedValuesOf("timeZone");
          } catch (e) {
            zones = [];
          }
          [state.tz, PAGE.timezone].forEach((z) => z && !zones.includes(z) && zones.unshift(z));
          zones.forEach((z) => {
            const opt = document.createElement("option");
            opt.value = z;
            opt.textContent = z.replace(/_/g, " ");
            select.appendChild(opt);
          });
          select.value = state.tz;
          select.addEventListener("change", () => {
            state.tz = select.value;
            loadMonth();
          });
        }

        const PHONE_RE = /^[0-9 +_\-,.*#()]{1,20}$/;
        function isPhone(f) {
          return f.fieldtype === "Phone" || f.options === "Phone";
        }

        // the form's visible fields, checked the way crm_form.html checks them
        function collectFormValues() {
          const doc = collectDoc();
          const values = {};
          const missing = [];
          const invalid = [];
          FIELDS.forEach((f) => {
            if (BREAKS[f.fieldtype]) return;
            const el = document.getElementById(f.fieldname);
            if (!el) return;
            el.classList.remove("has-error");
            if (!isVisible(f, doc)) return;
            const val = f.fieldtype === "Check" ? (el.checked ? 1 : 0) : el.value;
            values[f.fieldname] = val;
            const empty = f.fieldtype === "Check" ? val === 0 : val === "" || val == null;
            if (isRequired(f, doc) && !isReadOnly(f, doc) && empty) {
              missing.push({ el, label: f.label || f.fieldname });
              el.classList.add("has-error");
            } else if (!empty && isPhone(f) && !PHONE_RE.test(String(val).trim())) {
              // same pattern as frappe.utils.validate_phone_number, checked before sending
              invalid.push({ el, message: T.badPhone.replace("{0}", f.label || f.fieldname) });
              el.classList.add("has-error");
            }
          });
          return { values, missing, invalid };
        }

        async function submitDetails(e) {
          e.preventDefault();
          showError("");
          const { values, missing, invalid } = collectFormValues();
          // same wording as crm_form.html
          let first = null;
          if (missing.length) {
            first = missing[0].el;
            showError(
              missing.length === 1
                ? T.missingOne.replace("{0}", missing[0].label)
                : T.missingMany
            );
          } else if (invalid.length) {
            first = invalid[0].el;
            showError(invalid[0].message);
          }
          const email = document.getElementById("email");
          if (!first && email && !/^\S+@\S+\.\S+$/.test(email.value.trim())) {
            email.classList.add("has-error");
            first = email;
          }
          if (first) {
            first.focus();
            return;
          }
          const btn = $("confirm-btn");
          btn.disabled = true;
          try {
            const booking = await api(
              "book",
              {
                route: PAGE.route,
                start: state.slot.toISOString(),
                values: values,
                timezone: state.tz,
              },
              true
            );
            showBooking(booking, "booked");
          } catch (err) {
            if (err.status === 409) {
              // the slot went; go back and pick again with fresh times
              show("pick");
              showError(err.message);
              loadMonth();
            } else {
              showError(err.message);
            }
          } finally {
            btn.disabled = false;
          }
        }

        // Managing a booking

        function iconRow(icon, text, sub, struck) {
          const row = document.createElement("div");
          row.className = "row" + (struck ? " struck" : "");
          row.innerHTML = $("icon-" + icon).innerHTML;
          const body = document.createElement("div");
          const main = document.createElement("span");
          if (text instanceof Node) main.appendChild(text);
          else main.textContent = text;
          body.appendChild(main);
          if (sub) {
            const subEl = document.createElement("span");
            subEl.className = "sub";
            subEl.textContent = sub;
            body.appendChild(subEl);
          }
          row.appendChild(body);
          return row;
        }

        // `how` is what just happened here; without it the booking was opened from an email
        function showBooking(booking, how) {
          state.booking = booking;
          state.rescheduling = false;
          const start = new Date(booking.start);
          const end = new Date(booking.end);
          const cancelled = booking.status === "Cancelled";
          const kind = cancelled ? "cancelled" : how === "booked" ? "booked" : how === "moved" ? "moved" : booking.upcoming ? "upcoming" : "past";

          const icon = $("done-icon");
          icon.innerHTML = $("icon-" + kind).innerHTML;
          icon.className = "state-icon" + ({ booked: " success", moved: " success", upcoming: " success", cancelled: " danger" }[kind] || "");
          $("done-title").textContent = T.titles[kind];
          $("done-note").textContent = (T.notes[kind] || "")
            .replace("{0}", booking.guest_email)
            .replace("{1}", booking.host);

          // shown with a booking that stands, not once it's cancelled or over
          const message = $("done-message");
          message.textContent = PAGE.confirmation_message || "";
          message.hidden = !PAGE.confirmation_message || !["booked", "moved", "upcoming"].includes(kind);

          const details = $("done-details");
          details.innerHTML = "";
          const title = document.createElement("div");
          title.className = "details-title";
          title.textContent = booking.page.title;
          details.appendChild(title);
          details.appendChild(
            iconRow("time", `${formatDay(start)}, ${formatTime(start)} – ${formatTime(end)}`, state.tz.replace(/_/g, " "), cancelled)
          );
          details.appendChild(iconRow("person", T.withHost.replace("{0}", booking.host)));
          if (booking.meeting_link && !cancelled) {
            const a = document.createElement("a");
            a.href = booking.meeting_link;
            a.target = "_blank";
            a.rel = "noopener";
            a.textContent = booking.meeting_link.replace(/^https?:\/\//, "");
            details.appendChild(iconRow("video", a));
          }

          $("done-manage").hidden = kind === "cancelled" || kind === "past";
          $("done-again").hidden = !$("done-manage").hidden;
          if (how === "booked") {
            const params = new URLSearchParams(location.search);
            params.set("booking", booking.token);
            history.replaceState(null, "", `${location.pathname}?${params}`);
          }
          show("done");
        }

        function bookAgain() {
          state.booking = null;
          state.rescheduling = false;
          const params = new URLSearchParams(location.search);
          params.delete("booking");
          const query = params.toString();
          history.replaceState(null, "", location.pathname + (query ? `?${query}` : ""));
          $("pick-title").textContent = T.pickTime;
          show("pick");
          setMonthFromToday();
          loadMonth();
        }

        async function moveBooking() {
          const btn = $("move-confirm");
          btn.disabled = true;
          try {
            const booking = await api("reschedule_booking", { token: state.booking.token, start: state.slot.toISOString() }, true);
            showBooking(booking, "moved");
          } catch (err) {
            showError(err.message);
          } finally {
            btn.disabled = false;
          }
        }

        async function cancelBooking() {
          const btn = $("cancel-confirm");
          btn.disabled = true;
          try {
            const booking = await api("cancel_booking", { token: state.booking.token, reason: $("cancel-reason").value }, true);
            showBooking(booking, "cancelled");
          } catch (err) {
            showError(err.message);
          } finally {
            btn.disabled = false;
          }
        }

        // Wiring

        $("prev-month").addEventListener("click", () => {
          if (state.month === 0) {
            state.year -= 1;
            state.month = 11;
          } else state.month -= 1;
          loadMonth();
        });
        $("next-month").addEventListener("click", () => {
          if (state.month === 11) {
            state.year += 1;
            state.month = 0;
          } else state.month += 1;
          loadMonth();
        });
        $("change-time").addEventListener("click", () => show("pick"));
        $("details-form").addEventListener("submit", submitDetails);
        $("reschedule-btn").addEventListener("click", () => {
          state.rescheduling = true;
          $("pick-title").textContent = T.pickNewTime;
          show("pick");
          setMonthFromToday();
          loadMonth();
        });
        $("cancel-btn").addEventListener("click", () => {
          $("cancel-time").textContent = formatRange(new Date(state.booking.start), new Date(state.booking.end));
          show("cancel");
        });
        $("move-back").addEventListener("click", () => show("pick"));
        $("move-confirm").addEventListener("click", moveBooking);
        $("cancel-back").addEventListener("click", () => showBooking(state.booking));
        $("cancel-confirm").addEventListener("click", cancelBooking);
        $("book-again-btn").addEventListener("click", bookAgain);

        renderAbout();
        renderWeekdays();
        renderTimezones();
        // re-apply the form's conditions as people type, and clear a field's error once it's filled
        ["input", "change"].forEach((type) =>
          $("details-form").addEventListener(type, (e) => {
            e.target.classList.remove("has-error");
            refreshDeps();
          })
        );
        refreshDeps();
        setMonthFromToday();

        // embedded: tell the host page how tall the card is, so the embed
        // snippet can size the iframe to fit instead of scrolling inside it
        if (document.body.classList.contains("embed") && window.parent !== window) {
          const card = $("card");
          const report = () =>
            window.parent.postMessage(
              { type: "crm-book:height", route: PAGE.route, height: Math.ceil(card.getBoundingClientRect().height) },
              "*"
            );
          new ResizeObserver(report).observe(card);
        }

        const token = params.get("booking");
        if (token) {
          api("get_booking", { token })
            .then((booking) => showBooking(booking))
            .catch((err) => {
              show("pick");
              showError(err.message);
              loadMonth();
            });
        } else {
          loadMonth();
        }
      })();
